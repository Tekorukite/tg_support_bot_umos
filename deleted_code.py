
#async def broadcaster(users, text: str):
    #count = 0
    #try:
        #for user in users:
            #if await send_message_custom(user[0], text):
                #count += await 1
            #await asyncio.sleep(.04)
    #finally:
        #log.info(f" {count} out of {len(users)} messages successful sent.")
    #return count, len(users)


#@dp.message_handler(lambda message: message.text[:7] == 'SENDALL', chat_id=TELEGRAM_SUPPORT_CHAT_ID)
#async def cmd_send_all(message: types.message):
    #cur.execute("SELECT tg_user_id FROM subscribers;")
    #users = cur.fetchall()
    #send = 0
    #total = 0
    #i = 0
    #i_max = (len(users)-1)//25
    #while i <= i_max:
        #if i == i_max:
            #send_now, total_now = await broadcaster(users[i*25+1:], message.text[8:])
        #else:
            #send_now, total_now = await broadcaster(users[i*25+1:(i+1)*25], message.text[8:])
        #log.info(f" {send_now} out of {total_now} messages successful sent for now.")
        #send += send_now
        #total += total_now
    #log.info(f" {send} out of {total} messages successful sent from broadcast handler.")
    
    #await message.reply(f"Сообщение доставлено {send} из {total} пользователей.", parse_mode='Markdown')


#async def cmd_delete_message(chat_id: int, message_id: int) -> bool:
    #try:
        #await bot.delete_message(chat_id=chat_id, message_id=message_id)
    #except MessageToDeleteNotFound:
        #log.exception(f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: not found.")
    #except MessageCantBeDeleted:
        #log.exception(f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: cant be deleted.")
    #except exceptions.RetryAfter as e:
        #log.error(
            #f"Target [CHAT_ID:{chat_id}, MSG_ID:{message_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        #await asyncio.sleep(e.timeout)
        #return await cmd_delete_message(chat_id, message_id)
    #else:
        #return True
    #return False


#@dp.message_handler(lambda message: message.text == 'DELETE BROADCAST', chat_id=TELEGRAM_SUPPORT_CHAT_ID)
#async def cmd_delete_all(message: types.message):
    #cur.execute("""SELECT * FROM broadcast;""")
    #count = 0
    #messages = cur.fetchall()
    #if messages is None or len(messages) == 0:
        #await message.reply("Нечего удалять. Ты точно отправлял броадкасты?", parse_mode='Markdown')
    #else:
        #try:
            #for row in messages:
                #if await cmd_delete_message(row[1], row[2]):
                    #count += 1
                    #await asyncio.sleep(.04)
                    #cur.execute(f"""DELETE FROM broadcast WHERE chat_id = {row[1]} AND message_id = {row[2]};""")
        #finally:
            #log.info(f" {count} out of {len(messages)} messages successfully deleted.")
            #await message.reply(f"Успешно удалено {count} из {len(messages)} сообщений.", parse_mode='Markdown')
            ##cur.execute("""DELETE FROM broadcast;""")
            #db.commit()


#async def send_message_custom(
    #user_id: int, text: str, disable_notification: bool = True
#) -> bool:
    #try:
        #msg = await bot.send_message(
            #user_id,
            #text,
            #disable_notification=disable_notification,
            #parse_mode="markdown",
        #)
    #except exceptions.BotBlocked:
        #log.error(f"Target [ID:{user_id}]: blocked by user")
    #except exceptions.ChatNotFound:
        #log.error(f"Target [ID:{user_id}]: invalid user ID")
    #except exceptions.RetryAfter as e:
        #log.error(
#            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds."
#        )
#        await asyncio.sleep(e.timeout)
#        return await send_message_custom(user_id, text)
#    except exceptions.UserDeactivated:
#        log.error(f"Target [ID:{user_id}]: user is deactivated")
#    except exceptions.TelegramAPIError:
#        log.exception(f"Target [ID:{user_id}]: failed")
#    except:
#        log.error(f"Unexpected error")
#    else:
#        cur.execute(
#            f"""INSERT INTO broadcast (chat_id, message_id) VALUES({msg.chat.id},{msg.message_id});"""
#        )
#        db.commit()
#        return True
#    return False
