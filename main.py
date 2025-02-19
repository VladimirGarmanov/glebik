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
import re

# Исходный список городов с возможными цифровыми суффиксами

assistant_cities = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Нижний Новгород",
    "Казань",
    "Челябинск",
    "Омск",
    "Самара",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Пермь",
    "Волгоград",
    "Воронеж",
    "Саратов",
    "Краснодар",
    "Тольятти",
    "Ижевск",
    "Барнаул",
    "Ульяновск",
    "Иркутск",
    "Владивосток",
    "Ярославль",
    "Хабаровск",
    "Махачкала",
    "Оренбург",
    "Новокузнецк",
    "Кемерово",
    "Рязань",
    "Астрахань",
    "Набережные Челны",
    "Пенза",
    "Липецк",
    "Киров",
    "Чебоксары",
    "Брянск",
    "Тверь",
    "Магнитогорск",
    "Улан-Удэ",
    "Ставрополь",
    "Смоленск",
    "Владимир",
    "Архангельск",
    "Севастополь",
    "Саранск",
    "Волжский",
    "Тюмень",
    "Нижневартовск",
    "Йошкар-Ола",
    "Элиста",
    "Курск",
    "Благовещенск",
    "Орёл",
    "Мурманск",
    "Новороссийск",
    "Нальчик",
    "Подольск",
    "Калининград",
    "Сургут",
    "Братск",
    "Щёлково",
    "Батайск",
    "Мытищи",
    "Орехово-Зуево",
    "Коломна",
    "Люберцы",
    "Прокопьевск",
    "Пятигорск",
    "Стерлитамак",
    "Северодвинск",
    "Новочеркасск",
    "Дзержинск",
    "Рыбинск",
    "Энгельс",
    "Златоуст",
    "Обнинск",
    "Электросталь",
    "Королёв",
    "Серпухов",
    "Нефтекамск",
    "Вологда",
    "Псков",
    "Ангарск",
    "Кропоткин",
    "Новомосковск",
    "Бузулук",
    "Абакан",
    "Кирово-Чепецк",
    "Норильск",
    "Химки",
    "Одинцово",
    "Зеленоград",
    "Домодедово",
    "Реутов",
    "Лыткарино",
    "Пушкино",
    "Арзамас",
    "Армавир",
    "Асбест",
    "Ачинск",
    "Балаково",
    "Балашиха",
    "Балашов",
    "Белгород",
    "Белорецк",
    "Белоярский",
    "Березники",
    "Березовский",
    "Бийск",
    "Будённовск",
    "Бугуруслан",
    "Буйнакск",
    "Владикавказ",
    "Волгодонск",
    "Вольск",
    "Выборг",
    "Геленджик",
    "Глазов",
    "Горно-Алтайск",
    "Горячий Ключ",
    "Грозный",
    "Дмитров",
    "Долгопрудный",
    "Дубна",
    "Ессентуки",
    "Елабуга",
    "Ефремов",
    "Железногорск",
    "Железногорск-Илимский",
    "Жуковский",
    "Иваново",
    "Калуга",
    "Каменск-Уральский",
    "Каменск-Шахтинский",
    "Керчь",
    "Кизел",
    "Кизляр",
    "Кинешма",
    "Кисловодск",
    "Клин",
    "Ковров",
    "Комсомольск-на-Амуре",
    "Копейск",
    "Кострома",
    "Котлас",
    "Котельники",
    "Красногорск",
    "Краснокаменск",
    "Краснознаменск",
    "Краснотурьинск",
    "Крымск",
    "Кстово",
    "Кубинка",
    "Курган",
    "Кыштым",
    "Лабинск",
    "Лениногорск",
    "Лесосибирск",
    "Лиски",
    "Лобня",
    "Ломоносов",
    "Луга",
    "Майкоп",
    "Междуреченск",
    "Менделеевск",
    "Мензелинск",
    "Миасс",
    "Минеральные Воды",
    "Минусинск",
    "Михайловка",
    "Михайловск",
    "Можга",
    "Надым",
    "Наро-Фоминск",
    "Невинномысск",
    "Нерюнгри",
    "Нефтеюганск",
    "Нижнекамск",
    "Новоуральск",
    "Новочебоксарск",
    "Новодвинск",
    "Новокуйбышевск",
    "Новомичуринск",
    "Новопавловск",
    "Новопетровск",
    "Новоузенск",
    "Новошахтинск",
    "Новотроицк",
    "Ногинск",
    "Ноябрьск",
    "Озерск",
    "Октябрьский",
    "Оленегорск",
    "Орск",
    "Павлово",
    "Павловский Посад",
    "Первоуральск",
    "Переславль-Залесский",
    "Петрозаводск",
    "Петров Вал",
    "Петропавловск-Камчатский",
    "Раменское",
    "Ревда",
    "Реж",
    "Ржев",
    "Рославль",
    "Рошаль",
    "Салават",
    "Сальск",
    "Сарапул",
    "Свободный",
    "Северобайкальск",
    "Серов",
    "Сибай",
    "Симферополь",
    "Славянск-на-Кубани",
    "Слободской",
    "Солнечногорск",
    "Сосновый Бор",
    "Сочи",
    "Старый Оскол",
    "Ступино",
    "Сызрань",
    "Таганрог",
    "Тамбов",
    "Томск",
    "Троицк",
    "Туапсе",
    "Тула",
    "Усть-Илимск",
    "Усть-Кут",
    "Феодосия",
    "Фрязино",
    "Ханты-Мансийск",
    "Хасавюрт",
    "Чайковский",
    "Чапаевск",
    "Череповец",
    "Черногорск",
    "Черняховск",
    "Черкесск",
    "Чистополь",
    "Чита",
    "Шадринск",
    "Шали",
    "Шахты",
    "Шуя",
    "Щекино",
    "Южно-Сахалинск",
    "Юрга",
    "Ялта",
    "Ясный",
    "Можайск"
]
# Функция для очистки названия города (удаляет пробелы и цифры в конце)
def clean_city(city):
    return re.sub(r'\s*\d+$', '', city)

# Очищаем список available_cities
cleaned_cities = [clean_city(city) for city in assistant_cities]

# Дополнительный список городов (из моего ранее составленного списка), где все наименования "нормальные"


# Объединяем оба списка, предварительно очистив названия в available_cities


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

        # Получаем текущую погоду и влажность по координатам
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m&timezone=Europe/Moscow"
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
            winddirection = current_weather.get("winddirection")
            observation_time = current_weather.get("time")
            weathercode = current_weather.get("weathercode")
            description = weather_codes.get(weathercode, f"Код погоды: {weathercode}")

            # Извлекаем данные о влажности из hourly
            humidity = None
            hourly = weather_data.get("hourly")
            if hourly and "time" in hourly and "relativehumidity_2m" in hourly:
                times = hourly["time"]
                humidity_values = hourly["relativehumidity_2m"]
                if observation_time in times:
                    index = times.index(observation_time)
                    humidity = humidity_values[index]

            humidity_str = f"{humidity}%" if humidity is not None else "нет данных"

            return (
                f"Погода в {city_name} (на {observation_time}):\n"
                f"Температура: {temperature}°C\n"
                f"Скорость ветра: {windspeed} км/ч\n"
                f"Направление ветра: {winddirection}°\n"
                f"Влажность: {humidity_str}\n"
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
        cursor.execute("INSERT INTO users (id, place) VALUES (?, ?)", (user_id, "Можайск"))
        conn.commit()
        await message.reply("Вы зарегистрированы! Местность установлена по умолчанию: Можайск")
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
        if new_place.lower() not in [city.lower() for city in assistant_cities]:
            await message.reply(
                "Извините, данный город не доступен. Пожалуйста, выберите город из списка:\n" +
                "\n".join(assistant_cities)
            )
            return
        cursor.execute("UPDATE users SET place = ? WHERE id = ?", (new_place, user_id))
        conn.commit()
        await message.reply(f"Ваша местность обновлена на: {new_place}")
    else:
        # Если аргумент не передан, выводим список доступных городов
        cities_list = "\n".join(assistant_cities)
        await message.reply("Введите в формате: Москва")
        await PlaceState.waiting_for_new_place.set()


# Обработчик для ввода новой местности, когда бот ждёт выбор пользователя
@dp.message_handler(state=PlaceState.waiting_for_new_place)
async def process_new_place(message: types.Message, state: FSMContext):
    new_place = message.text.strip()
    if new_place.lower() not in [city.lower() for city in assistant_cities]:
        await message.reply(
            "Извините, данный город не доступен. Пожалуйста, выберите город из списка:\n" +
            "\n".join(assistant_cities)
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
