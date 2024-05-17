import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

import os

logging.basicConfig(level=logging.INFO)

bot_token = os.getenv('TOKEN')

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

currency_rates = {}

class ConvertCurrencyStates(StatesGroup):
    wait_currency_name = State()
    wait_amount = State()

class CurrencyStates(StatesGroup):
    wait_currency_name = State()
    wait_currency_rate = State()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот для работы с валютой.\n"
                        "Чтобы сохранить курс валюты используйте команду /save_currency\n"
                        "Для конвертации валюты используйте команду /convert")

@dp.message_handler(commands=['save_currency'])
async def save_currency(message: types.Message):
    await message.answer("Введите название валюты:")
    await CurrencyStates.wait_currency_name.set()

@dp.message_handler(state=CurrencyStates.wait_currency_name)
async def save_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    if currency_name:
        await state.update_data(currency_name=currency_name)
        await message.answer("Введите курс валюты к рублю:")
        await CurrencyStates.wait_currency_rate.set()
    else:
        await message.answer("Вы ввели некорректное название валюты.")

@dp.message_handler(state=CurrencyStates.wait_currency_rate)
async def save_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data['currency_name']
        currency_rates[currency_name] = rate
        await message.answer(f"Курс валюты {currency_name} успешно сохранен.")
        await state.finish()
    except ValueError:
        await message.answer("Неверный формат курса. Пожалуйста, введите число.")

@dp.message_handler(commands=['convert'])
async def convert_currency(message: types.Message):
    await message.answer("Введите название валюты:")
    await ConvertCurrencyStates.wait_currency_name.set()

@dp.message_handler(state=ConvertCurrencyStates.wait_currency_name)
async def convert_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    if currency_name in currency_rates:
        await state.update_data(currency_name=currency_name)
        await message.answer("Введите количество валюты:")
        await ConvertCurrencyStates.next()
    else:
        await message.answer("Курс указанной валюты не сохранен. Пожалуйста, используйте команду /save_currency.")

@dp.message_handler(state=ConvertCurrencyStates.wait_amount)
async def convert_currency_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data.get("currency_name")
        if currency_name in currency_rates:
            rate = currency_rates[currency_name]
            converted_amount = amount * rate
            await message.answer(f"{amount} {currency_name} = {converted_amount} RUB")
            await state.finish()
        else:
            await message.answer("Курс указанной валюты не сохранен. Пожалуйста, используйте команду /save_currency.")
    except ValueError:
        await message.answer("Неверный формат суммы. Пожалуйста, введите число.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)