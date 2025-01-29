import logging
from read_json import read, write

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

file_path = 'users.json'

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def generateReplyMarkup(update: Update):
    user_info = read(file_path)[str(update.effective_user.id)]
    if(user_info["notJerking"] == True):
        return InlineKeyboardMarkup(
        [
           [InlineKeyboardButton("обдрочился", callback_data="/doneJerkedOff"),  InlineKeyboardButton("хочу дрочить", callback_data="/wannaJerkOff")],
           [InlineKeyboardButton("сбросить", callback_data="/reset"), InlineKeyboardButton("обновить статистику", callback_data="/statistics")]
        ])
    else:
        return InlineKeyboardMarkup(
        [
           [InlineKeyboardButton("стать мужчиной", callback_data="/becomeTheMan"),  InlineKeyboardButton("хочу дрочить", callback_data="/wannaJerkOff")],
           [InlineKeyboardButton("сбросить", callback_data="/reset"), InlineKeyboardButton("обновить статистику", callback_data="/statistics")]
        ])

async def loginIfDoesntExist(update: Update):
    user_info = read(file_path)
    user_id = str(update.effective_user.id)

    if(user_id not in user_info):
        user_info[user_id] = {}
        user_info[user_id]['username'] = update.effective_user.username
        user_info[user_id]['full_name'] = update.effective_user.full_name
        user_info[user_id]['first_name'] = update.effective_user.first_name
        user_info[user_id]['last_name'] = update.effective_user.last_name
        user_info[user_id]['name'] = update.effective_user.name
        user_info[user_id]['id'] = update.effective_user.id
        user_info[user_id]['wantedCount'] = 0
        user_info[user_id]['relapsedCount'] = 0
        user_info[user_id]['notJerking'] = False

        write(file_path, user_info)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    await update.message.reply_html(rf"Привет {user.mention_html()}! Я запрещаю тебе дрочить.")

    await loginIfDoesntExist(update)
    await update.effective_message.delete()

    table = await statisticsTable()

    await update.message.reply_html(text=table, reply_markup=generateReplyMarkup(update))

async def statisticsTable() -> None:
    users_from_storage = read(file_path)

    statuses_from_users = []

    for uid, user_from_storage in users_from_storage.items():
        user_mention = rf'<a href="tg://user?id={user_from_storage["id"]}">{user_from_storage["full_name"]}</a>'
        statuses_from_users.append(rf"{user_mention}: хотел дрочить {user_from_storage["wantedCount"]} раз(а), дрочил {user_from_storage["relapsedCount"]}")
    
    statuses_html = "\n".join(statuses_from_users) if statuses_from_users else "Пока нет статистики."

    return statuses_html


async def wannaJerkOff(update: Update) -> None:
    user_info = read(file_path)
    user_id = str(update.effective_user.id)

    user_info[user_id]['wantedCount'] += 1

    write(file_path, user_info)

async def reset(update: Update):
    user_info = read(file_path)
    user_id = str(update.effective_user.id)

    user_info[user_id]['wantedCount'] = 0
    user_info[user_id]['relapsedCount'] = 0
    user_info[user_id]['notJerking'] = False

    write(file_path, user_info)

async def doneJerkedOff(update: Update):
    user_info = read(file_path)
    user_id = str(update.effective_user.id)

    user_info[user_id]['relapsedCount'] += 1
    user_info[user_id]['notJerking'] = False

    write(file_path, user_info)

async def becomeTheMan(update: Update):
    user_info = read(file_path)
    user_id = str(update.effective_user.id)

    user_info[user_id]['notJerking'] = True

    write(file_path, user_info)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    match query.data:
        case "/statistics":
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))

        case "/wannaJerkOff":
            await wannaJerkOff(update)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))
        
        case "/reset":
            await reset(update)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))
        
        case "/doneJerkedOff":
            await doneJerkedOff(update)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))
        
        case "/becomeTheMan":
            await becomeTheMan(update)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))


def main() -> None:
    application = Application.builder().token("7876823433:AAHsS_vLaoisMWilukDJbooqiq7VNDBboyE").build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()