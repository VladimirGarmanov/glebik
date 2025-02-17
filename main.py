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
    "Абакан 3",
    "Айхал",
    "Алдан",
    "Алушта",
    "Алыкель",
    "Анадырь",
    "Анапа",
    "Апатиты",
    "Аргахтах",
    "Аргун",
    "Арзамас 2",
    "Артем",
    "Архангельск",
    "Асташово",
    "Астрахань 2",
    "Ахтубинск",
    "Ахты",
    "Ачинск",
    "Балаково",
    "Балашиха",
    "Балтийск",
    "Бараниха",
    "Барнаул",
    "Белгород 2",
    "Белёв",
    "Белозерск 3",
    "Бердск",
    "Березники",
    "Беслан",
    "Бечевинка",
    "Бийск",
    "Билибино",
    "Биробиджан",
    "Бичура",
    "Благовещенск 2",
    "Болхов",
    "Большой Нимныр",
    "Бор",
    "Борзя",
    "Боровичи",
    "Боровск",
    "Братск",
    "Брянск 2",
    "Буйнакск",
    "Валдай 2",
    "Великий Устюг",
    "Верхняя Балкария",
    "Верхняя Пышма",
    "Весьегонск",
    "Вилюйск",
    "Владивосток 5",
    "Владикавказ 2",
    "Владимир",
    "Власиха 2",
    "Волгоград 2",
    "Волгореченск 3",
    "Волжск",
    "Вологда 4",
    "Волоколамск",
    "Волочанка",
    "Ворогово",
    "Воронеж 2",
    "Воскресенск",
    "Выборг",
    "Вытегра 2",
    "Вязьма",
    "Галич",
    "Гвардейск",
    "Горно-Алтайск",
    "Городец",
    "Горячий Ключ",
    "Грозный 4",
    "Гудермес",
    "Гудым",
    "Гурзуф",
    "Дебин",
    "Дербент",
    "Дивеево",
    "Дивногорск 2",
    "Дмитров",
    "Дубна 2",
    "Дудинка 2",
    "Евпатория",
    "Егорьевск",
    "Екатеринбург 8",
    "Елабуга",
    "Елец 3",
    "Елизово",
    "Енисейск",
    "Ерофей Павлович",
    "Железногорск 2",
    "Железнодорожный",
    "Жиганск",
    "Жилинда",
    "Жуковский",
    "Завидово",
    "Заозерный",
    "Зарайск 2",
    "Заречный",
    "Звездный (Пермь-76)",
    "Зеленогорск",
    "Златоуст",
    "Знаменск",
    "Зырянка",
    "Иваново",
    "Ижевск 4",
    "Иркутск 3",
    "Истра",
    "Йошкар-Ола",
    "Кадуй",
    "Кадыкчан",
    "Казань 10",
    "Кайеркан 2",
    "Калининград 6",
    "Калуга 7",
    "Калязин",
    "Камышин",
    "Канск",
    "Карабаш",
    "Касимов",
    "Касли",
    "Каспийск",
    "Катырык",
    "Кемерово 2",
    "Кимжа",
    "Кимры 2",
    "Кинешма 2",
    "Кириллов",
    "Киров 2",
    "Кировск",
    "Клин 2",
    "Клинцы",
    "Козельск",
    "Козьмодемьянск",
    "Коломна 4",
    "Комсомольск-на-Амуре 2",
    "Конаково",
    "Корсаков",
    "Коса",
    "Кострома 11",
    "Красногорск",
    "Краснодар 9",
    "Краснознаменск",
    "Красноярск 8",
    "Кронштадт 2",
    "Кунгур",
    "Курган",
    "Курск",
    "Кызыл",
    "Кюбюме",
    "Кюсюр",
    "Лазаревское",
    "Лесосибирск",
    "Ливны",
    "Лиинахамари",
    "Липецк",
    "Лодейное Поле",
    "Луховицы",
    "Лысьва",
    "Магадан",
    "Магнитогорск",
    "Малая Вишера",
    "Мариинск",
    "Маркс",
    "Матвеев-Курган",
    "Махачкала 2",
    "Междуреченск",
    "Мезень",
    "Мелитополь",
    "Миасс",
    "Минусинск 2",
    "Мирный",
    "Мончегорск",
    "Москва 13",
    "Мурманск 7",
    "Мценск",
    "Мышкин",
    "Мяунджа",
    "Набережные Челны 3",
    "Назрань",
    "Нальчик 2",
    "Нарьян-Мар",
    "Находка",
    "Невьянск",
    "Нерчинск",
    "Нерюнгри 2",
    "Нефтекамск",
    "Нижнеудинск",
    "Нижний Новгород 9",
    "Нижний Тагил 2",
    "Новгород Великий 2",
    "Новоалтайск",
    "Новокузнецк",
    "Новорыбная",
    "Новосибирск 8",
    "Новый Уренгой",
    "Норильск 3",
    "Ноябрьск",
    "Озеры",
    "Оймякон",
    "Окуловка",
    "Оленек",
    "Ольхон",
    "Омск 2",
    "Орёл 2",
    "Оренбург 2",
    "Осташков",
    "Павловский Посад",
    "Палех 2",
    "Паника",
    "Певек",
    "Пенза",
    "Пересвет",
    "Переславль-Залесский 6",
    "Пермь 20",
    "Петрозаводск",
    "Петропавловск-Камчатский 3",
    "Пирамида",
    "Плавск",
    "Плес 3",
    "Подольск 2",
    "Поленово",
    "Помары",
    "Попигай (Сопочное)",
    "Поповка",
    "Потапово",
    "Приволжск",
    "Приисковое",
    "Приморск",
    "Протвино",
    "Псков",
    "Пугачев",
    "Пустозерск",
    "Путорана",
    "Пятигорск",
    "Радужный",
    "Рославль",
    "Ростов",
    "Ростов-на-Дону 6",
    "Рыбинск 4",
    "Рязань 4",
    "Самара 4",
    "Санкт-Петербург 118",
    "Саранск 2",
    "Саратов 7",
    "Сарман",
    "Саров",
    "Саскалых",
    "Сатка",
    "Светлый",
    "Свободный",
    "Североморск",
    "Северск",
    "селигер 2",
    "Сергиев Посад 3",
    "Серпухов 2",
    "Синегорье",
    "Слюдянка",
    "Смоленск 2",
    "Сокол",
    "Солигалич",
    "Соликамск",
    "Солнечный",
    "Солнечный (Ужур)",
    "Соловки",
    "Соловьевск",
    "Сочи 15",
    "Среднеколымск",
    "Средняя Ахтуба",
    "Сростки",
    "Ставрополь",
    "Старая Ладога",
    "Старая Русса",
    "Старица",
    "Старый Оскол",
    "Судак 2",
    "Судиславль",
    "Суздаль 5",
    "Суксун",
    "Сулак",
    "Сургут",
    "Сусуман",
    "Сызрань",
    "Сыктывкар",
    "Таганрог 2",
    "Талдом 2",
    "Талнах",
    "Тамбов",
    "Тарбагатай",
    "Тарко-Сале",
    "Таруса",
    "Тверь 8",
    "Теплый Ключ",
    "Тетюши",
    "Тикси",
    "Тольятти",
    "Томск 3",
    "Томтор",
    "Торжок 5",
    "Тотьма 2",
    "Туапсе",
    "Тула 5",
    "Тура",
    "Туруханск",
    "Тутаев",
    "Тюмень 4",
    "Углич 6",
    "Удачный",
    "Улан-Удэ",
    "Ульяновск",
    "Уссурийск",
    "Усть-Нера",
    "Устье-Кубенское",
    "Устюжна",
    "Уфа 4",
    "Учма 4",
    "Ферапонтово",
    "Фрязино",
    "Хабаровск 6",
    "Хасавюрт",
    "Хатанга 2",
    "Хета",
    "Холуй",
    "Цаган-Толгой 2",
    "Чагода",
    "Чебаркуль",
    "Чебоксары 3",
    "Челябинск 3",
    "Череповец 4",
    "Черноголовка",
    "Чернышевский",
    "Черский",
    "Чехов",
    "Чита",
    "Шексна",
    "Шикотан",
    "Шушенское",
    "Ытык-Кюэль",
    "Электрогорск",
    "Электросталь",
    "Электроугли",
    "Элиста",
    "Эльбрус 2",
    "Энгельс",
    "Энергодар",
    "Эрзин",
    "Южа",
    "Южно-Сахалинск 2",
    "Юрюнг-Хая",
    "Якутск 3",
    "Ярополец",
    "Ярославль 11",
    "Ярцево",
    "Яхрома"
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
        await message.reply("Введите в формате: Москва")
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
