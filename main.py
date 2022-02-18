import logging
from contextlib import suppress
import psycopg2
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified, MessageCantBeDeleted, MessageToDeleteNotFound
from aiogram.utils.executor import start_webhook
import keyboards
import texts
from settings import TELEGRAM_TOKEN, HEROKU_APP_NAME, PORT, TELEGRAM_SUPPORT_CHAT_ID
from aiogram.utils import exceptions
import asyncio

storage = MemoryStorage()

WEBHOOK_URL = f"https://{HEROKU_APP_NAME}.herokuapp.com/{TELEGRAM_TOKEN}"
WEBHOOK_HOST = f"https://{HEROKU_APP_NAME}.herokuapp.com"
WEBHOOK_PATH = f"/{TELEGRAM_TOKEN}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = PORT
POSSIBLE_DORMITORY_NAMES = ['ГЗ', 'ДСЛ', 'ФДС', 'ДСВ', 'ДСК', 'ДСШ', 'ДСЯ']
DS_GFORM = {
    'url': 'https://docs.google.com/forms/d/e/1FAIpQLSdPxSyJxmyuoyidT5vPx4_cD53118OcT7j5Qv-sOiNz2G03mg/formResponse',
    'name': 'entry.651748368',
    'phone': 'entry.539972922',
    'login': 'entry.1963659940',
    'room': 'entry.234720864',
    'problem': 'entry.835582122',
    'time': 'entry.681152745'
}
DSL_GFORM = {
    'url': 'https://docs.google.com/forms/d/e/1FAIpQLSe_2_hHZQHAz1x1u5rbMd51nY4ruWBNWib5QODlCCtT_Qtphg/formResponse',
    'name': 'entry.315753433',
    'phone': 'entry.329797146',
    'login': 'entry.782191196',
    'room': 'entry.100962389',
    'problem': 'entry.1401337801',
    'time': 'entry.97627762',
    'building': 'entry.1452465197',
    'building_other': 'entry.1452465197.other_option_response'
}
FDS_GFORM = {
    'url': 'https://docs.google.com/forms/d/e/1FAIpQLSeMIc5TuwUiegFx7BWHXJrPjbm1HP-Gefsgvx_BKi2WLxNPbg/formResponse',
    'name': 'entry.315753433',
    'phone': 'entry.329797146',
    'login': 'entry.782191196',
    'room': 'entry.100962389',
    'problem': 'entry.1401337801',
    'time': 'entry.97627762',
    'building': 'entry.1452465197',
    'building_other': 'entry.1452465197.other_option_response'
}
DSVKSY_GFORM = {
    'url': 'https://docs.google.com/forms/d/e/1FAIpQLSfjy_GB8kMNn7zQZL7KeJPhqiGhhoq42IfLgybkbtXeNdaTIA/formResponse',
    'name': 'entry.315753433',
    'phone': 'entry.329797146',
    'login': 'entry.782191196',
    'dorm': 'entry.1452465197',
    'room': 'entry.100962389',
    'problem': 'entry.1401337801',
    'time': 'entry.97627762'
}


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


bot = Bot(token=TELEGRAM_TOKEN, parse_mode='markdownv2')
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')
db = psycopg2.connect(
    user="umosbot",
    password="UmosSupportBotMSU",
    host="3.16.161.63",
    database="umosdb",
    port=5432
)
cur = db.cursor()


@dp.message_handler(commands="start", state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    cur.execute("SELECT * FROM subscribers WHERE tg_user_id = %s;", [message.from_user.id])
    row = cur.fetchall()
    if row is None or len(row) == 0:
        user_data = (message.from_user.first_name, message.from_user.id)
        cur.execute("""INSERT INTO subscribers (name, tg_user_id, reg_date) VALUES(%s, %s, CURRENT_DATE);""", user_data)
        cur.execute("COMMIT;")
        print(f"Added user {user_data[0]} with userid={user_data[1]}")
    await message.answer(f'Привет, {message.from_user.first_name}. Я бот техподдержки ЮМОС. \n'
                         f'Какой вопрос Вас интересует?',
                         reply_markup=keyboards.start_kb, parse_mode='Markdown')


@dp.message_handler(lambda message: message.text.lower() == 'отмена', state='*')
async def cmd_cancel_button(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(f'Какой вопрос Вас интересует?', reply_markup=keyboards.start_kb)


async def send_message_custom(user_id: int, text: str, disable_notification: bool = True) -> bool:
    try:
        msg = await bot.send_message(user_id, text, disable_notification=disable_notification, parse_mode='markdown')
        await bot.pin_chat_message(chat_id=msg.chat.id, message_id=msg.message_id)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message_custom(user_id, text)
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    except:
        log.error(f"Unexpected error")
    else:
        cur.execute(f"""INSERT INTO broadcast (chat_id, message_id) VALUES({msg.chat.id},{msg.message_id});""")
        return True
    return False


async def insult_owner(text: str, repeats: int) -> (int, int):
    insult_count = 0;
    try:
        for i in range (repeats):
            if await send_message_custom(230957711, text):
                insult_count += 1
            await asyncio.sleep(.04)
            i += 1
    finally:
        log.info(f" {insult_count} out of {repeats} messages successful sent.")
    return insult_count, repeats
                                  
@dp.message_handler(lambda message: message.text[:6] == 'INSULT', chat_id=TELEGRAM_SUPPORT_CHAT_ID)
async def cmd_insult_teko(message: types.message):
    repeats = int(message.text[7:10])
    text = message.text[11:]
    send, total = await insult_owner(text, repeats)
    log.info(f" {send} out of {total} messages successful sent.")
    
    




async def broadcaster(users, text: str) -> (int, int):
    count = 0
    try:
        for user in users:
            if await send_message_custom(user[0], text):
                count += 1
            await asyncio.sleep(.04)
    finally:
        log.info(f" {count} out of {len(users)} messages successful sent.")
    return count, len(users)


@dp.message_handler(lambda message: message.text[:7] == 'SENDALL', chat_id=TELEGRAM_SUPPORT_CHAT_ID)
async def cmd_send_all(message: types.message):
    cur.execute("SELECT tg_user_id FROM subscribers;")
    users = cur.fetchall()
    send = 0
    total = 0
    i = 0
    i_max = (len(users)-1)//25
    while i <= i_max:
        if i == i_max:
            send_now, total_now = await broadcaster(users[i*25+1:], message.text[8:])
        else:
            send_now, total_now = await broadcaster(users[i*25+1:(i+1)*25], message.text[8:])
        log.info(f" {send_now} out of {total_now} messages successful sent for now.")
        send += send_now
        total += total_now
    log.info(f" {send} out of {total} messages successful sent.")
    
    #await message.reply(f"Сообщение доставлено {send} из {total} пользователей.", parse_mode='Markdown')


async def cmd_delete_message(chat_id: int, message_id: int) -> bool:
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except MessageToDeleteNotFound:
        log.exception(f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: not found.")
    except MessageCantBeDeleted:
        log.exception(f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: cant be deleted.")
    except exceptions.RetryAfter as e:
        log.error(
            f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await cmd_delete_message(chat_id, message_id)
    else:
        return True
    return False


@dp.message_handler(lambda message: message.text == 'DELETE BROADCAST', chat_id=TELEGRAM_SUPPORT_CHAT_ID)
async def cmd_delete_all(message: types.message):
    cur.execute("""SELECT * FROM broadcast;""")
    count = 0
    messages = cur.fetchall()
    if messages is None or len(messages) == 0:
        await message.reply("Нечего удалять. Ты точно отправлял броадкасты?", parse_mode='Markdown')
    else:
        try:
            for row in messages:
                if await cmd_delete_message(row[1], row[2]):
                    count += 1
                    await asyncio.sleep(.04)
                    cur.execute(f"""DELETE FROM broadcast WHERE chat_id = {row[1]} AND message_id = {row[2]};""")
        finally:
            log.info(f" {count} out of {len(messages)} messages successfully deleted.")
            await message.reply(f"Успешно удалено {count} из {len(messages)} сообщений.", parse_mode='Markdown')
            #cur.execute("""DELETE FROM broadcast;""")
            db.commit()


@dp.message_handler(commands="payment", state='*')
@dp.message_handler(lambda message: message.text.lower() == 'оплата', state='*')
async def cmd_payment(message: types.Message, state: FSMContext):
    await state.finish()
    await Support.payment.set()
    await message.answer(f"Каким способом оплаты Вы желаете воспользоваться?\n",
                         reply_markup=keyboards.inline_kb_payment)


@dp.callback_query_handler(text='credit_card', state=Support.payment)
async def cmd_credit_card(call: types.CallbackQuery):
    await call.message.edit_text(texts.CREDIT_CARD_TEXT, reply_markup=InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('Личный кабинет', url='https://msu.umos.ru/?module=01_login'), keyboards.inline_back,
        keyboards.inline_cancel))


@dp.callback_query_handler(text='sb_online', state=Support.payment)
async def cmd_sb_online(call: types.CallbackQuery):
    await call.message.edit_text(texts.SB_TEXT, reply_markup=InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('Подробная инструкция', url='https://msu.umos.ru/files/sberbank_online.pdf'),
        keyboards.inline_back, keyboards.inline_cancel))


@dp.callback_query_handler(text='sb_atm', state=Support.payment)
async def cmd_sb_atm(call: types.CallbackQuery):
    await call.message.edit_text(texts.SB_TEXT, reply_markup=InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('Подробная инструкция', url='https://msu.umos.ru/files/sberbank.pdf'),
        keyboards.inline_back, keyboards.inline_cancel))


@dp.callback_query_handler(text='vtb_atm', state=Support.payment)
async def cmd_vtb_atm(call: types.CallbackQuery):
    await call.message.edit_text(texts.VTB_TEXT, reply_markup=InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('Подробная инструкция', url='https://msu.umos.ru/files/vtb.pdf'), keyboards.inline_back,
        keyboards.inline_cancel))


@dp.callback_query_handler(text='back', state=Support.payment)
async def cmd_back_payment(call: types.CallbackQuery):
    await call.message.edit_text(f"Каким способом оплаты Вы желаете воспользоваться?\n",
                                 reply_markup=keyboards.inline_kb_payment)


@dp.callback_query_handler(text='cancel', state="*")
async def cmd_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    with suppress(MessageNotModified):
        await call.message.delete_reply_markup()
        await call.answer()
        await call.message.answer(f'Какой вопрос Вас интересует?', reply_markup=keyboards.start_kb)


@dp.message_handler(commands="router", state='*')
@dp.message_handler(lambda message: message.text.lower() == 'настройка роутера', state='*')
async def cmd_router(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(f"Информацию о настройке роутера для работы в нашей сети можно найти по ссылке ниже\.",
                         reply_markup=keyboards.inline_kb_router)


@dp.message_handler(commands="faq", state='*')
@dp.message_handler(lambda message: message.text.lower() == 'faq', state='*')
async def cmd_faq(message: types.Message, state: FSMContext):
    await state.finish()
    await Support.faq.set()
    await state.update_data(current_faq_page=1)
    await message.answer(f'Распространенные вопросы:\n', reply_markup=keyboards.inline_faq_kb_1)


@dp.callback_query_handler(Text(startswith="faq_"), state=Support.faq)
async def cmd_faq_question(call: types.CallbackQuery, state: FSMContext):
    question = int(call.data[4:])
    kb = InlineKeyboardMarkup(row_width=1)
    if question == 0:
        kb.add(InlineKeyboardButton('Заявка в техподдержку', callback_data='support'))
    elif question == 1:
        kb.add(InlineKeyboardButton('Тарифы', url='https://msu.umos.ru/?module=tariffs'))
    elif question == 2:
        kb.add(InlineKeyboardButton('Способы оплаты', url='https://msu.umos.ru/?module=oplata'))
    elif question == 3:
        kb.add(InlineKeyboardButton('Личный кабинет', url='https://msu.umos.ru/?module=01_login'))
    elif question == 4:
        kb.add(InlineKeyboardButton('Заявка в техподдержку', callback_data='support'))
    elif question == 5:
        kb.add(InlineKeyboardButton('Личный кабинет', url='https://msu.umos.ru/?module=01_login'))
        kb.add(InlineKeyboardButton('Заявка в техподдержку', callback_data='support'))
    elif question == 6:
        kb.add(InlineKeyboardButton('Личный кабинет', url='https://msu.umos.ru/?module=01_login'))
    elif question == 9:
        kb.add(InlineKeyboardButton('Настройка роутера', url='https://msu.umos.ru/routers.html'))
    kb.add(keyboards.inline_back, keyboards.inline_cancel)
    await call.message.edit_text(texts.FAQ_Q[question] + texts.FAQ_Ans[question], reply_markup=kb)


@dp.callback_query_handler(text='back', state=Support.faq)
async def cmd_cb_faq(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    if user_data['current_faq_page'] == 1:
        await call.message.edit_text(f'Распространенные вопросы:\n', reply_markup=keyboards.inline_faq_kb_1)
    elif user_data['current_faq_page'] == 2:
        await call.message.edit_text(f'Распространенные вопросы:\n', reply_markup=keyboards.inline_faq_kb_2)


@dp.callback_query_handler(text='next_page', state=Support.faq)
async def cmd_next(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await state.update_data(current_faq_page=user_data['current_faq_page'] + 1)
    await call.message.edit_reply_markup(keyboards.inline_faq_kb_2)


@dp.callback_query_handler(text='prev_page', state=Support.faq)
async def cmd_next(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await state.update_data(current_faq_page=user_data['current_faq_page'] - 1)
    await call.message.edit_reply_markup(keyboards.inline_faq_kb_1)


@dp.callback_query_handler(text='support', state='*')
async def cmd_support_inline(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer('Выберите общежитие:', reply_markup=keyboards.dorm_kb)
    await Support.dormitory.set()


@dp.message_handler(commands="support", state='*')
@dp.message_handler(lambda message: message.text.lower() == 'заявка в техподдержку', state='*')
async def cmd_support(message: types.Message, state: FSMContext):
    await state.finish()
    cur.execute(
        f"""SELECT * FROM tickets 
        WHERE user_id=(SELECT user_id FROM subscribers WHERE tg_user_id={message.from_user.id})
        ORDER BY ticket_id DESC
        LIMIT 1;""")
    ticket = cur.fetchone()
    print(ticket)
    if ticket is None or len(ticket) == 0:
        await message.answer('Выберите общежитие:', reply_markup=keyboards.dorm_kb)
        await Support.dormitory.set()
    else:
        await state.update_data(chosen_dormitory=ticket[2])
        await state.update_data(chosen_building=ticket[3])
        await state.update_data(chosen_room=ticket[4])
        await state.update_data(chosen_name=ticket[5])
        await state.update_data(chosen_phone=ticket[7])
        await state.update_data(chosen_login=ticket[6])
        user_data = await state.get_data()
        await message.answer(f"В прошлый раз Вы указали следующие данные:\n"
                             f"Общежитие: {user_data['chosen_dormitory']}\n"
                             f"Корпус: {user_data['chosen_building']}\n"
                             f"Комната: {user_data['chosen_room']}\n"
                             f"Имя: {user_data['chosen_name']}\n"
                             f"Номер телефона: {user_data['chosen_phone']}\n"
                             f"Логин: {user_data['chosen_login']}\n",
                             reply_markup=InlineKeyboardMarkup(row_width=1).add(keyboards.inline_commit,
                                                                                keyboards.inline_edit,
                                                                                keyboards.inline_cancel), parse_mode=""
                             )


@dp.message_handler(state=Support.dormitory)
async def cmd_building(message: types.Message, state: FSMContext):
    if message.text not in POSSIBLE_DORMITORY_NAMES:
        await message.answer("Пожалуйста, выберите общежитие, используя клавиатуру ниже\.",
                             reply_markup=keyboards.dorm_kb)
        return
    await state.update_data(chosen_dormitory=message.text)

    await Support.next()
    await message.answer('Укажите корпус\. Если нет, поставьте "\-"',
                         reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.building)
async def cmd_building(message: types.Message, state: FSMContext):
    await state.update_data(chosen_building=message.text)
    await Support.next()
    await message.answer("Введите номер комнаты\.", reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.room)
async def cmd_room(message: types.Message, state: FSMContext):
    await state.update_data(chosen_room=message.text)
    await Support.next()
    await message.answer("Укажите, как к Вам обращаться\.",
                         reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.name)
async def cmd_name(message: types.Message, state: FSMContext):
    await state.update_data(chosen_name=message.text)
    await Support.next()
    await message.answer("Введите номер телефона\.", reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.phone)
async def cmd_phone(message: types.Message, state: FSMContext):
    await state.update_data(chosen_phone=message.text)
    await Support.next()
    await message.answer("Укажите свой логин или лицевой счет\.",
                         reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.login)
async def cmd_login(message: types.Message, state: FSMContext):
    await state.update_data(chosen_login=message.text)
    await Support.next()
    await message.answer("Опишите проблему \(подробно\)\.",
                         reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.callback_query_handler(text='commit', state='*')
async def cmd_continue_problem(call: types.CallbackQuery, state: FSMContext):
    await Support.problem.set()
    await call.message.answer("Опишите проблему \(подробно\)\.",
                              reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.problem)
async def cmd_problem(message: types.Message, state: FSMContext):
    await state.update_data(chosen_problem=message.text)
    await Support.next()
    await message.answer("В какое время можно перезвонить \(Например: с 15\.00 до 23\.00 или 01\.01\.18 днем\)\.",
                         reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state=Support.call_time)
async def cmd_call_time(message: types.Message, state: FSMContext):
    await state.update_data(chosen_time=message.text)

    await Support.filled.set()
    await cmd_print(message, state)


async def cmd_print(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(f"Полученные данные:\n"
                         f"Общежитие: {user_data['chosen_dormitory']}\n"
                         f"Корпус: {user_data['chosen_building']}\n"
                         f"Комната: {user_data['chosen_room']}\n"
                         f"Имя: {user_data['chosen_name']}\n"
                         f"Номер телефона: {user_data['chosen_phone']}\n"
                         f"Логин: {user_data['chosen_login']}\n"
                         f"Пробелма: {user_data['chosen_problem']}\n"
                         f"Время звонка: {user_data['chosen_time']}\n",
                         reply_markup=InlineKeyboardMarkup(row_width=1).add(keyboards.inline_send,
                                                                            keyboards.inline_edit,
                                                                            keyboards.inline_cancel), parse_mode="")


@dp.callback_query_handler(text='edit', state='*')
async def cmd_edit(call: types.CallbackQuery, state: FSMContext):
    await cmd_support(call.message, state)


@dp.callback_query_handler(text='send', state=Support.filled)
async def cmd_send(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    cur.execute(
        f"""SELECT * FROM tickets 
        WHERE user_id=(SELECT user_id FROM subscribers WHERE tg_user_id={call.from_user.id}) AND request_date=CURRENT_DATE
        ORDER BY ticket_id DESC
        LIMIT 5;""")
    row = cur.fetchall()
    if row is None or len(row) < 5:
        cur.execute(f"""INSERT INTO tickets 
                    (user_id, dorm, building, room, fullname, login, phone, request_date) 
                    VALUES((SELECT user_id FROM subscribers WHERE tg_user_id={call.from_user.id}), %s, %s, %s, %s, %s, %s, CURRENT_DATE);""",
                    (user_data['chosen_dormitory'], user_data['chosen_building'], user_data['chosen_room'],
                     user_data['chosen_name'], user_data['chosen_login'], user_data['chosen_phone'])
                    )
        db.commit()
        if user_data['chosen_dormitory'] in ['ДСВ', 'ДСК', 'ДСШ', 'ДСЯ']:
            url = DSVKSY_GFORM['url']
            sending_data = {
                DSVKSY_GFORM['dorm']: user_data['chosen_dormitory'] + ' ' + user_data['chosen_building'],
                DSVKSY_GFORM['room']: user_data['chosen_room'],
                DSVKSY_GFORM['name']: user_data['chosen_name'],
                DSVKSY_GFORM['login']: user_data['chosen_login'],
                DSVKSY_GFORM['phone']: user_data['chosen_phone'] + ' from TG_BOT',
                DSVKSY_GFORM['problem']: user_data['chosen_problem'],
                DSVKSY_GFORM['time']: user_data['chosen_time']
            }
        elif user_data['chosen_dormitory'] == 'ДСЛ':
            url = DSL_GFORM['url']
            sending_data = {
                DSL_GFORM['building_other']: user_data['chosen_building'],
                DSL_GFORM['building']: '__other_option__',
                DSL_GFORM['room']: user_data['chosen_room'],
                DSL_GFORM['name']: user_data['chosen_name'],
                DSL_GFORM['login']: user_data['chosen_login'],
                DSL_GFORM['phone']: user_data['chosen_phone'] + ' from TG_BOT',
                DSL_GFORM['problem']: user_data['chosen_problem'],
                DSL_GFORM['time']: user_data['chosen_time']
            }
        elif user_data['chosen_dormitory'] == 'ФДС':
            url = FDS_GFORM['url']
            sending_data = {
                FDS_GFORM['building_other']: user_data['chosen_building'],
                FDS_GFORM['building']: '__other_option__',
                FDS_GFORM['room']: user_data['chosen_room'],
                FDS_GFORM['name']: user_data['chosen_name'],
                FDS_GFORM['login']: user_data['chosen_login'],
                FDS_GFORM['phone']: user_data['chosen_phone'] + ' from TG_BOT',
                FDS_GFORM['problem']: user_data['chosen_problem'],
                FDS_GFORM['time']: user_data['chosen_time']
            }
        elif user_data['chosen_dormitory'] == 'ГЗ':
            url = DS_GFORM['url']
            sending_data = {
                DS_GFORM['room']: user_data['chosen_building'] + ' ' + user_data['chosen_room'],
                DS_GFORM['name']: user_data['chosen_name'],
                DS_GFORM['login']: user_data['chosen_login'],
                DS_GFORM['phone']: user_data['chosen_phone'] + ' from TG_BOT',
                DS_GFORM['problem']: user_data['chosen_problem'],
                DS_GFORM['time']: user_data['chosen_time']
            }
        sent = requests.post(url, sending_data)
        if sent:
            await call.message.answer('Заявка успешно отправлена\!')
            await state.finish()
            await call.message.answer(f'Какой вопрос Вас интересует?', reply_markup=keyboards.start_kb)
        else:
            await call.message.answer('Что-то пошло не так\. Попробуйте еще раз\.')
            await cmd_print(call.message, state)
    else:
        await call.message.answer("К сожалению, Вы отправили уже 5 заявок в техподдержку сегодня. "
                                  "Вы можете написать нам на почту: msu.umos@gmail.com\n"
                                  "или позвонить по телефону: +7 (499) 553-02-17",
                                  parse_mode='Markdown',
                                  reply_markup=InlineKeyboardMarkup().add(keyboards.inline_cancel))


@dp.message_handler(state='*')
async def cmd_unknown(message: types.Message, state: FSMContext):
    await message.answer("Я не смог распознать данную команду. Попробуйте воспользоваться клавиатурой ниже.",
                         parse_mode='Markdown')
    await cmd_cancel_button(message, state)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


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
