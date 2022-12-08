import logging
from contextlib import suppress
import psycopg2
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import (
    MessageNotModified,
    MessageCantBeDeleted,
    MessageToDeleteNotFound,
)
from aiogram.utils.executor import start_webhook
import keyboards
import texts
from settings import (
    TELEGRAM_TOKEN,
    HEROKU_APP_NAME,
    PORT,
    TELEGRAM_SUPPORT_CHAT_ID,
    TRELLO_KEY,
    TRELLO_TOKEN,
    DATABASE_URL,
    TRELLO_DORM_IDLIST,
)
from aiogram.utils import exceptions
import asyncio
import json
from datetime import datetime
import pytz

storage = MemoryStorage()

MOSCOW = pytz.timezone("Europe/Moscow")

WEBHOOK_URL = f"https://{HEROKU_APP_NAME}.herokuapp.com/{TELEGRAM_TOKEN}"
WEBHOOK_HOST = f"https://{HEROKU_APP_NAME}.herokuapp.com"
WEBHOOK_PATH = f"/{TELEGRAM_TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = PORT
POSSIBLE_DORMITORY_NAMES = ["ГЗ", "ДСЛ", "ФДС", "ДСВ", "ДСК", "ДСШ", "ДСЯ"]


TRELLO_URL = "https://api.trello.com/1/cards"
TRELLO_MSU_BOARD_ID = "5d480632c826f51e58a2162"


class Support(StatesGroup):
    faq = State()
    payment = State()
    dormitory = State()
    building = State()
    room = State()
    name = State()
    phone = State()
    login = State()
    problem = State()
    call_time = State()
    filled = State()
    edit = State()


bot = Bot(token=TELEGRAM_TOKEN, parse_mode="markdownv2")
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("broadcast")
db = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = db.cursor()


@dp.message_handler(commands="start", state="*")
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    cur.execute(
        "SELECT * FROM subscribers WHERE tg_user_id = %s;", [message.from_user.id]
    )
    row = cur.fetchall()
    if row is None or len(row) == 0:
        user_data = (message.from_user.first_name, message.from_user.id)
        cur.execute(
            """INSERT INTO subscribers (name, tg_user_id, reg_date) VALUES(%s, %s, CURRENT_DATE);""",
            user_data,
        )
        cur.execute("COMMIT;")
        print(f"Added user {user_data[0]} with userid={user_data[1]}")
    await message.answer(
        f"Привет, {message.from_user.first_name}. Я бот техподдержки ЮМОС. \n"
        f"Какой вопрос Вас интересует?",
        reply_markup=keyboards.start_kb,
        parse_mode="Markdown",
    )


@dp.message_handler(lambda message: message.text.lower() == "отмена", state="*")
async def cmd_cancel_button(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        f"Какой вопрос Вас интересует?", reply_markup=keyboards.start_kb
    )


@dp.message_handler(commands="payment", state="*")
@dp.message_handler(lambda message: message.text.lower() == "оплата", state="*")
async def cmd_payment(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await Support.payment.set()
    await message.answer(
        f"Каким способом оплаты Вы желаете воспользоваться?\n",
        reply_markup=keyboards.inline_kb_payment,
    )


@dp.callback_query_handler(text="credit_card", state=Support.payment)
async def cmd_credit_card(call: types.CallbackQuery) -> None:
    await call.message.edit_text(
        texts.CREDIT_CARD_TEXT,
        reply_markup=InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(
                "Личный кабинет", url="https://msu.umos.ru/?module=01_login"
            ),
            keyboards.inline_back,
            keyboards.inline_cancel,
        ),
    )


@dp.callback_query_handler(text="sb_online", state=Support.payment)
async def cmd_sb_online(call: types.CallbackQuery) -> None:
    await call.message.edit_text(
        texts.SB_TEXT,
        reply_markup=InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(
                "Подробная инструкция",
                url="https://msu.umos.ru/files/sberbank_online.pdf",
            ),
            keyboards.inline_back,
            keyboards.inline_cancel,
        ),
    )


@dp.callback_query_handler(text="sb_atm", state=Support.payment)
async def cmd_sb_atm(call: types.CallbackQuery) -> None:
    await call.message.edit_text(
        texts.SB_TEXT,
        reply_markup=InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(
                "Подробная инструкция", url="https://msu.umos.ru/files/sberbank.pdf"
            ),
            keyboards.inline_back,
            keyboards.inline_cancel,
        ),
    )


@dp.callback_query_handler(text="vtb_atm", state=Support.payment)
async def cmd_vtb_atm(call: types.CallbackQuery) -> None:
    await call.message.edit_text(
        texts.VTB_TEXT,
        reply_markup=InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(
                "Подробная инструкция", url="https://msu.umos.ru/files/vtb.pdf"
            ),
            keyboards.inline_back,
            keyboards.inline_cancel,
        ),
    )


@dp.callback_query_handler(text="back", state=Support.payment)
async def cmd_back_payment(call: types.CallbackQuery) -> None:
    await call.message.edit_text(
        f"Каким способом оплаты Вы желаете воспользоваться?\n",
        reply_markup=keyboards.inline_kb_payment,
    )


@dp.callback_query_handler(text="cancel", state="*")
async def cmd_cancel(call: types.CallbackQuery, state: FSMContext) -> None:
    await state.finish()
    with suppress(MessageNotModified):
        await call.message.delete_reply_markup()
        await call.answer()
        await call.message.answer(
            f"Какой вопрос Вас интересует?", reply_markup=keyboards.start_kb
        )


@dp.message_handler(commands="router", state="*")
@dp.message_handler(
    lambda message: message.text.lower() == "настройка роутера", state="*"
)
async def cmd_router(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        f"Информацию о настройке роутера для работы в нашей сети можно найти по ссылке ниже\.",
        reply_markup=keyboards.inline_kb_router,
    )


@dp.message_handler(commands="faq", state="*")
@dp.message_handler(lambda message: message.text.lower() == "faq", state="*")
async def cmd_faq(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await Support.faq.set()
    await state.update_data(current_faq_page=1)
    await message.answer(
        f"Распространенные вопросы:\n", reply_markup=keyboards.inline_faq_kb_1
    )


@dp.callback_query_handler(Text(startswith="faq_"), state=Support.faq)
async def cmd_faq_question(call: types.CallbackQuery, state: FSMContext) -> None:
    question = int(call.data[4:])
    kb = InlineKeyboardMarkup(row_width=1)
    if question == 0:
        kb.add(InlineKeyboardButton("Заявка в техподдержку", callback_data="support"))
    elif question == 1:
        kb.add(
            InlineKeyboardButton("Тарифы", url="https://msu.umos.ru/?module=tariffs")
        )
    elif question == 2:
        kb.add(
            InlineKeyboardButton(
                "Способы оплаты", url="https://msu.umos.ru/?module=oplata"
            )
        )
    elif question == 3:
        kb.add(
            InlineKeyboardButton(
                "Личный кабинет", url="https://msu.umos.ru/?module=01_login"
            )
        )
    elif question == 4:
        kb.add(InlineKeyboardButton("Заявка в техподдержку", callback_data="support"))
    elif question == 5:
        kb.add(
            InlineKeyboardButton(
                "Личный кабинет", url="https://msu.umos.ru/?module=01_login"
            )
        )
        kb.add(InlineKeyboardButton("Заявка в техподдержку", callback_data="support"))
    elif question == 6:
        kb.add(
            InlineKeyboardButton(
                "Личный кабинет", url="https://msu.umos.ru/?module=01_login"
            )
        )
    elif question == 9:
        kb.add(
            InlineKeyboardButton(
                "Настройка роутера", url="https://msu.umos.ru/routers.html"
            )
        )
    kb.add(keyboards.inline_back, keyboards.inline_cancel)
    await call.message.edit_text(
        texts.FAQ_Q[question] + texts.FAQ_Ans[question], reply_markup=kb
    )


@dp.callback_query_handler(text="back", state=Support.faq)
async def cmd_cb_faq(call: types.CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    if user_data["current_faq_page"] == 1:
        await call.message.edit_text(
            f"Распространенные вопросы:\n", reply_markup=keyboards.inline_faq_kb_1
        )
    elif user_data["current_faq_page"] == 2:
        await call.message.edit_text(
            f"Распространенные вопросы:\n", reply_markup=keyboards.inline_faq_kb_2
        )


@dp.callback_query_handler(text="next_page", state=Support.faq)
async def cmd_next(call: types.CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    await state.update_data(current_faq_page=user_data["current_faq_page"] + 1)
    await call.message.edit_reply_markup(keyboards.inline_faq_kb_2)


@dp.callback_query_handler(text="prev_page", state=Support.faq)
async def cmd_next(call: types.CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    await state.update_data(current_faq_page=user_data["current_faq_page"] - 1)
    await call.message.edit_reply_markup(keyboards.inline_faq_kb_1)


@dp.callback_query_handler(text="support", state="*")
async def cmd_support_inline(call: types.CallbackQuery, state: FSMContext) -> None:
    await state.finish()
    await call.message.answer("Выберите общежитие:", reply_markup=keyboards.dorm_kb)
    await Support.dormitory.set()


@dp.message_handler(commands="support", state="*")
@dp.message_handler(
    lambda message: message.text.lower() == "заявка в техподдержку", state="*"
)
async def cmd_support(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    cur.execute(
        "SELECT * FROM subscribers WHERE tg_user_id = %s;", [message.from_user.id]
    )
    row = cur.fetchall()
    if row is None or len(row) == 0:
        user = (message.from_user.first_name, message.from_user.id)
        cur.execute(
            """INSERT INTO subscribers (name, tg_user_id, reg_date) VALUES(%s, %s, CURRENT_DATE);""",
            user,
        )
        db.commit()
        print(f"Added user {user[0]} with еп_user_id={user[1]}")
    cur.execute(
        f"""SELECT * FROM tickets 
        WHERE user_id=(SELECT user_id FROM subscribers WHERE tg_user_id={message.from_user.id})
        ORDER BY ticket_id DESC
        LIMIT 1;"""
    )
    ticket = cur.fetchone()
    # print(ticket)
    if ticket is None or len(ticket) == 0:
        await message.answer("Выберите общежитие:", reply_markup=keyboards.dorm_kb)
        await Support.dormitory.set()
    else:
        await state.update_data(chosen_dormitory=ticket[2])
        await state.update_data(chosen_building=ticket[3])
        await state.update_data(chosen_room=ticket[4])
        await state.update_data(chosen_name=ticket[5])
        await state.update_data(chosen_phone=ticket[7])
        await state.update_data(chosen_login=ticket[6])
        user_data = await state.get_data()
        await message.answer(
            f"В прошлый раз Вы указали следующие данные:\n"
            f"Общежитие: {user_data['chosen_dormitory']}\n"
            f"Корпус: {user_data['chosen_building']}\n"
            f"Комната: {user_data['chosen_room']}\n"
            f"Имя: {user_data['chosen_name']}\n"
            f"Номер телефона: {user_data['chosen_phone']}\n"
            f"Логин: {user_data['chosen_login']}\n",
            reply_markup=InlineKeyboardMarkup(row_width=1, one_time_keyboard=True).add(
                keyboards.inline_commit, keyboards.inline_edit, keyboards.inline_cancel
            ),
            parse_mode="",
        )


@dp.message_handler(state=Support.dormitory)
async def cmd_building(message: types.Message, state: FSMContext) -> None:
    if message.text not in POSSIBLE_DORMITORY_NAMES:
        await message.answer(
            "Пожалуйста, выберите общежитие, используя клавиатуру ниже\.",
            reply_markup=keyboards.dorm_kb,
        )
        return
    await state.update_data(chosen_dormitory=message.text)

    await Support.next()
    await message.answer(
        'Укажите корпус\. Если нет, поставьте "\-"',
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.building)
async def cmd_building(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_building=message.text)
    await Support.next()
    await message.answer(
        "Введите номер комнаты\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.room)
async def cmd_room(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_room=message.text)
    await Support.next()
    await message.answer(
        "Укажите, как к Вам обращаться\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.name)
async def cmd_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_name=message.text)
    await Support.next()
    await message.answer(
        "Введите номер телефона\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.phone)
async def cmd_phone(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_phone=message.text)
    await Support.next()
    await message.answer(
        "Укажите свой логин или лицевой счет\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.login)
async def cmd_login(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_login=message.text)
    await Support.next()
    await message.answer(
        "Опишите проблему \(подробно\)\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.callback_query_handler(text="commit", state="*")
async def cmd_continue_problem(call: types.CallbackQuery, state: FSMContext) -> None:
    await Support.problem.set()
    await call.message.answer(
        "Опишите проблему \(подробно\)\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.problem)
async def cmd_problem(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_problem=message.text)
    await Support.next()
    await message.answer(
        "В какое время можно перезвонить \(Например: с 15\.00 до 23\.00 или 01\.01\.18 днем\)\.",
        reply_markup=InlineKeyboardMarkup(one_time_keyboard=True).add(keyboards.inline_cancel),
    )


@dp.message_handler(state=Support.call_time)
async def cmd_call_time(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chosen_time=message.text)

    await Support.filled.set()
    await cmd_print(message, state)


async def cmd_print(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    await message.answer(
        f"Полученные данные:\n"
        f"Общежитие: {user_data['chosen_dormitory']}\n"
        f"Корпус: {user_data['chosen_building']}\n"
        f"Комната: {user_data['chosen_room']}\n"
        f"Имя: {user_data['chosen_name']}\n"
        f"Номер телефона: {user_data['chosen_phone']}\n"
        f"Логин: {user_data['chosen_login']}\n"
        f"Пробелма: {user_data['chosen_problem']}\n"
        f"Время звонка: {user_data['chosen_time']}\n",
        reply_markup=InlineKeyboardMarkup(row_width=1, one_time_keyboard=True).add(
            keyboards.inline_send, keyboards.inline_edit, keyboards.inline_cancel
        ),
        parse_mode="",
    )


@dp.callback_query_handler(text="edit", state="*")
async def cmd_edit(call: types.CallbackQuery, state: FSMContext) -> None:
    await cmd_support(call.message, state)


@dp.callback_query_handler(text="send", state=Support.filled)
async def cmd_send(call: types.CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    cur.execute(
        f"""SELECT * FROM tickets 
        WHERE user_id=(SELECT user_id FROM subscribers WHERE tg_user_id={call.from_user.id}) AND request_date=CURRENT_DATE
        ORDER BY ticket_id DESC
        LIMIT 5;"""
    )
    row = cur.fetchall()
    if row is None or len(row) < 5:
        cur.execute(
            f"""INSERT INTO tickets 
                    (user_id, dorm, building, room, fullname, login, phone, request_date) 
                    VALUES((SELECT user_id FROM subscribers WHERE tg_user_id={call.from_user.id}), %s, %s, %s, %s, %s, %s, CURRENT_DATE);""",
            (
                user_data["chosen_dormitory"],
                user_data["chosen_building"],
                user_data["chosen_room"],
                user_data["chosen_name"],
                user_data["chosen_login"],
                user_data["chosen_phone"],
            ),
        )
        db.commit()
        TICKET_TIME = datetime.now(MOSCOW).strftime("%d-%m-%Y %H:%M:%S")
        trello_headers = {"Accept": "application/json"}
        trello_query = {
            "idList": TRELLO_DORM_IDLIST[f"{user_data['chosen_dormitory']}"],
            "key": TRELLO_KEY,
            "token": TRELLO_TOKEN,
            "name": f"{TICKET_TIME} {user_data['chosen_login']} {user_data['chosen_phone']} from TG_BOT",
            "desc": f"{user_data['chosen_name']}\n{user_data['chosen_phone']}\n{user_data['chosen_login']}\n{user_data['chosen_dormitory']} {user_data['chosen_building']} {user_data['chosen_room']}\n{TICKET_TIME}\n{user_data['chosen_problem']}\n{user_data['chosen_time']}",
        }

        trello_sent = requests.request(
            "POST", TRELLO_URL, headers=trello_headers, params=trello_query
        )
        if trello_sent:
            await call.message.answer("Заявка успешно отправлена\!")
            await state.finish()
            await call.message.answer(
                f"Какой вопрос Вас интересует?", reply_markup=keyboards.start_kb
            )
            log.info(
                f"Trello card created {TICKET_TIME} {user_data['chosen_login']}"
            )
        else:
            await call.message.answer(
                "Что\-то пошло не так\. Попробуйте еще раз\.\n"
                "Вы можете написать нам на почту: msu.umos@gmail.com\n"
                "или позвонить по телефону: +7 (499) 553\-02\-17")
            await cmd_print(call.message, state)
            log.warning(
                f"Trello card was NOT created {TICKET_TIME} {user_data['chosen_login']} {user_data['chosen_phone']}"
            )

    else:
        await call.message.answer(
            "К сожалению, Вы отправили уже 5 заявок в техподдержку сегодня. "
            "Вы можете написать нам на почту: msu.umos@gmail.com\n"
            "или позвонить по телефону: +7 (499) 553-02-17",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel),
        )
        log.warning(f"SPAMER DETECTED login: {user_data['chosen_login']}, name: {user_data['chosen_name']}, {user_data['chosen_phone']}")


@dp.message_handler(state="*")
async def cmd_unknown(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Я не смог распознать данную команду. Попробуйте воспользоваться клавиатурой ниже.",
        parse_mode="Markdown",
    )
    await cmd_cancel_button(message, state)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS subscribers (
                        user_id serial PRIMARY KEY,
                        name text,
                        tg_user_id bigint,
                        reg_date date DEFAULT CURRENT_DATE
                        );"""
    )
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id serial PRIMARY KEY,
                        user_id integer,
                        dorm text NOT NULL,
                        building text DEFAULT '-'::text,
                        room text NOT NULL,
                        fullname text NOT NULL,
                        login text NOT NULL,
                        phone text NOT NULL,
                        request_date date DEFAULT CURRENT_DATE,
                        FOREIGN KEY (user_id)
                        REFERENCES subscribers (user_id) ON DELETE CASCADE
                        );"""
    )
    db.commit()


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    db.close()
    logging.warning('Bye!')


if __name__ == "__main__":
    # Запуск бота
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
