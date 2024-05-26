import os
import logging
import asyncio
import datetime
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from psycopg2 import OperationalError

# Настройки подключения к базе данных
DB_NAME = "finance_bot"
DB_USER = "kolesnikov_knowledge_base"
DB_PASSWORD = "9999"
DB_HOST = "127.0.0.1"

# Установка уровня логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot_token = os.getenv('TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher()

# Функция для подключения к базе данных
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password = DB_PASSWORD,
            host=DB_HOST
        )
        logging.info("Подключение к базе данных выполнено успешно")
        return conn
    except OperationalError as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None


# Обработчик команды /start
async def start(message: types.Message):
    await message.reply(
        "Привет! Я твой финансовый бот. Используй /reg для регистрации и /add_operation для добавления новой операции.")


# Обработчик команды /reg
async def register(message: types.Message):
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (chat_id) VALUES (%s)", (message.chat.id,))
            conn.commit()
            await message.reply("Ты успешно зарегистрирован!")
        except Exception as e:
            logging.error(f"Ошибка регистрации пользователя: {e}")
            await message.reply("Возникла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        finally:
            cur.close()
            conn.close()


# Обработчик команды /add_operation
async def add_operation(message: types.Message):
    await message.reply("Пожалуйста, выбери тип операции:",
                        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Расход"),
                                                                                   KeyboardButton("Доход")))
    await types.ChatActions.typing()


# Обработчик текстовых сообщений (выбор типа операции)
async def choose_operation_type(message: types.Message):
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            await cur.execute("INSERT INTO operations (date, sum, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
                              (datetime.datetime.now().date(), 0, message.chat.id, message.text))
            conn.commit()
            await message.reply("Пожалуйста, введи сумму в рублях:")
        except Exception as e:
            logging.error(f"Ошибка добавления операции: {e}")
            await message.reply("Возникла ошибка при добавлении операции. Пожалуйста, попробуйте позже.")
        finally:
            cur.close()
            conn.close()


# Обработчик текстовых сообщений (ввод суммы операции)
async def process_sum(message: types.Message):
    try:
        sum = float(message.text)
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("UPDATE operations SET sum = %s WHERE chat_id = %s ORDER BY id DESC LIMIT 1",
                            (sum, message.chat.id))
                conn.commit()
                await message.reply("Пожалуйста, введи дату операции (ГГГГ-ММ-ДД):")
            except Exception as e:
                logging.error(f"Ошибка обновления операции: {e}")
                await message.reply("Возникла ошибка при обновлении операции. Пожалуйста, попробуйте позже.")
            finally:
                cur.close()
                conn.close()
    except ValueError:
        await message.reply("Неверная сумма. Пожалуйста, введите корректное число.")

# Обработчик текстовых сообщений (ввод даты операции)
async def process_date(message: types.Message):
    try:
        date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("UPDATE operations SET date = %s WHERE chat_id = %s ORDER BY id DESC LIMIT 1", (date, message.chat.id))
                conn.commit()
                await message.reply("Операция успешно добавлена!")
            except Exception as e:
                logging.error(f"Ошибка обновления операции: {e}")
                await message.reply("Возникла ошибка при обновлении операции. Пожалуйста, попробуйте позже.")
            finally:
                cur.close()
                conn.close()
    except ValueError:
        await message.reply("Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")
    except Exception as e:
        logging.error(f"Ошибка при обработке даты: {e}")
        await message.reply("Возникла ошибка при обработке даты. Пожалуйста, попробуйте позже.")

# Обработчик команды /operations
@dp.message_handler(commands=['operations'])
async def view_operations(message: types.Message):
    conn = connect_to_db()
    if conn:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("RUB"), types.KeyboardButton("EUR"), types.KeyboardButton("USD"))
        await message.reply("Выберите валюту для просмотра операций:", reply_markup=markup)
    else:
        logging.error("Ошибка подключения к базе данных")

# Обработчик ввода валюты
@dp.message_handler(lambda message: message.text in ["RUB", "EUR", "USD"], state="*")
async def process_currency(message: types.Message):
    currency = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("РАСХОДНЫЕ ОПЕРАЦИИ"), types.KeyboardButton("ДОХОДНЫЕ ОПЕРАЦИИ"), types.KeyboardButton("ВСЕ"))
    await message.reply("Выберите тип операций для просмотра:", reply_markup=markup)
    # Сохраняем выбранную валюту в состоянии
    await message.answer(currency)
    await types.ChatActions.typing()

# Обработчик ввода типа операций
@dp.message_handler(lambda message: message.text in ["РАСХОДНЫЕ ОПЕРАЦИИ", "ДОХОДНЫЕ ОПЕРАЦИИ", "ВСЕ"], state="*")
async def process_operation_type(message: types.Message):
    currency = await dp.current_state().get_data()
    operation_type = message.text
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        try:
            if operation_type == "ВСЕ":
                cur.execute("SELECT * FROM operations WHERE chat_id = %s", (message.chat.id,))
            else:
                cur.execute("SELECT * FROM operations WHERE chat_id = %s AND type_operation = %s", (message.chat.id, "ДОХОД" if operation_type == "ДОХОДНЫЕ ОПЕРАЦИИ" else "РАСХОД"))
            operations = cur.fetchall()
            if currency != "RUB":
                rate = await get_exchange_rate(currency)
                operations = [(op[0], op[1], op[2] * rate, op[3], op[4]) for op in operations]
            if operations:
                response = "\n".join([f"{op[1]}: {op[2]} {currency} - {op[4]}" for op in operations])
                await message.reply(response)
            else:
                await message.reply("Операции не найдены.")
        except psycopg2.Error as e:
            logging.error(f"Ошибка выполнения запроса: {e}")
        finally:
            cur.close()
            conn.close()
    else:
        logging.error("Ошибка подключения к базе данных")

# Функция для получения курса обмена валюты
async def get_exchange_rate(currency: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'http://195.58.54.159:8000/rate?currency={currency}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['rate']
                else:
                    return 1
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при получении курса обмена: {e}")
            return 1

# Регистрация обработчиков команд и сообщений
dp.register_message_handler(start, commands=["start"])
dp.register_message_handler(register, commands=["reg"])
dp.register_message_handler(add_operation, commands=["add_operation"])
dp.register_message_handler(choose_operation_type)
dp.register_message_handler(process_sum, state="sum_state")
dp.register_message_handler(process_date, state="date_state")
dp.register_message_handler(view_operations, commands=["operations"])

# Запуск бота
if __name__ == '__main__':
    asyncio.run(dp.start_polling())
