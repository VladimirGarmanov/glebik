
import os
import logging
import asyncio
import sqlite3
import aiohttp
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

# Токен бота из переменной окружения или напрямую
API_TOKEN = os.getenv("BOT_TOKEN", "7775481098:AAGm_yzn3r9J9p2mYQWZIfqj52o84WtOvdI")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота, диспетчера и хранилища состояний
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключение к SQLite (файл users.db)
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Таблица chats: chat_id, выбранный город и тип чата (private/group/supergroup)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id    INTEGER PRIMARY KEY,
        place      TEXT,
        chat_type  TEXT
    )
""")
conn.commit()

# Список доступных городов
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

# Функция очистки названия города (удаляет цифры в конце)
def clean_city(city: str) -> str:
    return re.sub(r'\s*\d+$', '', city)

# Словарь кодов погоды Open-Meteo
weather_codes = {
    0: "Ясно", 1: "Преимущественно ясно", 2: "Местами облачно", 3: "Пасмурно",
    45: "Туман", 48: "Иней", 51: "Лёгкая морось", 53: "Умеренная морось",
    55: "Сильная морось", 56: "Лёгкий ледяной дождь", 57: "Сильный ледяной дождь",
    61: "Небольшой дождь", 63: "Умеренный дождь", 65: "Сильный дождь",
    66: "Лёгкий ледяной дождь", 67: "Сильный ледяной дождь", 71: "Небольшой снегопад",
    73: "Умеренный снегопад", 75: "Сильный снегопад", 77: "Снежные зерна",
    80: "Небольшой дождь", 81: "Умеренный дождь", 82: "Сильный дождь",
    85: "Лёгкий снегопад", 86: "Сильный снегопад", 95: "Гроза",
    96: "Гроза с небольшим градом", 99: "Гроза с сильным градом",
}

# Глобальные для оповещений
alert_status = {}
alert_date = None

# Получение погоды
async def get_weather(place: str) -> str:
    async with aiohttp.ClientSession() as session:
        geocode_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={place}&count=1&language=ru&format=json"
        )
        async with session.get(geocode_url, ssl=False) as geo_resp:
            if geo_resp.status != 200:
                return f"Ошибка геокодирования для {place}."
            geo = await geo_resp.json()
            if not geo.get("results"):
                return f"Город {place} не найден."
            loc = geo["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            city_name = loc.get("name", place)

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true&hourly=relativehumidity_2m"
            f"&timezone=Europe/Moscow"
        )
        async with session.get(weather_url, ssl=False) as w_resp:
            if w_resp.status != 200:
                return f"Ошибка получения погоды для {city_name}."
            data = await w_resp.json()
            cw = data.get("current_weather") or {}
            temp = cw.get("temperature")
            ws = cw.get("windspeed")
            wd = cw.get("winddirection")
            obs_time = cw.get("time")
            code = cw.get("weathercode")
            desc = weather_codes.get(code, f"Код: {code}")

            hum = None
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            hums = hourly.get("relativehumidity_2m", [])
            if obs_time in times:
                hum = hums[times.index(obs_time)]
            hum_str = f"{hum}%" if hum is not None else "нет данных"

            return (
                f"Погода в {city_name} (на {obs_time}):\n"
                f"Температура: {temp}°C\n"
                f"Ветер: {ws} км/ч, {wd}°\n"
                f"Влажность: {hum_str}\n"
                f"Состояние: {desc}"
            )

# Получение скорости ветра
async def get_wind_speed(place: str) -> float:
    async with aiohttp.ClientSession() as session:
        geocode_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={place}&count=1&language=ru&format=json"
        )
        async with session.get(geocode_url, ssl=False) as geo_resp:
            if geo_resp.status != 200:
                return None
            geo = await geo_resp.json()
            if not geo.get("results"):
                return None
            loc = geo["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true&timezone=Europe/Moscow"
        )
        async with session.get(weather_url, ssl=False) as w_resp:
            if w_resp.status != 200:
                return None
            data = await w_resp.json()
            cw = data.get("current_weather") or {}
            return cw.get("windspeed")

# Фоновые оповещения ветра
async def check_alerts():
    global alert_date, alert_status
    while True:
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        today = now.date()
        if alert_date != today:
            alert_status.clear()
            alert_date = today

        if 9 <= now.hour < 18:
            cursor.execute("SELECT chat_id, place FROM chats")
            rows = cursor.fetchall()
            city_chats = {}
            for chat_id, place in rows:
                city_chats.setdefault(place, []).append(chat_id)

            for city, chat_ids in city_chats.items():
                if alert_status.get(city):
                    continue
                ws = await get_wind_speed(city)
                if ws and ws > 36:
                    for cid in chat_ids:
                        try:
                            await bot.send_message(
                                cid,
                                f"Срочное сообщение: в городе {city} ветер {ws} км/ч — оставайтесь дома!"
                            )
                        except Exception as e:
                            logging.error(f"Ошибка при отправке в чат {cid}: {e}")
                    alert_status[city] = True

        await asyncio.sleep(300)

# FSM для /place
class PlaceState(StatesGroup):
    waiting_for_new_place = State()

# /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO chats (chat_id, place, chat_type) VALUES (?, ?, ?)",
            (chat_id, "Можайск", chat_type)
        )
        conn.commit()
        await message.reply("Бот активирован! Местность по умолчанию: Можайск.")
    else:
        await message.reply("Этот чат уже зарегистрирован.")

# /weather
@dp.message_handler(commands=["weather"])
async def weather_command(message: types.Message):
    chat_id = message.chat.id
    cursor.execute("SELECT place FROM chats WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        await message.reply("Чат не зарегистрирован. Используйте /start.")
        return
    info = await get_weather(row[0])
    await bot.send_message(chat_id, info)

# /place
@dp.message_handler(commands=["place"])
async def place_command(message: types.Message):
    chat_id = message.chat.id
    args = message.get_args().strip()
    if args:
        new_city = args
        if new_city.lower() not in [c.lower() for c in assistant_cities]:
            await message.reply(
                "Город не доступен. Выберите из списка:\n" + "\n".join(assistant_cities)
            )
            return
        cursor.execute(
            "UPDATE chats SET place = ? WHERE chat_id = ?",
            (new_city, chat_id)
        )
        conn.commit()
        await message.reply(f"Местность обновлена: {new_city}")
    else:
        await message.reply("Введите город после команды, например: /place Москва")
        await PlaceState.waiting_for_new_place.set()

@dp.message_handler(state=PlaceState.waiting_for_new_place)
async def process_new_place(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    new_city = message.text.strip()
    if new_city.lower() not in [c.lower() for c in assistant_cities]:
        await message.reply(
            "Город не доступен. Выберите из списка:\n" + "\n".join(assistant_cities)
        )
        return
    cursor.execute(
        "UPDATE chats SET place = ? WHERE chat_id = ?",
        (new_city, chat_id)
    )
    conn.commit()
    await message.reply(f"Местность обновлена: {new_city}")
    await state.finish()

# Ежедневная рассылка в 9:00 МСК
def seconds_until_target() -> float:
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()

async def broadcast_weather():
    while True:
        wait = seconds_until_target()
        logging.info(f"Ждём {wait} сек. до рассылки погоды в 9:00 МСК.")
        await asyncio.sleep(wait)
        cursor.execute("SELECT chat_id, place FROM chats")
        rows = cursor.fetchall()
        for chat_id, place in rows:
            info = await get_weather(place)
            try:
                await bot.send_message(chat_id, info)
            except Exception as e:
                logging.error(f"Ошибка при рассылке в чат {chat_id}: {e}")

async def on_startup(dp: Dispatcher):
    asyncio.create_task(broadcast_weather())
    asyncio.create_task(check_alerts())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)