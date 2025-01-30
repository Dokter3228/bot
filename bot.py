import logging
from datetime import datetime
from read_json import read, write

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import Forbidden

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TOKEN")

file_path = 'data.json'

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def getCurrentTime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generateReplyMarkup(update: Update):
    user = read(file_path)["users"][str(update.effective_user.id)]

    if(user["notJerking"] == True):
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

def loginIfDoesntExist(update: Update):
    data = read(file_path)
    user_id = str(update.effective_user.id)

    if not data.get("chat_ids"):
        data["chat_ids"] = [update.effective_chat.id]
    elif update.effective_chat.id not in data["chat_ids"]:
        data["chat_ids"].append(update.effective_chat.id)

    if("users" not in data):
        data["users"] = {}

    users = data.get("users")

    if(user_id not in data["users"]):
        users[user_id] = {}
        users[user_id]['username'] = update.effective_user.username
        users[user_id]['full_name'] = update.effective_user.full_name
        users[user_id]['first_name'] = update.effective_user.first_name
        users[user_id]['last_name'] = update.effective_user.last_name
        users[user_id]['name'] = update.effective_user.name
        users[user_id]['id'] = update.effective_user.id
        users[user_id]['wantedCount'] = 0
        users[user_id]['relapsedCount'] = 0
        users[user_id]['notJerking'] = False

    write(file_path, data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    await update.message.reply_html(rf"Привет {user.mention_html()}! Я запрещаю тебе дрочить.")

    loginIfDoesntExist(update)
    await update.effective_message.delete()

    table = await statisticsTable()

    await update.message.reply_html(text=table, reply_markup=generateReplyMarkup(update))

async def statisticsTable() -> None:
    data = read(file_path)

    statuses_from_users = []

    for uid, user_from_storage in data["users"].items():
        timeOfTry = datetime.strptime(user_from_storage["notJerkingDateTime"], "%Y-%m-%d %H:%M:%S") if user_from_storage.get("notJerkingDateTime") else None
        timePassedFromBecomingTheMan = (datetime.now() - timeOfTry).days if timeOfTry else ""

        theMan = f" (мужчина {timePassedFromBecomingTheMan if timePassedFromBecomingTheMan else "0" } дн)" if user_from_storage["notJerking"] else ""

        user_mention = rf'<a href="tg://user?id={user_from_storage["id"]}">{user_from_storage["full_name"]}</a>{theMan}'
        statuses_from_users.append(rf"{user_mention}: хотел дрочить {user_from_storage["wantedCount"]} раз(а), дрочил {user_from_storage["relapsedCount"]}")
    
    statuses_html = "\n".join(statuses_from_users) if statuses_from_users else "Пока нет статистики."

    return statuses_html


async def wannaJerkOff(update: Update) -> None:
    data = read(file_path)
    users = data.get("users")
    user_id = str(update.effective_user.id)

    users[user_id]['wantedCount'] += 1

    write(file_path, data)

async def reset(update: Update):
    data = read(file_path)
    users = data.get("users")
    user_id = str(update.effective_user.id)

    users[user_id]['wantedCount'] = 0
    users[user_id]['relapsedCount'] = 0
    users[user_id]['notJerking'] = False

    write(file_path, data)

async def doneJerkedOff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = read(file_path)
    users = data.get("users")
    chat_ids = data.get("chat_ids")

    user_id = str(update.effective_user.id)

    users[user_id]['relapsedCount'] += 1
    users[user_id]['notJerking'] = False
    users[user_id]['notJerkingDateTime'] = None

    try:
        for chat_id in chat_ids:
            await context.bot.send_message(chat_id=chat_id,text= rf'<a href="tg://user?id={user_id}">{users[user_id]["full_name"]}</a> обдрочился!', parse_mode="HTML")
    except Forbidden as e:
        print(e)

    write(file_path, data)

async def becomeTheMan(update: Update):
    data = read(file_path)
    users = data.get("users")
    user_id = str(update.effective_user.id)

    users[user_id]['notJerking'] = True
    users[user_id]['notJerkingDateTime'] = getCurrentTime()

    write(file_path, data)

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
            await doneJerkedOff(update, context)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))
        
        case "/becomeTheMan":
            await becomeTheMan(update)
            table = await statisticsTable()
            await query.edit_message_text(text=table, parse_mode="HTML", reply_markup=generateReplyMarkup(update))


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()