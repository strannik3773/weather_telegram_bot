import os
import aiogram.dispatcher.filters
import dotenv
import requests
import datetime
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

dotenv.load_dotenv(dotenv.find_dotenv())
open_weather_token = os.getenv('open_weather_token')
tg_bot_token = os.getenv('tg_bot_token')
bot = Bot(token=tg_bot_token)
dp = Dispatcher(bot)
inline_buttons = [[InlineKeyboardButton(text='Погода на завтра', callback_data='btn1'),
                   InlineKeyboardButton(text='Погода на 5 дней', callback_data='btn2')]]
inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
hour_now = (datetime.datetime.now().time().hour // 3) * 3
hours_to_tomorrow = 24 + 9 - hour_now
code_to_smile = {
    "Clear": "Ясно \U00002600",
    "Clouds": "Облачно \U00002601",
    "Rain": "Дождь \U00002614",
    "Drizzle": "Дождь \U00002614",
    "Thunderstorm": "Гроза \U000026A1",
    "Snow": "Снег \U0001F328",
    "Mist": "Туман \U0001F32B"
}

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Напиши мне название города и я пришлю сводку погоды!")


@dp.message_handler(aiogram.dispatcher.filters.Text)
async def get_weather(message: types.Message):
    city = message.text
    try:
        query = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={open_weather_token}"
        r = requests.get(query)
        data = r.json()
        latitude = data[0]['lat']
        longitude = data[0]['lon']
        query = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid={open_weather_token}"
        r = requests.get(query)
        data = r.json()
        cur_weather = data["main"]["temp"]
        weather_description = data["weather"][0]["main"]
        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, не пойму что там за погода!"

        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        length_of_the_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
            data["sys"]["sunrise"])

        await message.reply(f"*** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ***\n"
                            f"Погода в городе: {city}\nТемпература: {cur_weather}C° {wd}\n"
                            f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
                            f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня: {length_of_the_day}\n"
                            f"***Хорошего дня!***", reply_markup=inline_kb
                            )
    except (Exception,):
        await message.reply(f"\U00002620 Проверьте название города \U00002620")


@dp.callback_query_handler(lambda c: c.data)
async def inline_kb_handler(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    latitude = 0.0
    longitude = 0.0
    try:
        code = int(callback_query.data[-1])
    except (Exception,):
        print('Error of callback.data')
    city = callback_query.message.text.split('\n')[1].split(': ')[1]
    query = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={open_weather_token}"
    r = requests.get(query)
    if r.status_code == 200:
        data = r.json()
        latitude = data[0]['lat']
        longitude = data[0]['lon']
        daily_uri_request = f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&units=metric&appid={open_weather_token}"
        daily_answ = requests.get(daily_uri_request)
        if daily_answ.status_code == 200:
            daily_data = daily_answ.json()
            tomorrow_weather = daily_data['list'][hours_to_tomorrow // 3]
            tomorrow_weather_msg = f"*** {tomorrow_weather['dt_txt']} ***\nПогода в городе: {city}\n" \
                                   f"Температура: {tomorrow_weather['main']['temp']}C° {code_to_smile[tomorrow_weather['weather'][0]['main']]}\n" \
                                   f"Влажность: {tomorrow_weather['main']['humidity']}%\n" \
                                   f"Давление: {tomorrow_weather['main']['pressure']} мм.рт.ст\n" \
                                   f"Ветер: {tomorrow_weather['wind']['speed']} м/с\n***Хорошего дня!***"
        else:
            await bot.send_message(callback_query.from_user.id, text=f"Ошибка получения данных о погоде")
        if code == 1:
            await bot.send_message(callback_query.from_user.id, text=f"{tomorrow_weather_msg}")
        elif code == 2:
            daily_weather_msg = f'Погода в городе: {city}\n'
            for i in range(0, 5):
                daily_weather_msg = daily_weather_msg + f"\n*** {daily_data['list'][hours_to_tomorrow // 3 + i * 8]['dt_txt']} *** \n" \
                                                        f"Температура: {daily_data['list'][hours_to_tomorrow // 3 + i * 8]['main']['temp']}C° {code_to_smile[daily_data['list'][hours_to_tomorrow // 3 + i * 8]['weather'][0]['main']]}\n" \
                                                        f"Влажность: {daily_data['list'][hours_to_tomorrow // 3 + i * 8]['main']['humidity']}%\n" \
                                                        f"Давление: {daily_data['list'][hours_to_tomorrow // 3 + i * 8]['main']['pressure']} мм.рт.ст\n" \
                                                        f"Ветер: {daily_data['list'][hours_to_tomorrow // 3 + i * 8]['wind']['speed']} м/с\n"
            await bot.send_message(callback_query.from_user.id, text=f"{daily_weather_msg}")

if __name__ == '__main__':
    executor.start_polling(dp)
