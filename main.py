import os
import logging
import asyncio
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

# Токен бота берётся из переменной окружения BOT_TOKEN
API_TOKEN = '7775481098:AAGm_yzn3r9J9p2mYQWZIfqj52o84WtOvdI'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера с хранением состояний в памяти
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация базы данных SQLite (файл users.db)
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        place TEXT
    )
""")
conn.commit()

# Список доступных городов (можно расширять по необходимости)
available_cities = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Нижний Новгород",
    "Казань",
    "Челябинск",
    "Омск",
    "Самара",
    "Ростов-на-Дону"
]

# Словарь для сопоставления кодов погоды Open-Meteo с описаниями
weather_codes = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Местами облачно",
    3: "Пасмурно",
    45: "Туман",
    48: "Иней",
    51: "Лёгкая морось",
    53: "Умеренная морось",
    55: "Сильная морось",
    56: "Лёгкий ледяной дождь",
    57: "Сильный ледяной дождь",
    61: "Небольшой дождь",
    63: "Умеренный дождь",
    65: "Сильный дождь",
    66: "Лёгкий ледяной дождь",
    67: "Сильный ледяной дождь",
    71: "Небольшой снегопад",
    73: "Умеренный снегопад",
    75: "Сильный снегопад",
    77: "Снежные зерна",
    80: "Небольшой дождь",
    81: "Умеренный дождь",
    82: "Сильный дождь",
    85: "Лёгкий снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с небольшим градом",
    99: "Гроза с сильным градом",
}


# Асинхронная функция для получения погоды через Open-Meteo API с отключённой проверкой сертификата
async def get_weather(place: str) -> str:
    async with aiohttp.ClientSession() as session:
        # Получаем координаты города через геокодинг API Open-Meteo
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={place}&count=1&language=ru&format=json"
        async with session.get(geocode_url, ssl=False) as geo_response:
            if geo_response.status != 200:
                return f"Ошибка при получении данных геокодирования для {place}."
            geo_data = await geo_response.json()
            if "results" not in geo_data or not geo_data["results"]:
                return f"Город {place} не найден."
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location.get("name", place)

        # Получаем текущую погоду по координатам
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true&timezone=Europe/Moscow"
        )
        async with session.get(weather_url, ssl=False) as weather_response:
            if weather_response.status != 200:
                return f"Ошибка при получении погоды для {city_name}."
            weather_data = await weather_response.json()
            current_weather = weather_data.get("current_weather")
            if not current_weather:
                return f"Нет данных о текущей погоде для {city_name}."
            temperature = current_weather.get("temperature")
            windspeed = current_weather.get("windspeed")
            weathercode = current_weather.get("weathercode")
            description = weather_codes.get(weathercode, f"Код погоды: {weathercode}")
            return (
                f"Погода в {city_name}:\n"
                f"Температура: {temperature}°C\n"
                f"Скорость ветра: {windspeed} км/ч\n"
                f"Состояние: {description}"
            )


# Класс состояний для изменения местности через FSM
class PlaceState(StatesGroup):
    waiting_for_new_place = State()


# Обработчик команды /start для регистрации пользователя
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result is None:
        # По умолчанию регистрируем с городом "Москва"
        cursor.execute("INSERT INTO users (id, place) VALUES (?, ?)", (user_id, "Москва"))
        conn.commit()
        await message.reply("Вы зарегистрированы! Местность установлена по умолчанию: Москва")
    else:
        await message.reply("Вы уже зарегистрированы.")


# Обработчик команды /place для обновления местности с выводом списка доступных городов
@dp.message_handler(commands=["place"])
async def place_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()  # Получаем аргументы после команды
    if args:
        new_place = args.strip()
        # Проверяем, входит ли введённый город в список доступных (без учёта регистра)
        if new_place.lower() not in [city.lower() for city in available_cities]:
            await message.reply(
                "Извините, данный город не доступен. Пожалуйста, выберите город из списка:\n" +
                "\n".join(available_cities)
            )
            return
        cursor.execute("UPDATE users SET place = ? WHERE id = ?", (new_place, user_id))
        conn.commit()
        await message.reply(f"Ваша местность обновлена на: {new_place}")
    else:
        # Если аргумент не передан, выводим список доступных городов
        cities_list = "\n".join(available_cities)
        await message.reply("Пожалуйста, выберите город из списка:\n" + cities_list)
        await PlaceState.waiting_for_new_place.set()


# Обработчик для ввода новой местности, когда бот ждёт выбор пользователя
@dp.message_handler(state=PlaceState.waiting_for_new_place)
async def process_new_place(message: types.Message, state: FSMContext):
    new_place = message.text.strip()
    if new_place.lower() not in [city.lower() for city in available_cities]:
        await message.reply(
            "Извините, данный город не доступен. Пожалуйста, выберите город из списка:\n" +
            "\n".join(available_cities)
        )
        return
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET place = ? WHERE id = ?", (new_place, user_id))
    conn.commit()
    await message.reply(f"Ваша местность обновлена на: {new_place}")
    await state.finish()


# Функция для вычисления времени до следующего 9:00 по Москве
def seconds_until_target():
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


# Фоновая задача для рассылки погоды каждому пользователю каждый день в 9:00 по Москве
async def broadcast_weather():
    while True:
        # Вычисляем, сколько секунд осталось до следующего 9:00 по Москве
        wait_seconds = seconds_until_target()
        logging.info(f"Ожидание {wait_seconds} секунд до следующего запуска рассылки в 9:00 по Москве.")
        await asyncio.sleep(wait_seconds)
        # Получаем список пользователей из базы
        cursor.execute("SELECT id, place FROM users")
        users = cursor.fetchall()
        for user_id, place in users:
            weather_info = await get_weather(place)
            try:
                await bot.send_message(user_id, weather_info)
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


# Функция, запускаемая при старте бота, для инициации фоновой задачи
async def on_startup(dp):
    asyncio.create_task(broadcast_weather())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)