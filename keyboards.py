from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

inline_cancel = InlineKeyboardButton('В начало', callback_data='cancel')
inline_commit = InlineKeyboardButton('Продолжить', callback_data='commit')
inline_back = InlineKeyboardButton('Назад', callback_data='back')
inline_credit_card = InlineKeyboardButton('Картой онлайн', callback_data='credit_card')
inline_sb_online = InlineKeyboardButton('Сбер Онлайн', callback_data='sb_online')
inline_sb_atm = InlineKeyboardButton('Сбер терминал', callback_data='sb_atm')
inline_vtb_atm = InlineKeyboardButton('ВТБ терминал', callback_data='vtb_atm')
inline_faq = InlineKeyboardButton('Назад', callback_data='faq')
inline_send = InlineKeyboardButton('Отправить', callback_data='send')
inline_edit = InlineKeyboardButton('Редактировать', callback_data='edit')
inline_dorm = InlineKeyboardButton('Общежитие', callback_data='edit_dorm')
inline_name = InlineKeyboardButton('Имя', callback_data='edit_name')
inline_building = InlineKeyboardButton('Корпус', callback_data='edit_building')
inline_room = InlineKeyboardButton('Комната', callback_data='edit_room')
inline_login = InlineKeyboardButton('Логин', callback_data='edit_login')
inline_phone = InlineKeyboardButton('Телефон', callback_data='edit_phone')
inline_problem = InlineKeyboardButton('Проблема', callback_data='edit_problem')
inline_call_time = InlineKeyboardButton('Время звонка', callback_data='edit_call_time')
button_faq = KeyboardButton('FAQ')
button_router = KeyboardButton('Настройка роутера')
button_payment = KeyboardButton('Оплата')
button_support = KeyboardButton('Заявка в техподдержку')
button_ds = KeyboardButton('ГЗ')
button_dsl = KeyboardButton('ДСЛ')
button_fds = KeyboardButton('ФДС')
button_dsv = KeyboardButton('ДСВ')
button_dsk = KeyboardButton('ДСК')
button_dssh = KeyboardButton('ДСШ')
button_dsy = KeyboardButton('ДСЯ')
button_cancel = KeyboardButton('Отмена')

inline_edit_kb = InlineKeyboardMarkup(row_width=2)
inline_edit_kb.add(inline_dorm, inline_building,
                   inline_room, inline_name,
                   inline_phone, inline_login,
                   inline_problem, inline_call_time,
                   inline_back)

dorm_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, one_time_keyboard=True)
dorm_kb.add(button_ds, button_dsl, button_fds, button_dsv, button_dsk, button_dsy, button_dssh)
dorm_kb.add(button_cancel)

start_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
start_kb.add(button_payment, button_router, button_faq, button_support)

inline_kb_payment = InlineKeyboardMarkup(row_width=2)
inline_kb_payment.add(inline_credit_card, inline_sb_online, inline_sb_atm, inline_vtb_atm, inline_cancel)

inline_kb_router = InlineKeyboardMarkup(row_width=1)
inline_kb_router.add(InlineKeyboardButton('Настройка роутера', url='https://msu.umos.ru/routers.html'), inline_cancel)

inline_faq_kb_1 = InlineKeyboardMarkup(row_width=1)
inline_faq_kb_1.add(InlineKeyboardButton('Куда обращаться?', callback_data='faq_0'))
inline_faq_kb_1.add(InlineKeyboardButton('Сколько стоит?', callback_data='faq_1'))
inline_faq_kb_1.add(InlineKeyboardButton('Как оплачивать?', callback_data='faq_2'))
inline_faq_kb_1.add(InlineKeyboardButton('Заблокировали за неуплату.', callback_data='faq_3'))
inline_faq_kb_1.add(
    InlineKeyboardButton('Интернет отключили \nменьше чем через месяц \nпосле оплаты?', callback_data='faq_4'))
inline_faq_kb_1.add(InlineKeyboardButton('Следующая страница ▶️', callback_data='next_page'))
inline_faq_kb_1.add(inline_cancel)

inline_faq_kb_2 = InlineKeyboardMarkup(row_width=1)
inline_faq_kb_2.add(
    InlineKeyboardButton('Появилась необходимость \nуехать на длительное время.', callback_data='faq_5'))
inline_faq_kb_2.add(InlineKeyboardButton('Как мне поменять тариф?', callback_data='faq_6'))
inline_faq_kb_2.add(InlineKeyboardButton('Что делать при переезде?', callback_data='faq_7'))
inline_faq_kb_2.add(InlineKeyboardButton('Как расторгнуть договор?', callback_data='faq_8'))
inline_faq_kb_2.add(
    InlineKeyboardButton('Интернет работает \nтолько на одном устройстве.', callback_data='faq_9'))
inline_faq_kb_2.add(InlineKeyboardButton('◀️ Предыдущая страница', callback_data='prev_page'))
inline_faq_kb_2.add(inline_cancel)
