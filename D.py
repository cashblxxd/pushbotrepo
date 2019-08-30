# coding=utf-8
import re
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
#import logging
from pprint import pprint
from uuid import uuid4
from datetime import date
from telegram import ParseMode
import traceback
from telegram.ext import CallbackQueryHandler
from telegram.utils.helpers import escape_markdown
from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegramcalendar
from datetime import datetime, timedelta
from json import load, dump
from calendr import week, days, time_hours, time_minutes
import schedule
from time import sleep
from dateutil.relativedelta import relativedelta
from stuff import get_admin_stats, get_translation, get_help, get_token_desc, get_payment_ad, get_menu_text, get_referral_text, get_buy_text
from telegram import LabeledPrice
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, PreCheckoutQueryHandler)
from calendar import monthrange


def get_tz():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"UTC{i}:00", callback_data=f"tz::{i - 3}")] for i in range(-12, 15)
    ])


bots = {}
admin_gspread_link = "https://docs.google.com/spreadsheets/d/1UxPtaJDXWsxtd5EpICIFIe0m_lu5wSt5FPNWPR3Gmgk/edit?usp=sharing"
with open("client_secret.json") as f:
    s = load(f)
    GSPREAD_ACCOUNT_EMAIL = s["client_email"]


def check_task_active(bot_id, uid, job_id):
    with open("dumpp.json") as f:
        user_data = load(f)
        #print(job_id in user_data[bot_id][uid] and user_data[bot_id][uid][job_id]["state"] == "running")
        return job_id in user_data[bot_id][uid] and user_data[bot_id][uid][job_id]["state"] == "running"


def send_msg(bot_id, cid, msg, uid):
    print("alivv")
    with open("request.log") as f:
        s = load(f)
        s["requests_sent"].append(str(datetime.now()))
        if uid not in s["requests_sent_usr"]:
            s["requests_sent_usr"][uid] = []
        s["requests_sent_usr"][uid].append(str(datetime.now()))
        dump(s, open("request.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    bots[bot_id].send_message(cid, msg)


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    query.answer(ok=True)


def successful_payment_callback(update, context):
    update.message.reply_text("Thank you for your payment!")


def sender(bot, job_data, bot_id, uid, lang):
    print("alive!")
    if datetime.strptime(job_data["date"], '%Y-%m-%d') <= datetime.now() and check_task_active(bot_id, uid, job_data["id"]):
        if datetime.strptime(job_data["end_date"], '%Y-%m-%d') < datetime.now():
            return schedule.CancelJob
        if job_data["state"] == "pending":
            return 1
        pprint(job_data)
        d = {
            "each_days": 1,
            "two_days": 2,
            "three_days": 3,
            "four_days": 4,
            "five_days": 5,
            "six_days": 6,
            "seven_days": 7,
            "out_days": -1,
            "busy_days": -1,
            "custom_week_days": -1,
            "month_end_days": -1,
            "custom_days": -1
        }
        if d[job_data['frequency']] != -1:
            if abs(datetime.strptime(job_data["date"], '%Y-%m-%d').day - date.today().day) % d[job_data['frequency']] == 0:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        elif job_data['frequency'] == "out_days":
            if datetime.now().weekday() in [6, 7]:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        elif job_data['frequency'] == "busy_days":
            if datetime.now().weekday() < 6:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        elif job_data['frequency'] == "custom_week_days":
            d = {
                "mo_week": 1,
                "tu_week": 2,
                "we_week": 3,
                "th_week": 4,
                "fr_week": 5,
                "sa_week": 6,
                "su_week": 7
            }
            if datetime.now().weekday() + 1 in [d[i] for i in job_data['selected_week']]:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        elif job_data['frequency'] == "month_end_days":
            r = datetime.now()
            if r.day == monthrange(r.year, r.month)[1]:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        elif job_data['frequency'] == "custom_days":
            if str(datetime.now().day) in job_data["selected_days"]:
                send_msg(bot_id, job_data["chat_id"], job_data["desc"], uid)
        print("al2")


def get_link(currency, uid, price):
    return f"https://qiwi.com/payment/form/99?amountFraction=0.0&currency={currency}&extra['account']=79258550898&extra['comment']={uid + '+' + '+'.join(str(datetime.now()).split())}&amountInteger={price}"


def create_message(bot, job_data, bot_id, uid, lang, from_main=False):
    print("set go")
    pprint(job_data)
    with open("dumpp.json") as f:
        s = load(f)
        job_data["selected_hr"] = str(int(job_data["selected_hr"]) + s[uid]["timezone"])
    minute = ":" + (job_data["selected_min"] if len(job_data["selected_min"]) == 2 else '0' + job_data["selected_min"])
    schedule.every().day.at(("" if len(job_data["selected_hr"]) == 2 else '0') + job_data["selected_hr"] + minute).do(sender, bot, job_data, bot_id, uid, lang).tag(bot_id + "::" + uid + "::" + job_data["id"])
    if not from_main:
        with open("request.log") as f:
            s = load(f)
            s["requests_created"].append(str(datetime.now()))
            s["requests_created_usr"][uid] = s["requests_created_usr"].get(uid, []) + [str(datetime.now())]
        dump(s, open("request.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    with open("request.log") as f:
        s = load(f)
        #pprint(s)
    print("task created successfully")
    print(schedule.jobs)


def delete_task(bot_id, uid, job_id):
    schedule.clear(bot_id + "::" + uid + "::" + job_id)


def commit(update, context, type):
    bot_id = str(context.bot.id)
    user_data = {**load_db(), **context.user_data}
    with open("payments.log") as f:
        s = load(f)
        if "payments" not in s:
            s["payments"] = []
            dump(s, open('payments.log', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)
    if "stats" not in user_data:
        user_data["stats"] = {
            "admin": {
                "users_count": 0,
                "checkout_count": 0,
                "promocode_usage_count": 0,
                "tasks_created_day": 0,
                "tasks_sent_day": 0,
            }
        }
    if bot_id not in user_data:
        user_data[bot_id] = {"owner": "", "chat_list": {}}
    if type == "message" or type == "command":
        uid = str(update.message.from_user.id)
        if uid not in user_data[bot_id]:
            user_data[bot_id][uid] = {"id": 0, "state": "pending", "subscription_end": str(datetime.now()).split()[0], "lang": "ru", "referrer": "", "referrals": {}, "task_bot": admin_id}
        if uid not in user_data:
            user_data[uid] = {"bot_list": [], "state": "pending", "sheet": "", "date_registered": str(date.today()), "promocodes": [], "checkouts_count": 0, "checkouts_sum": {"EUR": 0, "RUB": 0, "USD": 0}, "timezone": 0}
        if not user_data[bot_id]["owner"]:
            user_data[bot_id]["owner"] = uid
            user_data[uid]["bot_list"] = list(set(user_data[uid]["bot_list"] + [bot_id]))
    elif type == "callback":
        uid = str(update.callback_query.from_user.id)
        if uid not in user_data[bot_id]:
            user_data[bot_id][uid] = {"id": 0, "state": "pending", "subscription_end": str(datetime.now()).split()[0], "lang": "ru", "referrer": "", "referrals": {}, "task_bot": admin_id}
        if uid not in user_data:
            user_data[uid] = {"bot_list": [], "state": "pending", "sheet": "", "date_registered": str(date.today()), "promocodes": [], "checkouts_count": 0, "checkouts_sum": {"EUR": 0, "RUB": 0, "USD": 0}, "timezone": 0}
        if not user_data[bot_id]["owner"]:
            user_data[bot_id]["owner"] = uid
            user_data[uid]["bot_list"] = list(set(user_data[uid]["bot_list"] + [bot_id]))
    elif type == "query":
        uid = str(update.inline_query.from_user.id)
        if uid not in user_data[bot_id]:
            user_data[bot_id][uid] = {"id": 0, "state": "pending", "subscription_end": str(datetime.now()).split()[0], "lang": "ru", "referrer": "", "referrals": {}, "task_bot": admin_id}
        if uid not in user_data:
            user_data[uid] = {"bot_list": [], "state": "pending", "sheet": "", "date_registered": str(date.today()), "promocodes": [], "checkouts_count": 0, "checkouts_sum": {"EUR": 0, "RUB": 0, "USD": 0}, "timezone": 0}
        if not user_data[bot_id]["owner"]:
            user_data[bot_id]["owner"] = uid
            user_data[uid]["bot_list"] = list(set(user_data[uid]["bot_list"] + [bot_id]))
    if uid not in user_data["stats"]:
        user_data["stats"][uid] = {
            "requests_created": 0,
            "requests_sent": 0,
        }
    context.user_data = user_data
    with open("users.json") as f:
        s = load(f)
        if context.bot.get_chat(uid).username not in s:
            s[context.bot.get_chat(uid).username] = uid
            notify(context.bot, uid)
            dump(s, open("users.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    with open("muted_chats.json") as f:
        #print(1)
        s = load(f)
        #print(s)
        #print(2)
        if uid not in s:
            s[uid] = {}
            dump(s, open('muted_chats.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)
    with open("request.log") as f:
        s = load(f)
        if not s:
            s = {
                "requests_created": [],
                "requests_sent": [],
                "requests_created_usr": {},
                "requests_sent_usr": {},
            }
            dump(s, open('request.log', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)
    dump_db(user_data)
    return user_data


def check_payment_notify(bot, uid):
    with open("dumpp.json") as f:
        s = load(f)
        if s[admin_id][uid]["subscription_end"] == -1:
            return schedule.CancelJob
        date_end = datetime.strptime(s[admin_id][uid]["subscription_end"], '%Y-%m-%d')
        lang = s[admin_id][uid]["lang"]
    days = (datetime.today() - date_end).days
    if days < -2:
        return
    elif days <= 0:
        if lang == "ru":
            bot.send_message(uid,
                             "Ваша подписка очень скоро закончится. Продлите её, чтобы продолжать получать автоматизированные уведомления от своих сотрудников!",
                             reply_markup=InlineKeyboardMarkup([[
                                 InlineKeyboardButton("🏡", callback_data="::home::")
                             ]]))
        else:
            bot.send_message(uid,
                             "Your subcription will end shortly. Purchase it to continue receiving automated feedback from your employees!",
                             reply_markup=InlineKeyboardMarkup([[
                                 InlineKeyboardButton("🏡", callback_data="::home::")
                             ]]))
    else:
        if datetime.today().day in [15, 30]:
            if lang == "ru":
                bot.send_message(uid, "Ваша подписка закончилась. Продлите её, чтобы продолжать получать автоматизированные уведомления от своих сотрудников!", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            else:
                bot.send_message(uid,
                                 "Your subcription is over. Purchase it to continue receiving automated feedback from your employees!",
                                 reply_markup=InlineKeyboardMarkup([[
                                     InlineKeyboardButton("🏡", callback_data="::home::")
                                 ]]))


def notify(bot, uid):
    schedule.every().day.do(check_payment_notify, bot, uid)


TOKEN ="202011111:AAHOPgcC_ZRHewrM3SYUX2loKMS9M7urUSk"
admin_id = TOKEN.split(":")[0]
admin_user_id = ["640028321", "106052"]
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logger = logging.getLogger(__name__)


def load_db():
    with open('dumpp.json', 'r+', encoding='utf-8') as f:
        return load(f)


def dump_db(context):
    dump(context, open('dumpp.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def start(update, context):
    context.user_data = commit(update, context, "command")
    uid = str(update.message.from_user.id)
    bot_id = str(context.bot.id)
    if len(context.user_data[uid]["bot_list"]) > 0:
        update.message.reply_text(get_translation("Вы уже зарегистрированы!:)", context.user_data[admin_id][uid]["lang"]), reply_markup=get_menu(context.user_data[admin_id][uid]["lang"], uid in admin_user_id, uid == context.user_data[bot_id]["owner"]))
    else:
        update.message.reply_text('Hi!', reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🇺🇸🇪🇺", callback_data="start::en"),
            InlineKeyboardButton("🇷🇺", callback_data="start::ru")
        ]]))
    context.user_data = commit(update, context, "command")


def help(update, context):
    context.user_data = commit(update, context, "command")
    lang = context.user_data[admin_id][str(update.message.from_user.id)]["lang"]
    update.message.reply_text(get_help(lang))


def get_freq_text(job_data, lang):
    d = {
        "each_days": ["Каждый день", "Each day"],
        "two_days": ["Каждые два дня", "Each two days"],
        "three_days": ["Каждые три дня", "Each three days"],
        "four_days": ["Каждые четыре дня", "Each four days"],
        "five_days": ["Каждые пять дней", "Each five days"],
        "six_days": ["Каждые шесть дней", "Each six days"],
        "seven_days": ["Каждые семь дней", "Each seven days"],
        "out_days": ["Выходные", "Each seven days", -1],
        "busy_days": ["Будни", "Each seven days", -1],
        "custom_week_days": ["Выбранные дни в неделе", "Selected days in the week", -1],
        "month_end_days": ["Конец каждого месяца", "End of each month", -1],
        "custom_days": ["Выбранные дни в месяце", "Selected days in the month", -1]
    }
    if len(d[job_data['frequency']]) == 2 or job_data['frequency'] in ["month_end_days", "out_days", "busy_days"]:
        return f"{'Частота' if lang == 'ru' else 'Frequency'}: {d[job_data['frequency']][0 if lang == 'ru' else 1]}"
    elif job_data['frequency'] == "custom_week_days":
        r = {
            "mo_week": ["Понедельник", "Monday"],
            "tu_week": ["Вторник", "Tuesday"],
            "we_week": ["Среда", "Wednesday"],
            "th_week": ["Четверг", "Thursday"],
            "fr_week": ["Пятница", "Friday"],
            "sa_week": ["Суббота", "Saturday"],
            "su_week": ["Воскресенье", "Sunday"]
        }
        st = []
        for i in job_data['selected_week']:
            st.append(r[i][0 if lang == 'ru' else 1])
        return f"{'Частота' if lang == 'ru' else 'Frequency'}: {d[job_data['frequency']][0 if lang == 'ru' else 1]}\n{'Выбранные дни' if lang == 'ru' else 'Selected days'}: {', '.join(st)}"
    elif job_data['frequency'] == "custom_days":
        return f"{'Частота' if lang == 'ru' else 'Frequency'}: {d[job_data['frequency']][0 if lang == 'ru' else 1]}\n{'Выбранные дни' if lang == 'ru' else 'Selected days'}: {', '.join(job_data['selected_days'])}"


def to_text(job_data, lang, bot_id):
    if lang == "ru":
        return f"Чат: {bots[bot_id].get_chat(job_data['chat_id']).title}\nСостояние: {'Работает' if job_data['state'] == 'running' else 'приостановлено'}\nСообщение: {job_data['desc']}\nДата начала работы: {job_data['date']}\n{get_freq_text(job_data, lang)}\nВремя рассылок: {('0' if len(job_data['selected_hr']) == 1 else '') + job_data['selected_hr'] + ':' + ('0' if len(job_data['selected_min']) == 1 else '') + job_data['selected_min']}\nДата завершения: {job_data['end_date']}"
    return f"Chat: {bots[bot_id].get_chat(job_data['chat_id']).title}\nState: {'Running' if job_data['state'] == 'running' else 'Paused'}\nMessage: {job_data['desc']}\nDate of start: {job_data['date']}\n{get_freq_text(job_data, lang)}\nMailing time: {('0' if len(job_data['selected_hr']) == 1 else '') + job_data['selected_hr'] + ':' + ('0' if len(job_data['selected_min']) == 1 else '') + job_data['selected_min']}\nDate of end: {job_data['end_date']}"


def error(update, context):
    pass
    #logger.warning('Update "%s" caused error "%s"', update, error)


def new_chat(update, context):
    context.user_data = commit(update, context, "message")
    uid = str(update.message.from_user.id)
    bot_id = str(context.bot.id)
    lang = context.user_data[admin_id][uid]["lang"]
    if str(update.message.new_chat_members[0].id) == bot_id:
        context.user_data[bot_id]["chat_list"][update.message.chat_id] = {
            'title': update.message.chat.title
        }
        ##pprint(context.user_data[bot_id][uid])
        with open("muted_chats.json") as f:
            s = load(f)
            s[context.user_data[bot_id]["owner"]] = {**s[context.user_data[bot_id]["owner"]], **{str(update.message.chat_id): {'title': update.message.chat.title, 'muted': 0}}}
            dump(s, open('muted_chats.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)
    context.user_data = commit(update, context, "message")


def check_subscription(update, context, type):
    if type == "message" or type == "command":
        uid = str(update.message.from_user.id)
    elif type == "callback":
        uid = str(update.callback_query.from_user.id)
    elif type == "query":
        uid = str(update.inline_query.from_user.id)
    return context.user_data[admin_id][uid]["subscription_end"] == -1 or datetime.strptime(context.user_data[admin_id][uid]["subscription_end"], '%Y-%m-%d') >= datetime.now()


def get_menu(lang, is_admin=False, is_local=False):
    keyboard = [
        [InlineKeyboardButton(get_translation("Добавить задачу📝", lang), callback_data="menu::add_task")],
        [InlineKeyboardButton(get_translation("Таблица📈", lang), callback_data="menu::gtable")],
        [InlineKeyboardButton(get_translation("Настройка уведомлений из чатов💬", lang), callback_data="menu::chat_push")],
        [InlineKeyboardButton(get_translation("Мои боты🤖", lang), callback_data="menu::my_bots")],
        [InlineKeyboardButton(get_translation("Оплата💸", lang), callback_data="menu::buy")],
        [InlineKeyboardButton(get_translation("Ещё", lang), callback_data="menu::more")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton(get_translation("АДМИНИСТРАТОРСКАЯ ПАНЕЛЬ", lang), callback_data="menu::admin_panel")])
    return InlineKeyboardMarkup(keyboard)


def menu(update, context):
    context.user_data = commit(update, context, "message")
    lang = context.user_data[admin_id][str(update.message.from_user.id)]["lang"]
    update.message.reply_text(get_menu_text(update, context, str(update.message.from_user.id), admin_id, lang), reply_markup=get_menu(lang, str(update.message.chat_id) in admin_user_id))


def update_admin_stats(update=0, context=0, type=0, data=0):
    if type == 0:
        with open("request.log") as f:
            s = load(f)
            requests_created = []
            requests_sent = []
            context.user_data["stats"]["admin"]["tasks_created_day"] = 0
            context.user_data["stats"]["admin"]["tasks_sent_day"] = 0
            context.user_data["stats"]["admin"]["users_count"] = sum([1 for i in context.user_data[admin_id] if i.isdigit()])
            for i in s["requests_created"]:
                if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=1) >= datetime.now():
                    context.user_data["stats"]["admin"]["tasks_created_day"] += 1
                    requests_created.append(i)
            s["requests_created"] = requests_created
            for i in s["requests_sent"]:
                if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=1) >= datetime.now():
                    context.user_data["stats"]["admin"]["tasks_sent_day"] += 1
                    requests_sent.append(i)
            s["requests_sent"] = requests_sent
        dump(s, open("request.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
        return context.user_data
    elif type == 1:
        with open("request.log") as f:
            s = load(f)
            requests_created = []
            requests_sent = []
            data["stats"]["admin"]["tasks_created_day"] = 0
            data["stats"]["admin"]["tasks_sent_day"] = 0
            data["stats"]["admin"]["users_count"] = sum([1 for i in data[admin_id] if i.isdigit()])
            for i in s["requests_created"]:
                if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=1) >= datetime.now():
                    data["stats"]["admin"]["tasks_created_day"] += 1
                    requests_created.append(i)
            s["requests_created"] = requests_created
            for i in s["requests_sent"]:
                if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=1) >= datetime.now():
                    data["stats"]["admin"]["tasks_sent_day"] += 1
                    requests_sent.append(i)
            s["requests_sent"] = requests_sent
            dump(s, open("request.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
            requests_created_usr = {}
            requests_sent_usr = {}
            for uid in s["requests_created_usr"]:
                requests_created_usr[uid] = []
                for i in s["requests_created_usr"][uid]:
                    if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + relativedelta(months=1) >= datetime.now():
                        requests_created_usr[uid].append(i)
            s["requests_created_usr"] = requests_created_usr
            for uid in s["requests_sent_usr"]:
                requests_sent_usr[uid] = []
                for i in s["requests_sent_usr"][uid]:
                    if datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f') + relativedelta(months=1) >= datetime.now():
                        requests_sent_usr[uid].append(i)
            s["requests_sent_usr"] = requests_sent_usr
            for uid in s["requests_created_usr"]:
                data["stats"][uid]["requests_created"] = len(s["requests_created_usr"][uid])
            for uid in s["requests_sent_usr"]:
                data["stats"][uid]["requests_sent"] = len(s["requests_sent_usr"][uid])
        dump(s, open("request.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
        #print("success")
        return data


def check_payments():
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 5dfbbde1e4636936c7786ad1553d58d1',
    }

    params = (
        ('rows', '50'),
        ("operations", "IN")
    )

    response = requests.get('https://edge.qiwi.com/payment-history/v2/persons/79258550898/payments', headers=headers,
                            params=params).json()
    for i in response["data"]:
        if i["status"] == "SUCCESS" and i["comment"]:
            comment = i["comment"].split()
            if len(comment) == 3 and comment[0].isdigit():
                with open("payments.log") as f:
                    s = load(f)
                    if "payments" not in s:
                        s["payments"] = []
                    if ' '.join(comment) not in s["payments"]:
                        s["payments"].append(' '.join(comment))
                        uid, date, time = comment
                        with open("dumpp.json") as f:
                            k = load(f)
                            if uid not in k:
                                continue
                        print(i["total"]["currency"])
                        currency = {
                            643: "RUB"
                        }[i["total"]["currency"]]
                        amt = i["total"]["amount"]
                        print(currency, amt)
                        if currency == "RUB":
                            print(1)
                            plan = {
                                290: "1months",
                                740: "3months",
                                1392: "6months",
                                2436: "12months",
                                4500: "-1"
                            }
                            sums = [290, 740, 1392, 2436, 4500, -1]
                            if amt < 290:
                                print(2)
                                continue
                            while amt >= 290:
                                for i in range(len(sums) - 1):
                                    if sums[i + 1] > amt or sums[i + 1] == -1:
                                        break
                                print(sums[i])
                                p = plan[sums[i]]
                                print(p)
                                verify_payment(uid, p, currency, amt)
                                amt -= sums[i]
                        elif currency == "EUR":
                            plan = {
                                8.9: "1months",
                                22.7: "3months",
                                42.7: "6months",
                                74.8: "12months",
                                135: "-1"
                            }
                            sums = [8.9, 22.7, 42.7, 74.8, 135, -1]
                            if amt < 8.9:
                                continue
                            while amt >= 8.9:
                                for i in range(len(sums) - 1):
                                    if sums[i + 1] > amt or sums[i + 1] == -1:
                                        break
                                print(sums[i])
                                p = plan[sums[i]]
                                print(p)
                                verify_payment(uid, p, currency, amt)
                                amt -= sums[i]
                        elif currency == "USD":
                            plan = {
                                9.90: "1months",
                                25.25: "3months",
                                47.52: "6months",
                                83.16: "12months",
                                155: "-1"
                            }
                            sums = [9.90, 25.25, 47.52, 83.16, 155, -1]
                            if amt < 9.90:
                                continue
                            while amt >= 9.90:
                                for i in range(len(sums) - 1):
                                    if sums[i + 1] > amt or sums[i + 1] == -1:
                                        break
                                print(sums[i])
                                p = plan[sums[i]]
                                print(p)
                                verify_payment(uid, p, currency, amt)
                                amt -= sums[i]
                dump(s, open("payments.log", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    #pprint(response)


def verify_payment(uid, plan, currency, amt):
    print(3)
    print(uid, plan, currency, amt)
    d = {
        "1months": relativedelta(months=1),
        "3months": relativedelta(months=3),
        "6months": relativedelta(months=6),
        "12months": relativedelta(months=12),
         "-1": -1,
    }
    with open("dumpp.json") as f:
        s = load(f)
        if s[admin_id][uid]["referrer"]:
            rfid = s[admin_id][uid]["referrer"]
            if s[admin_id][rfid]["subscription_end"] != -1:
                s[admin_id][rfid]["subscription_end"] = str(datetime.strptime(s[admin_id][rfid]["subscription_end"], '%Y-%m-%d') + relativedelta(months=1)).split()[0]
            if s[admin_id][uid]["subscription_end"] != -1:
                s[admin_id][uid]["subscription_end"] = str(datetime.strptime(s[admin_id][uid]["subscription_end"], '%Y-%m-%d') + relativedelta(months=1)).split()[0]
            s[admin_id][rfid]["referrals"][uid]["payment_date"] = str(date.today())
        if d[plan] == -1:
            s[admin_id][uid]["subscription_end"] = -1
        else:
            if s[admin_id][uid]["subscription_end"] != -1:
                s[admin_id][uid]["subscription_end"] = str(datetime.strptime(s[admin_id][uid]["subscription_end"], '%Y-%m-%d') + d[plan]).split()[0]
        #print(s[admin_id][uid]["subscription_end"])
        s[uid]["checkouts_count"] += 1
        s[uid]["checkouts_sum"][currency] += amt
        s["stats"]["admin"]["checkout_count"] += 1
    dump(s, open("dumpp.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)



def button(update, context):
    try:
        context.user_data = commit(update, context, "callback")
        uid = str(update.callback_query.from_user.id)
        bot_id = str(context.bot.id)
        data = update.callback_query.data
        lang = context.user_data[admin_id][uid]["lang"]
        bot_idd = context.user_data[admin_id][uid]["task_bot"]
        if data.startswith("mute_toggle::"):
            cid = data.strip("mute_toggle::")
            with open("muted_chats.json") as f:
                s = load(f)
                s[uid][cid]["muted"] = (s[uid][cid]["muted"] + 1) % 2
                if not s[uid]:
                    update.callback_query.edit_message_text(
                        get_translation("Чатов пока нет. Добавляйте своих ботов в чаты, чтобы настраивать уведомления",
                                        lang),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙", callback_data="back::start"),
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ]]))
                else:
                    a = [[InlineKeyboardButton("🔙", callback_data="back::start"),
                          InlineKeyboardButton("🏡", callback_data="::home::")]]
                    for i in s[uid]:
                        a.append([InlineKeyboardButton(s[uid][i]["title"] + (" 🔇" if s[uid][i]["muted"] else " 🔊"),
                                                       callback_data=f"mute_toggle::{i}")])
                    update.callback_query.edit_message_text(get_translation("Ваши чаты", lang),
                                                            reply_markup=InlineKeyboardMarkup(a))
            dump(s, open('muted_chats.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)
        elif data == "gpread::admin::change":
            context.user_data[uid]["state"] = "admin::gtable"
            update.callback_query.edit_message_text(f"Введите ссылку на новую администраторскую таблицу. Не забудьте открыть доступ {GSPREAD_ACCOUNT_EMAIL} на редактирование⚠️",
                                                    reply_markup=InlineKeyboardMarkup([[
                                                        InlineKeyboardButton("🔙", callback_data="admin::gtable"),
                                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                                    ]]))
        elif data == "gtable::change":
            context.user_data[uid]["state"] = "gtable"
            update.callback_query.edit_message_text(get_translation("Введите ссылку на Вашу таблицу. Не забудьте открыть доступ ", lang) + GSPREAD_ACCOUNT_EMAIL + get_translation(" на редактирование⚠️", lang),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙", callback_data="back::to_gtable"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]))
        elif data.startswith("admin::"):
            if data == "admin::gtable":
                update.callback_query.edit_message_text(f"(Ссылка){admin_gspread_link}",
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                                                            InlineKeyboardButton("Поменять таблицу", callback_data="gpread::admin::change"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]))
            elif data == "admin::post":
                keyboard = [[InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                            InlineKeyboardButton("🏡", callback_data="::home::")],
                            [InlineKeyboardButton("Все", callback_data="send_message::all")]]
                for i in context.user_data[admin_id]:
                    if i.isdigit():
                        c = bots[admin_id].get_chat(i)
                        p = c.username if c.username else "hidden"
                        if c.first_name:
                            p += '\n' + (c.first_name if c.first_name else "hidden")
                        keyboard.append([InlineKeyboardButton(p, callback_data="send_message::" + i)])
                update.callback_query.edit_message_text(get_translation('Выберите чат:', lang),
                                          reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "admin::create_promocode":
                keyboard = [[InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                             InlineKeyboardButton("🏡", callback_data="::home::")],
                            [InlineKeyboardButton("Список промокодов", callback_data="promocode::list")],
                            [InlineKeyboardButton("Неделя", callback_data="promocode::1weeks")],
                            [InlineKeyboardButton("2 недели", callback_data="promocode::2weeks")],
                            [InlineKeyboardButton("Месяц", callback_data="promocode::1months")],
                            [InlineKeyboardButton("2 месяца", callback_data="promocode::2months")],
                            [InlineKeyboardButton("3 месяца", callback_data="promocode::3months")],
                            ]
                update.callback_query.edit_message_text("Промокоды", reply_markup=InlineKeyboardMarkup(keyboard))
        elif data.startswith("promocode::"):
            if data == "promocode::list":
                a = []
                with open("promocodes.json") as f:
                    s = load(f)
                    t = {
                        '1weeks': '1 неделя',
                        '2weeks': '2 недели',
                        '1months': '1 месяц',
                        '2months': '2 месяца',
                        '3months': '3 месяца'
                    }
                    for i in s:
                        a.append((f"{i}\nДлительность: {t[s[i]['duration']]}\nАктивирован раз: {s[i]['activated']}\nСрок годности: {s[i]['expiration_date']}", i))
                if not a:
                    update.callback_query.edit_message_text("Промокодов пока нет",
                                                            reply_markup=InlineKeyboardMarkup([[
                                                                InlineKeyboardButton("🔙", callback_data="back::to_promocodes"),
                                                                InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ]]))
                else:
                    update.callback_query.edit_message_text("Ваши промокоды",
                                                            reply_markup=InlineKeyboardMarkup([[
                                                                InlineKeyboardButton("🔙",
                                                                                     callback_data="back::to_promocodes"),
                                                                InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ]]))
                    for i, j in a:
                        context.bot.send_message(uid, i, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Удалить промокод", callback_data=f"promocode::delete::{j}"), InlineKeyboardButton("🏡", callback_data="::home::")]]))
            elif data.startswith("promocode::delete::"):
                j = data.lstrip("promocode::delete::")
                with open("promocodes.json") as f:
                    s = load(f)
                    s.pop(j)
                dump(s, open("promocodes.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
                update.callback_query.edit_message_text("Промокод успешно удалён",
                                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ]]))
            else:
                context.user_data[uid]["state"] = data
                update.callback_query.edit_message_text("Выберите дату, до которой промокод действителен:", reply_markup = telegramcalendar.create_calendar())
        elif data.startswith("start::"):
            #print(data)
            if data in ["start::ru", "start::en"]:
                context.user_data[admin_id][uid]["lang"] = "ru" if data == "start::ru" else "en"
                context.user_data[uid]["state"] = "ref"
                update.callback_query.edit_message_text(get_translation("Привет, начнем же процедуру регистрации твоего первого личного бота. Введи @username человека, который тебя пригласил.\nПосле оплаты вы оба получите приятный бонус", "ru" if data == "start::ru" else "en"), reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_translation("Нет реферера", "ru" if data == "start::ru" else "en"), callback_data="start::no_ref")]
                ]))
            elif data == "start::no_ref":
                update.callback_query.edit_message_text(get_translation("Введите вашу временную зону:", lang), reply_markup=get_tz())
        elif data.startswith("tz::"):
            data = data.strip("tz::")
            context.user_data[uid]["timezone"] = int(data)
            context.user_data[uid]["state"] = "token"
            update.callback_query.edit_message_text(get_token_desc(lang),
                                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ]]))
        elif data == "::home::":
            update.callback_query.edit_message_text(get_menu_text(update, context, uid, admin_id, lang), reply_markup=get_menu(lang, uid in admin_user_id))
        elif data.startswith("back::"):
            #print(data)
            if data in ["back::start", "back::buy", "back::lang", "back::referrer", "back::my_bots", "back::gtable"]:
                update.callback_query.edit_message_text(get_menu_text(update, context, uid, admin_id, lang), reply_markup=get_menu(lang, uid in admin_user_id))
            elif data == "back::currency":
                update.callback_query.edit_message_text(
                    get_translation("Премиум доступ", lang) + "\n" + get_buy_text(lang),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙", callback_data="back::lang"),
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ], [InlineKeyboardButton("₽", callback_data="RUB::currency")],
                        [InlineKeyboardButton("💶", callback_data="EUR::currency")],
                        [InlineKeyboardButton("💲", callback_data="USD::currency")]]))
            elif data in ["back::promocode", "back::referral", "back::help"]:
                update.callback_query.edit_message_text(text=get_translation("Главное меню", lang),
                                                        reply_markup=InlineKeyboardMarkup([
                                                            [InlineKeyboardButton("🔙",
                                                                callback_data="menu::less")],
                                                            [InlineKeyboardButton(
                                                                get_translation("Активировать промокод🎁", lang),
                                                                callback_data="menu::promocode")],
                                                            [InlineKeyboardButton(
                                                                get_translation("Мои рефералы📣", lang),
                                                                callback_data="menu::my_referrals")],
                                                            [InlineKeyboardButton(
                                                                get_translation("Сменить язык🎌", lang),
                                                                callback_data="menu::lang")],
                                                            [InlineKeyboardButton(get_translation("Справка📖", lang),
                                                                                  callback_data="menu::help")]]))
            elif data == "back::to_gtable":
                context.user_data[uid]["state"] = "pending"
                if context.user_data[uid]["sheet"]:
                    update.callback_query.edit_message_text(get_translation("Ваша таблица: ", lang) + f"[{get_translation('Ссылка', lang)}]({context.user_data[uid]['sheet']})\n{get_translation('Не забудьте открыть доступ ')}{GSPREAD_ACCOUNT_EMAIL}",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data=f"back::gtable"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ], [InlineKeyboardButton(get_translation("Привязать другую", lang), callback_data="gtable::change")]]), parse_mode=ParseMode.MARKDOWN)
                else:
                    update.callback_query.edit_message_text(
                        get_translation("У вас пока нет действующей таблицы (spreadsheets.google.com). Привяжите её, чтобы начать получать ответы сотрудников.", lang) + context.user_data[uid]["sheet"],
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙", callback_data=f"back::gtable"),
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ], [InlineKeyboardButton(get_translation("Привязать таблицу", lang),
                                                 callback_data="gtable::change")]]))
            elif data == "back::to_promocodes":
                keyboard = [[InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                             InlineKeyboardButton("🏡", callback_data="::home::")],
                            [InlineKeyboardButton("Список промокодов", callback_data="promocode::list")],
                            [InlineKeyboardButton("Неделя", callback_data="promocode::1weeks")],
                            [InlineKeyboardButton("2 недели", callback_data="promocode::2weeks")],
                            [InlineKeyboardButton("Месяц", callback_data="promocode::1months")],
                            [InlineKeyboardButton("2 месяца", callback_data="promocode::2months")],
                            [InlineKeyboardButton("3 месяца", callback_data="promocode::3months")],
                            ]
                update.callback_query.edit_message_text("Промокоды", reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "back::to_admin":
                context.user_data = update_admin_stats(update, context, 0)
                update.callback_query.edit_message_text(get_admin_stats(context.user_data["stats"]["admin"], lang),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙", callback_data="back::start"),
                                                            InlineKeyboardButton("🎁", callback_data="admin::create_promocode"),
                                                            InlineKeyboardButton("📝", callback_data="admin::gtable"),
                                                            InlineKeyboardButton("📢", callback_data="admin::post"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]))
            elif data == "back::send_message":
                keyboard = [[InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                             InlineKeyboardButton("🏡", callback_data="::home::")],
                            [InlineKeyboardButton("Все", callback_data="send_message::all")]]
                for i in context.user_data[admin_id]:
                    if i.isdigit():
                        c = bots[admin_id].get_chat(i)
                        p = c.username
                        if c.first_name:
                            p += '\n' + c.first_name
                        keyboard.append([InlineKeyboardButton(p, callback_data="send_message::" + i)])
                update.callback_query.edit_message_text(get_translation('Выберите чат:', lang),
                                          reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "back::add_task":
                update.callback_query.edit_message_text(get_menu_text(update, context, uid, admin_id, lang), reply_markup=get_menu(lang, uid in admin_user_id))
            elif data == "back::add_task::confirm":
                keyboard = [
                    [InlineKeyboardButton("🔙", callback_data="back::add_task"),
                     InlineKeyboardButton("🏡", callback_data="::home::")]
                ]
                for i in context.user_data[uid]["bot_list"]:
                    if i == admin_id:
                        continue
                    c = bots[i]
                    keyboard.append(
                        [InlineKeyboardButton(f"{c.first_name} (@{c.username})", callback_data=f"add_task::{i}")])
                keyboard.append([InlineKeyboardButton(get_translation("Добавить бота", lang),
                                                      callback_data="menu::add_bot::from_task")])
                update.callback_query.edit_message_text(get_translation("Выберите бота", lang),
                                                        reply_markup=InlineKeyboardMarkup(keyboard))
            elif data.startswith("back::add_bot"):
                from_action = data.lstrip("back::add_bot::")
                #print(from_action)
                if from_action == "from_my_bots":
                    a = [[InlineKeyboardButton("🔙", callback_data="back::my_bots"),
                          InlineKeyboardButton("🏡", callback_data="::home::")]]
                    for i in context.user_data[uid]["bot_list"]:
                        if i == admin_id:
                            continue
                        data = bots[i]
                        a.append([InlineKeyboardButton(f"{data.first_name} @{data.username}", callback_data=f"menu::messages::{i}")])
                    a.append([InlineKeyboardButton(get_translation("Добавить бота", lang),
                                                   callback_data="menu::add_bot::from_bots")])
                    if len(a) == 2:
                        update.callback_query.edit_message_text(get_translation("Ботов пока нет", lang),
                                                                reply_markup=InlineKeyboardMarkup(a))
                    else:
                        update.callback_query.edit_message_text(get_translation("Ваши боты", lang),
                                                                reply_markup=InlineKeyboardMarkup(a))
                elif from_action == "from_task":
                    keyboard = [
                        [InlineKeyboardButton("🔙", callback_data="back::add_task"),
                         InlineKeyboardButton("🏡", callback_data="::home::")]
                    ]
                    for i in context.user_data[uid]["bot_list"]:
                        if i == admin_id:
                            continue
                        c = bots[i]
                        keyboard.append(
                            [InlineKeyboardButton(f"{c.first_name} (@{c.username})", callback_data=f"add_task::{i}")])
                    keyboard.append([InlineKeyboardButton(get_translation("Добавить бота", lang),
                                                          callback_data="menu::add_bot::from_task")])
                    update.callback_query.edit_message_text(get_translation("Выберите бота", lang),
                                                            reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "back::message":
                #print(data)
                keyboard = [
                    [InlineKeyboardButton("🔙", callback_data="back::add_task"),
                     InlineKeyboardButton("🏡", callback_data="::home::")]
                ]
                for i in context.user_data[uid]["bot_list"]:
                    if i == admin_id:
                        continue
                    c = bots[i]
                    keyboard.append(
                        [InlineKeyboardButton(f"{c.first_name} (@{c.username})", callback_data=f"add_task::{i}")])
                keyboard.append([InlineKeyboardButton(get_translation("Добавить бота", lang),
                                                      callback_data="menu::add_bot::from_task")])
                update.callback_query.edit_message_text(get_translation("Выберите бота", lang),
                                                        reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "back::messages":
                a = [[InlineKeyboardButton("🔙", callback_data="back::my_bots"),
                      InlineKeyboardButton("🏡", callback_data="::home::")]]
                for i in context.user_data[uid]["bot_list"]:
                    if i == admin_id:
                        continue
                    data = bots[i]
                    a.append([InlineKeyboardButton(f"{data.first_name} @{data.username}", callback_data=f"menu::messages::{i}")])
                a.append([InlineKeyboardButton(get_translation("Добавить бота", lang),
                                               callback_data="menu::add_bot::from_bots")])
                if len(a) == 2:
                    update.callback_query.edit_message_text(get_translation("Ботов пока нет", lang),
                                                            reply_markup=InlineKeyboardMarkup(a))
                else:
                    update.callback_query.edit_message_text(get_translation("Ваши боты", lang),
                                                            reply_markup=InlineKeyboardMarkup(a))
            elif data == "back::lang_successful":
                update.callback_query.edit_message_text(get_translation("Выберите язык", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::lang"),
                    InlineKeyboardButton("🇺🇸🇪🇺", callback_data="lang::en"),
                    InlineKeyboardButton("🇷🇺", callback_data="lang::ru"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            elif data == "back::frequency":
                context.user_data[uid]["state"] = 'date'
                update.callback_query.edit_message_text(get_translation("Выберите дату начала:", lang),
                                          reply_markup=telegramcalendar.create_calendar())
            elif data == "back::text":
                keyboard = [
                    [InlineKeyboardButton("🔙", callback_data="back::add_task"),
                     InlineKeyboardButton("🏡", callback_data="::home::")]
                ]
                for i in context.user_data[bot_idd]["chat_list"]:
                    keyboard.append([InlineKeyboardButton(context.user_data[bot_idd]["chat_list"][i]['title'],
                                                          callback_data="chat_id::" + str(i))])
                if len(keyboard) == 1:
                    update.callback_query.edit_message_text(get_translation('Чатов нет;(\nДобавьте меня хотя бы в один чат:)', lang), reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                update.callback_query.edit_message_text(get_translation('Выберите чат:', lang), reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == "back::start_calendar":
                if context.user_data[uid]["state"].startswith("promocode::"):
                    context.user_data[uid]["state"] = "pending"
                    keyboard = [[InlineKeyboardButton("🔙", callback_data="back::to_admin"),
                                 InlineKeyboardButton("🏡", callback_data="::home::")],
                                [InlineKeyboardButton("Список промокодов", callback_data="promocode::list")],
                                [InlineKeyboardButton("Неделя", callback_data="promocode::1weeks")],
                                [InlineKeyboardButton("2 недели", callback_data="promocode::2weeks")],
                                [InlineKeyboardButton("Месяц", callback_data="promocode::1months")],
                                [InlineKeyboardButton("2 месяца", callback_data="promocode::2months")],
                                [InlineKeyboardButton("3 месяца", callback_data="promocode::3months")],
                                ]
                    update.callback_query.edit_message_text("Промокоды", reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    context.user_data[uid]["state"] = "desc"
                    update.callback_query.edit_message_text(text=get_translation("Введите текст сообщения.", lang),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙", callback_data="back::text"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]))
            elif data == "back::end_calendar":
                context.user_data[uid]["state"] = 'minutes'
                update.callback_query.edit_message_text(text=get_translation("Выберите минуты отправки:", lang),
                                                        reply_markup=time_minutes(lang))
            elif data in ["back::days", "back::week"]:
                context.user_data[uid]["state"] = "frequency"
                update.callback_query.edit_message_text(text=get_translation("Выберите периодичность:", lang), reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙", callback_data="back::frequency")],
                    [InlineKeyboardButton(get_translation('1 день', lang), callback_data="each_days")],
                    [InlineKeyboardButton(get_translation('2 дня', lang), callback_data="two_days")],
                    [InlineKeyboardButton(get_translation('3 дня', lang), callback_data="three_days")],
                    [InlineKeyboardButton(get_translation('4 дня', lang), callback_data="four_days")],
                    [InlineKeyboardButton(get_translation('5 дней', lang), callback_data="five_days")],
                    [InlineKeyboardButton(get_translation('6 дней', lang), callback_data="six_days")],
                    [InlineKeyboardButton(get_translation('7 дней', lang), callback_data="seven_days")],
                    [InlineKeyboardButton(get_translation('Выходные', lang), callback_data="out_days")],
                    [InlineKeyboardButton(get_translation('Будние', lang), callback_data="busy_days")],
                    [InlineKeyboardButton(get_translation('Каждое конкретный день в неделе', lang), callback_data="custom_week_days")],
                    [InlineKeyboardButton(get_translation('Последний день месяца.', lang), callback_data="month_end_days")],
                    [InlineKeyboardButton(get_translation('Каждое конкретное число в месяце', lang), callback_data="custom_days")],
                    [InlineKeyboardButton("🏡", callback_data="::home::")]
                ]))
            elif data == "back::hours":
                if "custom" not in context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]["frequency"]:
                    context.user_data[uid]["state"] = "frequency"
                    update.callback_query.edit_message_text(text=get_translation("Выберите периодичность:", lang), reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙", callback_data="back::frequency")],
                        [InlineKeyboardButton(get_translation('1 день', lang), callback_data="each_days")],
                        [InlineKeyboardButton(get_translation('2 дня', lang), callback_data="two_days")],
                        [InlineKeyboardButton(get_translation('3 дня', lang), callback_data="three_days")],
                        [InlineKeyboardButton(get_translation('4 дня', lang), callback_data="four_days")],
                        [InlineKeyboardButton(get_translation('5 дней', lang), callback_data="five_days")],
                        [InlineKeyboardButton(get_translation('6 дней', lang), callback_data="six_days")],
                        [InlineKeyboardButton(get_translation('7 дней', lang), callback_data="seven_days")],
                        [InlineKeyboardButton(get_translation('Выходные', lang), callback_data="out_days")],
                        [InlineKeyboardButton(get_translation('Будние', lang), callback_data="busy_days")],
                        [InlineKeyboardButton(get_translation('Каждое конкретный день в неделе', lang), callback_data="custom_week_days")],
                        [InlineKeyboardButton(get_translation('Последний день месяца.', lang), callback_data="month_end_days")],
                        [InlineKeyboardButton(get_translation('Каждое конкретное число в месяце', lang), callback_data="custom_days")],
                        [InlineKeyboardButton("🏡", callback_data="::home::")]
                    ]))
                else:
                    if context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]["frequency"] == "custom_week_days":
                        context.user_data[uid]["state"] = "custom_week_days"
                        update.callback_query.edit_message_text(text=get_translation("Выберите дни недели:", lang),
                                                                reply_markup=week(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'], lang))
                    elif context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]["frequency"] == "custom_days":
                        context.user_data[uid]["state"] = "custom_days"
                        update.callback_query.edit_message_text(text=get_translation("Выберите дни месяца:", lang),
                                                                reply_markup=days(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'],
                                                                                  lang))
            elif data == "back::minutes":
                context.user_data[uid]["state"] = 'time'
                update.callback_query.edit_message_text(text=get_translation("Выберите часы отправки:", lang),
                                                        reply_markup=time_hours(lang))
        elif data.startswith("menu::"):
            if data == "menu::more":
                update.callback_query.edit_message_text(text=get_translation("Главное меню", lang),
                                                        reply_markup=InlineKeyboardMarkup([
                                                            [InlineKeyboardButton("🔙",
                                                                callback_data="menu::less")],
                [InlineKeyboardButton(get_translation("Активировать промокод🎁", lang), callback_data="menu::promocode")],
                [InlineKeyboardButton(get_translation("Мои рефералы📣", lang), callback_data="menu::my_referrals")],
                [InlineKeyboardButton(get_translation("Сменить язык🎌", lang), callback_data="menu::lang")],
                [InlineKeyboardButton(get_translation("Справка📖", lang), callback_data="menu::help")]]))
            elif data == "menu::less":
                update.callback_query.edit_message_text(get_menu_text(update, context, uid, admin_id, lang),
                                                        reply_markup=get_menu(lang, uid in admin_user_id))
            if data == "menu::chat_push":
                with open("muted_chats.json") as f:
                    s = load(f)
                    if not s[uid]:
                        update.callback_query.edit_message_text(get_translation("Чатов пока нет. Добавляйте своих ботов в чаты, чтобы настраивать уведомления", lang),
                                                                reply_markup=InlineKeyboardMarkup([[
                                                                    InlineKeyboardButton("🔙", callback_data="back::start"),
                                                                    InlineKeyboardButton("🏡", callback_data="::home::")
                                                                ]]))
                    else:
                        a = [[InlineKeyboardButton("🔙", callback_data="back::start"), InlineKeyboardButton("🏡", callback_data="::home::")]]
                        for i in s[uid]:
                            a.append([InlineKeyboardButton(s[uid][i]["title"] + (" 🔇" if s[uid][i]["muted"] else " 🔊"), callback_data=f"mute_toggle::{i}")])
                        update.callback_query.edit_message_text(get_translation("Ваши чаты", lang),
                                                                reply_markup=InlineKeyboardMarkup(a))
            elif data == "menu::promocode":
                context.user_data[uid]["state"] = "promocode"
                update.callback_query.edit_message_text(get_translation("Введите промокод", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::promocode"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            elif data == "menu::admin_panel":
                context.user_data = update_admin_stats(update, context, 0)
                update.callback_query.edit_message_text(get_admin_stats(context.user_data["stats"]["admin"], lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::start"),
                    InlineKeyboardButton("🎁", callback_data="admin::create_promocode"),
                    InlineKeyboardButton("📝", callback_data="admin::gtable"),
                    InlineKeyboardButton("📢", callback_data="admin::post"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            elif data.startswith("menu::message::"):
                bot_idt = data.strip("menu::message::")
                if bot_idt == admin_id:
                    update.callback_query.edit_message_text(
                        get_translation('Извините, из этого бота можно создавать только других ботов.', lang), reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data="back::message"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                elif context.user_data[bot_idt]["owner"] != uid:
                    update.callback_query.edit_message_text(
                        get_translation("Извините, создавать задачи может только администратор бота.", lang), reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data="back::message"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                else:
                    context.user_data[admin_id][uid]["task_bot"] = bot_idt
                    keyboard = [[
                        InlineKeyboardButton("🔙", callback_data="back::message"),
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ]]
                    for i in context.user_data[bot_idt]["chat_list"]:
                        keyboard.append([InlineKeyboardButton(context.user_data[bot_idt]["chat_list"][i]['title'],
                                                              callback_data="chat_id::" + str(i))])
                    if len(keyboard) == 1:
                        update.callback_query.edit_message_text(
                            get_translation('Чатов нет;(\nДобавьте меня хотя бы в один чат:)', lang),
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data="back::message"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                    else:
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        update.callback_query.edit_message_text(get_translation('Выберите чат:', lang),
                                                                reply_markup=reply_markup)
            elif data.startswith("menu::messages::"):
                bot_idt = data.strip("menu::messages::")
                if uid != context.user_data[bot_idt]["owner"]:
                    update.callback_query.edit_message_text(get_translation('Извините, задачи может смотреть только администратор бота', lang),
                                                                reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data="back::start"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                else:
                    empty = True
                    update.callback_query.edit_message_text(
                        get_translation('Ваши задачи', lang),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙", callback_data="back::messages"),
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ]]))
                    for i in context.user_data[bot_idt][uid]:
                        if i.isdigit():
                            res = to_text(context.user_data[bot_idt][uid][i], lang, bot_idt)
                            if context.user_data[bot_idt][uid][i]["state"] == "running":
                                empty = False
                                context.bot.send_message(uid, res, reply_markup=InlineKeyboardMarkup([[
                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                    ],
                                    [InlineKeyboardButton(get_translation("Приостановить", lang),
                                                          callback_data=f"messages::pause::{bot_idt}::{uid}::{i}"),
                                     InlineKeyboardButton(get_translation("Удалить", lang),
                                                          callback_data=f"messages::delete::{bot_idt}::{uid}::{i}")]
                                ]))
                            elif context.user_data[bot_idt][uid][i]["state"] == "paused":
                                empty = False
                                context.bot.send_message(uid, res, reply_markup=InlineKeyboardMarkup([[
                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                    ],
                                    [InlineKeyboardButton(get_translation("Возобновить", lang),
                                                          callback_data=f"messages::resume::{bot_idt}::{uid}::{i}"),
                                     InlineKeyboardButton(get_translation("Удалить", lang),
                                                          callback_data=f"messages::delete::{bot_idt}::{uid}::{i}")]
                                ]))
                    if empty:
                        context.bot.send_message(uid, get_translation("Задач пока нет. Создайте их!:)", lang),
                                reply_markup=InlineKeyboardMarkup([[
                                    InlineKeyboardButton("🏡", callback_data="::home::")
                                ]]))
                    else:
                        context.bot.send_message(uid, get_translation("Возврат в меню", lang),
                                                 reply_markup=InlineKeyboardMarkup([[
                                                     InlineKeyboardButton("🏡", callback_data="::home::")
                                                 ]]))
            elif data == "menu::gtable":
                if context.user_data[uid]["sheet"]:
                    update.callback_query.edit_message_text(get_translation("Ваша таблица: ", lang) + f"[{get_translation('Ссылка', lang)}]({context.user_data[uid]['sheet']})\n{get_translation('Не забудьте открыть доступ ')}{GSPREAD_ACCOUNT_EMAIL}",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔙", callback_data=f"back::gtable"),
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ], [InlineKeyboardButton(get_translation("Привязать другую", lang), callback_data="gtable::change")]]), parse_mode=ParseMode.MARKDOWN)
                else:
                    update.callback_query.edit_message_text(
                        get_translation("У вас пока нет действующей таблицы (spreadsheets.google.com). Привяжите её, чтобы начать получать ответы сотрудников.", lang) + context.user_data[uid]["sheet"],
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙", callback_data=f"back::gtable"),
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ], [InlineKeyboardButton(get_translation("Привязать таблицу", lang),
                                                 callback_data="gtable::change")]]))
            elif data.startswith("menu::add_bot"):
                from_action = data.strip("menu::add_bot::")
                if not check_subscription(update, context, "callback") and len(context.user_data[uid]["bot_list"]) > 1:
                    update.callback_query.edit_message_text(get_payment_ad(lang),
                                                            reply_markup=InlineKeyboardMarkup([[
                                                                InlineKeyboardButton("🔙",
                                                                                     callback_data=f"back::add_bot::{from_action}"),
                                                                InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ], [InlineKeyboardButton(get_translation("Получить доступ", lang), callback_data="menu::buy")]]))
                else:
                    context.user_data[bot_id][uid]['state'] = "token"
                    update.callback_query.edit_message_text(get_translation("Введите токен (@BotFather):", lang),
                                                            reply_markup=InlineKeyboardMarkup([[
                                                                InlineKeyboardButton("🔙",
                                                                                     callback_data=f"back::add_bot::{from_action}"),
                                                                InlineKeyboardButton("🏡", callback_data="::home::")
                                                            ]]))
                    context.user_data[uid]['state'] = "token"
            elif data == "menu::my_referrals":
                a = []
                for i in context.user_data[admin_id][uid]["referrals"]:
                    date_added = context.user_data[admin_id][uid]["referrals"][i]["date_added"]
                    payment = context.user_data[admin_id][uid]["referrals"][i]["payment_date"] if context.user_data[admin_id][uid]["referrals"][i]["payment_date"] != -1 else ""
                    if lang == "ru":
                        a.append(
                            f"@{context.bot.get_chat(i).username}:\n\tДата добавления: {date_added}\n\tПоследняя оплата: {payment if payment else 'Бесплатный аккаунт'}")
                    else:
                        a.append(
                            f"@{context.bot.get_chat(i).username}:\tDate added: {date_added}\n\tLast checkout:{payment if payment else 'Free account'}")
                if not a:
                    update.callback_query.edit_message_text(get_referral_text(lang), reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙", callback_data="back::referral"),
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ]]))
                else:
                    update.callback_query.edit_message_text('\n'.join(a), reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙", callback_data="back::referral"),
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ]]))
            elif data == "menu::lang":
                update.callback_query.edit_message_text(get_translation("Выберите язык", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::lang"),
                    InlineKeyboardButton("🇺🇸🇪🇺", callback_data="lang::en"),
                    InlineKeyboardButton("🇷🇺", callback_data="lang::ru"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            elif data == "menu::help":
                update.callback_query.edit_message_text(get_help(lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::help"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            elif data == "menu::my_bots":
                a = [[InlineKeyboardButton("🔙", callback_data="back::my_bots"),
                    InlineKeyboardButton("🏡", callback_data="::home::")]]
                for i in context.user_data[uid]["bot_list"]:
                    if i == admin_id:
                        continue
                    data = bots[i]
                    a.append([InlineKeyboardButton(f"{data.first_name} @{data.username}", callback_data=f"menu::messages::{i}")])
                a.append([InlineKeyboardButton(get_translation("Добавить бота", lang), callback_data="menu::add_bot::from_my_bots")])
                if len(a) == 2:
                    update.callback_query.edit_message_text(get_translation("Ботов пока нет", lang), reply_markup=InlineKeyboardMarkup(a))
                else:
                    update.callback_query.edit_message_text(get_translation("Ваши боты", lang), reply_markup=InlineKeyboardMarkup(a))
            elif data == "menu::buy":
                update.callback_query.edit_message_text(get_translation("Премиум доступ", lang) + "\n" + get_buy_text(lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::buy"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ], [InlineKeyboardButton("₽", callback_data="RUB::currency")],
                [InlineKeyboardButton("💶", callback_data="EUR::currency")],
                [InlineKeyboardButton("💲", callback_data="USD::currency")]]))
            elif data.startswith("buy::"):
                title = get_translation("Премиум доступ", lang)
                description = get_buy_text(lang)
                payload = "Custom-Payload"
                # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
                provider_token = "410694247:TEST:df95cc18-1b35-42fc-8620-b7c86b448285"
                start_parameter = "test-payment"
                currency = "RUB"
                # price in dollars
                price = 1
                # price * 100 so as to include 2 d.p.
                prices = [LabeledPrice("Test", price * 1000)]
    
                # optionally pass need_name=True, need_phone_number=True,
                # need_email=True, need_shipping_address=True, is_flexible=True
                try:
                    context.bot.send_invoice(uid, title, description, payload,
                                         provider_token, start_parameter, currency, prices)
                except Exception as e:
                    traceback.print_stack()
                    #print(e)

            elif data == "menu::add_task":
                keyboard = [
                    [InlineKeyboardButton("🔙", callback_data="back::add_task"),
                    InlineKeyboardButton("🏡", callback_data="::home::")]
                ]
                for i in context.user_data[uid]["bot_list"]:
                    if i == admin_id:
                        continue
                    c = bots[i]
                    keyboard.append([InlineKeyboardButton(f"{c.first_name} (@{c.username})", callback_data=f"add_task::{i}")])
                keyboard.append([InlineKeyboardButton(get_translation("Добавить бота", lang), callback_data="menu::add_bot::from_task")])
                update.callback_query.edit_message_text(get_translation("Выберите бота", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        elif data.startswith("add_task::"):
            bot_idt = data.strip("add_task::")
            update.callback_query.edit_message_text(get_translation("Добавление задач", lang),
                                                    reply_markup=InlineKeyboardMarkup([
                                                        [InlineKeyboardButton("🔙", callback_data="back::add_task::confirm"),
                                                         InlineKeyboardButton("🏡", callback_data="::home::")],
                                                        [InlineKeyboardButton(get_translation("Добавить задачу", lang), callback_data=f"menu::message::{bot_idt}")]
                                                    ]))
        elif data.startswith("messages::"):
            action, bot_idt, uid, job_id = data.strip("messages::").split("::")
            if action == "pause":
                context.user_data[bot_idt][uid][job_id]["state"] = "paused"
                update.callback_query.edit_message_text(to_text(context.user_data[bot_idt][uid][job_id], lang, bot_idt),
                                                        reply_markup=InlineKeyboardMarkup([
                                                            [InlineKeyboardButton(get_translation("Возобновить", lang),
                                                                                  callback_data=f"messages::resume::{bot_idt}::{uid}::{job_id}"),
                                                             InlineKeyboardButton(get_translation("Удалить", lang),
                                                                                  callback_data=f"messages::delete::{bot_idt}::{uid}::{job_id}")]
                                                        ]))
            elif action == "delete":
                delete_task(bot_idt, uid, job_id)
                context.user_data[bot_idt][uid].pop(job_id)
                update.callback_query.edit_message_text(get_translation("Задача успешно удалена", lang),
                                                    reply_markup=InlineKeyboardMarkup([
                                                         [InlineKeyboardButton("🏡", callback_data="::home::")]
                                                        ]))
            elif action == "resume":
                if not check_subscription(update, context, "callback"):
                    can = True
                    for bid in context.user_data[uid]["bot_list"]:
                        for i in context.user_data[bid][uid]:
                            if i.isdigit():
                                if context.user_data[bid][uid][i]["state"] == "running":
                                    can = False
                    if can:
                        context.user_data[bot_idt][uid][job_id]["state"] = "running"
                        update.callback_query.edit_message_text(to_text(context.user_data[bot_idt][uid][job_id], lang, bot_idt),
                                                                reply_markup=InlineKeyboardMarkup([
                                                                    [InlineKeyboardButton(
                                                                        get_translation("Приостановить", lang),
                                                                        callback_data=f"messages::pause::{bot_idt}::{uid}::{job_id}"),
                                                                     InlineKeyboardButton(
                                                                         get_translation("Удалить", lang),
                                                                         callback_data=f"messages::delete::{bot_idt}::{uid}::{job_id}")]
                                                                ]))
                    else:
                        update.callback_query.edit_message_text(
                            get_payment_ad(lang) + "\n" + to_text(context.user_data[bot_idt][uid][job_id], lang, bot_idt),
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(get_translation("Возобновить", lang),
                                                      callback_data=f"messages::resume::{bot_idt}::{uid}::{job_id}"),
                                 InlineKeyboardButton(get_translation("Удалить", lang),
                                                      callback_data=f"messages::delete::{bot_idt}::{uid}::{job_id}")], [InlineKeyboardButton(get_translation("Получить доступ💸", lang), callback_data="menu::buy")]]))
                else:
                    context.user_data[bot_idt][uid][job_id]["state"] = "running"
                    update.callback_query.edit_message_text(to_text(context.user_data[bot_idt][uid][job_id], lang, bot_idt),
                                                            reply_markup=InlineKeyboardMarkup([
                                                                [InlineKeyboardButton(
                                                                    get_translation("Приостановить", lang),
                                                                    callback_data=f"messages::pause::{bot_idt}::{uid}::{job_id}"),
                                                                 InlineKeyboardButton(
                                                                     get_translation("Удалить", lang),
                                                                     callback_data=f"messages::delete::{bot_idt}::{uid}::{job_id}")]
                                                            ]))
        elif data.endswith("::currency"):
            data = data.strip("::currency")
            if data == "RUB":
                a = []
                for i, j in [
                    (get_translation("1 месяц", lang), 290),
                    (get_translation("3 месяца (15% скидка)", lang), 740),
                    (get_translation("6 месяцев(20% скидка", lang), 1392),
                    (get_translation("12 месяцев (30% скидка)", lang), 2436),
                    (get_translation("На всю жизнь", lang), 4500)
                ]:
                    a.append(f"{i} ({j}‎₽): [{get_translation('Ссылка', lang)}]({get_link(data, uid, j)})")
                update.callback_query.edit_message_text(get_translation("Пожалуйста, не меняйте комментарий и сумму перевода, иначе оплата может быть не учтена. (откройте ссылку в браузере)\n\n", lang) + "\n\n".join(a),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙",
                                                                                 callback_data="back::currency"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]), parse_mode=ParseMode.MARKDOWN)
            elif data == "EUR":
                a = []
                for i, j in [
                    (get_translation("1 месяц", lang), 8.9),
                    (get_translation("3 месяца (15% скидка)", lang), 22.7),
                    (get_translation("6 месяцев(20% скидка", lang), 42.7),
                    (get_translation("12 месяцев (30% скидка)", lang), 74.8),
                    (get_translation("На всю жизнь", lang), 135)
                ]:
                    a.append(f"{i} ({j}‎€): [{get_translation('Ссылка', lang)}]({get_link(data, uid, j)})")
                update.callback_query.edit_message_text(get_translation(
                    "Пожалуйста, не меняйте комментарий и сумму перевода, иначе оплата может быть не учтена.\n\n",
                    lang) + "\n\n".join(a),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙",
                                                                                 callback_data="back::start"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]), parse_mode=ParseMode.MARKDOWN)
            elif data == "USD":
                a = []
                for i, j in [
                    (get_translation("1 месяц", lang), 9.90),
                    (get_translation("3 месяца (15% скидка)", lang), 25.25),
                    (get_translation("6 месяцев(20% скидка", lang), 47.52),
                    (get_translation("12 месяцев (30% скидка)", lang), 83.16),
                    (get_translation("На всю жизнь", lang), 155)
                ]:
                    a.append(f"{i} ({j}‎💲): [{get_translation('Ссылка', lang)}]({get_link(data, uid, j)})")
                update.callback_query.edit_message_text(get_translation(
                    "Пожалуйста, не меняйте комментарий и сумму перевода, иначе оплата может быть не учтена.\n\n",
                    lang) + "\n\n".join(a),
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🔙",
                                                                                 callback_data="back::start"),
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]), parse_mode=ParseMode.MARKDOWN)
        elif data.startswith("lang::"):
            data = data.strip("lang::")
            context.user_data[admin_id][uid]["lang"] = data
            update.callback_query.edit_message_text(get_translation("Привет!", data), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::lang_successful"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
        elif data.startswith("send_message::"):
            #print(data)
            context.user_data[uid]["state"] = data
            update.callback_query.edit_message_text(get_translation("Введите текст сообщения", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::send_message"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
        elif data == "change_date":
            if context.user_data[uid]["state"].startswith("promocode::"):
                update.callback_query.edit_message_text("Выберите дату, до которой промокод действителен:",
                                                        reply_markup=telegramcalendar.create_calendar())
            if context.user_data[uid]["state"] == 'end_date':
                update.callback_query.edit_message_text(text=get_translation("Выберите дату окончания:", lang), reply_markup=telegramcalendar.create_calendar("end"))
            else:
                update.callback_query.edit_message_text(text=get_translation("Выберите дату начала:", lang), reply_markup=telegramcalendar.create_calendar())
        elif data == "confirm_date":
            if context.user_data[uid]["state"].startswith('promocode::'):
                update.callback_query.edit_message_text("Введите текст промокода:",
                                                        reply_markup=InlineKeyboardMarkup([[
                                                            InlineKeyboardButton("🏡", callback_data="::home::")
                                                        ]]))

            elif context.user_data[uid]["state"] == 'end_date':
                context.user_data[uid]["state"] = 'pending'
                if not check_subscription(update, context, "callback"):
                    for bid in context.user_data[uid]["bot_list"]:
                        if uid not in context.user_data[bid]:
                            context.user_data[bid][uid] = {"id": 0, "state": "pending",
                                                      "subscription_end": str(datetime.now()).split()[0], "lang": "ru",
                                                      "referrer": "", "referrals": {}, "task_bot": admin_id}
                        for i in context.user_data[bid][uid]:
                            if i.isdigit():
                                if context.user_data[bid][uid][i]["state"] == "running":
                                    context.user_data[bid][uid][i]["state"] = "paused"
                context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]["state"] = "running"
                create_message(bots[bot_idd], context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])], bot_idd, uid, context.user_data[admin_id][uid]["lang"])
                if not check_subscription(update, context, "callback"):
                    update.callback_query.edit_message_text(get_translation('Рассылка успешно создана!', lang) + get_translation(" (все остальные задачи будут временно приостановлены, приобретите полную версию, чтобы иметь сразу несколько активных задач)", lang),
                                                            reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ], [InlineKeyboardButton(get_translation("Оплата💸", lang), callback_data="menu::buy")]]))
                else:
                    update.callback_query.edit_message_text(
                        get_translation('Рассылка успешно создана!', lang),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ]]))
                context.user_data[bot_idd][uid]["id"] += 1
            else:
                context.user_data[uid]["state"] = 'frequency'
                update.callback_query.edit_message_text(text=get_translation("Выберите периодичность:", lang), reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙", callback_data="back::frequency")],
                    [InlineKeyboardButton(get_translation('1 день', lang), callback_data="each_days")],
                    [InlineKeyboardButton(get_translation('2 дня', lang), callback_data="two_days")],
                    [InlineKeyboardButton(get_translation('3 дня', lang), callback_data="three_days")],
                    [InlineKeyboardButton(get_translation('4 дня', lang), callback_data="four_days")],
                    [InlineKeyboardButton(get_translation('5 дней', lang), callback_data="five_days")],
                    [InlineKeyboardButton(get_translation('6 дней', lang), callback_data="six_days")],
                    [InlineKeyboardButton(get_translation('7 дней', lang), callback_data="seven_days")],
                    [InlineKeyboardButton(get_translation('Выходные', lang), callback_data="out_days")],
                    [InlineKeyboardButton(get_translation('Будние', lang), callback_data="busy_days")],
                    [InlineKeyboardButton(get_translation('Каждое конкретный день в неделе', lang), callback_data="custom_week_days")],
                    [InlineKeyboardButton(get_translation('Последний день месяца.', lang), callback_data="month_end_days")],
                    [InlineKeyboardButton(get_translation('Каждое конкретное число в месяце', lang), callback_data="custom_days")],
                    [InlineKeyboardButton("🏡", callback_data="::home::")]
                ]))
        elif data == "confirm_days":
            context.user_data[uid]["state"] = 'time'
            update.callback_query.edit_message_text(text=get_translation("Выберите часы отправки:", lang), reply_markup=time_hours(lang))
        elif data.endswith('_days'):
            context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['frequency'] = data
            if data not in ("custom_days", "custom_week_days"):
                context.user_data[uid]["state"] = 'time'
                update.callback_query.edit_message_text(text=get_translation("Выберите часы отправки:", lang), reply_markup=time_hours(lang))
            else:
                context.user_data[uid]["state"] = data
                if data == "custom_week_days":
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'] = []
                    update.callback_query.edit_message_text(text=get_translation("Выберите дни недели:", lang), reply_markup=week(lang=lang))
                elif data == "custom_days":
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'] = []
                    update.callback_query.edit_message_text(text=get_translation("Выберите дни месяца:", lang), reply_markup=days(lang=lang))
        elif data.startswith("chat_id::"):
            data = data.strip("chat_id::")
            context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])] = {
                'chat_id': data, 'state': 'desc',
                "id": str(context.user_data[bot_idd][uid]["id"])
            }
            context.user_data[uid]["state"] = "desc"
            update.callback_query.edit_message_text(text=get_translation("Введите текст сообщения.", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::text"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
        elif data.endswith('_week'):
            if data == "confirm_week":
                context.user_data[uid]["state"] = 'time'
                update.callback_query.edit_message_text(text=get_translation("Выберите часы отправки:", lang), reply_markup=time_hours(lang))
            else:
                if data in context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week']:
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'].pop(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'].index(data))
                else:
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'].append(data)
                update.callback_query.edit_message_text(text=get_translation("Выберите дни недели:", lang), reply_markup=week(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_week'], lang))
        elif data.endswith("_day") and data.strip("_day").isdigit():
            data = data.strip("_day")
            if data in context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days']:
                context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'].pop(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'].index(data))
            else:
                context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'].append(data)
            update.callback_query.edit_message_text(text=get_translation("Выберите дни месяца:", lang), reply_markup=days(context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_days'], lang))
        elif data.endswith("_hr") and data.strip("_hr").isdigit():
            context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_hr'] = data.strip("_hr")
            context.user_data[uid]["state"] = 'minutes'
            update.callback_query.edit_message_text(text=get_translation("Выберите минуты отправки:", lang), reply_markup=time_minutes(lang))
        elif data.endswith("_min") and data.strip("_min").isdigit():
            context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['selected_min'] = data.strip("_min")
            context.user_data[uid]["state"] = 'end_date'
            update.callback_query.edit_message_text(text=get_translation("Выберите дату окончания рассылки:", lang), reply_markup=telegramcalendar.create_calendar("end"))
        else:
            selected, date = telegramcalendar.process_calendar_selection(update, context)
            if selected:
                if context.user_data[uid]["state"].startswith("promocode::"):
                    context.user_data[uid]["state"] += "::" + str(date).split()[0]
                    #print(context.user_data[uid]["state"])
                elif context.user_data[uid]["state"] == 'end_date':
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['end_date'] = str(date).split()[0]
                else:
                    context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['date'] = str(date).split()[0]
                update.callback_query.edit_message_text(text=get_translation("Вы выбрали ", lang) + "%s" % (date.strftime("%d/%m/%Y")), reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_translation("Подтвердить", lang), callback_data="confirm_date")],
                     [InlineKeyboardButton(get_translation("Выбрать другую", lang), callback_data="change_date")]]
                ))
        context.user_data = commit(update, context, "callback")
    except Exception as e:
        traceback.print_exc()


def texter(update, context):
    context.user_data = commit(update, context, "message")
    uid = str(update.message.chat_id)
    bot_id = str(context.bot.id)
    bot_idd = context.user_data[admin_id][uid]["task_bot"]
    lang = context.user_data[admin_id][uid]["lang"]
    if context.user_data[uid]["state"] == "admin::gtable":
        sheet_link = update.message.text
        try:
            scope = ['https://spreadsheets.google.com/feeds']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                'client_secret.json', scope)
            gc = gspread.authorize(credentials)
            sh = gc.open_by_url(sheet_link)
            admin_gspread_link = sheet_link
            update.message.reply_text(get_translation("Таблица успешно привязана", lang),
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton("🏡", callback_data="::home::")
                                      ]]))
            context.user_data[uid]["state"] = "pending"
        except Exception as e:
            #print(e)
            update.message.reply_text(get_translation(
                f"Бот не может получить доступ к таблице. Пожалуйста, проверьте настройки на spreadsheets.google.com и попробуйте ещё раз({GSPREAD_ACCOUNT_EMAIL})",
                lang),
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton("🏡", callback_data="::home::")
                                      ]]))
    elif context.user_data[uid]["state"].startswith("promocode::"):
        with open("promocodes.json") as f:
            s = load(f)
            i, date = context.user_data[uid]["state"].strip("promocode::").split("::")
            text = update.message.text
            s[text] = {
                "duration": i,
                "activated": 0,
                "expiration_date": date
            }
            update.message.reply_text(get_translation("Промокод успешно создан", lang),
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton("🔙", callback_data="back::to_promocodes"),
                                          InlineKeyboardButton("🏡", callback_data="::home::")
                                      ]]))
            dump(s, open("promocodes.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    elif context.user_data[uid]["state"] == "gtable":
        sheet_link = update.message.text
        try:
            scope = ['https://spreadsheets.google.com/feeds']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                'client_secret.json', scope)
            gc = gspread.authorize(credentials)
            sh = gc.open_by_url(sheet_link).sheet1
            context.user_data[uid]["sheet"] = sheet_link
            update.message.reply_text(get_translation("Таблица успешно привязана", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            context.user_data[uid]["state"] = "pending"
        except Exception as e:
            #print(e)
            update.message.reply_text(get_translation(f"Бот не может получить доступ к таблице. Пожалуйста, проверьте настройки на spreadsheets.google.com и попробуйте ещё раз ({GSPREAD_ACCOUNT_EMAIL})", lang),
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton("🏡", callback_data="::home::")
                                      ]]))
    elif context.user_data[uid]["state"] == "promocode":
        with open("promocodes.json") as f:
            s = load(f)
            text = update.message.text
            t = {
                '1weeks': timedelta(weeks=1),
                '2weeks': timedelta(weeks=2),
                '1months': relativedelta(months=1),
                '2months': relativedelta(months=2),
                '3months': relativedelta(months=3)
            }
            if text not in s:
                update.message.reply_text(get_translation("Такого промокода не нашлось, попробуйте ещё раз", lang), reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙", callback_data="back::start"),
                    InlineKeyboardButton("🏡", callback_data="::home::")
                ]]))
            else:
                if datetime.strptime(s[text]["expiration_date"], '%Y-%m-%d') < datetime.now():
                    update.message.reply_text(get_translation("У промокода истёк срок действия.", lang),
                                              reply_markup=InlineKeyboardMarkup([[
                                                  InlineKeyboardButton("🔙", callback_data="back::start"),
                                                  InlineKeyboardButton("🏡", callback_data="::home::")
                                              ]]))
                elif text in context.user_data[uid]["promocodes"]:
                    update.message.reply_text(get_translation("Вы уже вводили этот промокод", lang),
                                             reply_markup=InlineKeyboardMarkup([[
                                                 InlineKeyboardButton("🔙", callback_data="back::start"),
                                                 InlineKeyboardButton("🏡", callback_data="::home::")
                                             ]]))
                else:
                    context.user_data[uid]["state"] = "pending"
                    s[text]["activated"] += 1
                    context.user_data["stats"]["admin"]["promocode_usage_count"] += 1
                    context.user_data[uid]["promocodes"].append(text)
                    if context.user_data[admin_id][uid]["subscription_end"] != -1:
                        context.user_data[admin_id][uid]["subscription_end"] = str(datetime.strptime(context.user_data[admin_id][uid]["subscription_end"], ('%Y-%m-%d' if len(context.user_data[admin_id][uid]["subscription_end"].split()) == 1 else "%Y-%m-%d %H:%M:%S.%f")) + t[s[text]["duration"]]).split()[0]
                    update.message.reply_text(get_translation("Промокод успешно активирован", lang), reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙", callback_data="back::start"),
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ]]))
                    dump(s, open("promocodes.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
    elif context.user_data[uid]["state"] == "ref":
        rfid = update.message.text.strip("@")
        with open("users.json") as f:
            s = load(f)
            if rfid not in s:
                update.message.reply_text(get_translation("Такого пользователя не нашлось, попробуйте ещё раз", lang), reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏡", callback_data="::home::")
                    ]]))
            else:
                rfid = s[rfid]
                context.user_data[uid]["state"] = "token"
                context.user_data[admin_id][uid]["referrer"] = rfid
                context.user_data[admin_id][rfid]["referrals"][uid] = {
                    "date_added": str(datetime.now()),
                    "payment_date": -1
                }
                update.message.reply_text(get_translation("Спасибо, я учту это.", lang),
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("🏡", callback_data="::home::")
                                          ]]))
                update.message.reply_text(get_token_desc(lang),
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("🏡", callback_data="::home::")
                                          ]]))
    elif context.user_data[uid]["state"].startswith('send_message::'):
        context.user_data[bot_id][uid]["state"] = "pending"
        data = context.user_data[uid]["state"]
        if data == "send_message::all":
            for i in context.user_data[admin_id]:
                if i.isdigit():
                    try:
                        bots[admin_id].send_message(i, update.message.text, reply_markup=InlineKeyboardMarkup([[
                                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                                    ]]))
                    except Exception as e:
                        pass
                        #print(e)
        else:
            try:
                bots[admin_id].send_message(data.lstrip('send_message::'), update.message.text, reply_markup=InlineKeyboardMarkup([[
                                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                                    ]]))
            except Exception as e:
                pass
                #print(e)
        update.message.reply_text(get_translation("Рассылка прошла успешно", lang),
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("🏡", callback_data="::home::")
                                  ]]))
    elif context.user_data[uid]["state"] == "desc":
        context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['desc'] = update.message.text
        context.user_data[bot_idd][uid][str(context.user_data[bot_idd][uid]["id"])]['state'] = 'date'
        context.user_data[uid]["state"] = "date"
        update.message.reply_text(get_translation("Выберите дату начала:", lang), reply_markup=telegramcalendar.create_calendar())
    elif context.user_data[uid]['state'] == "token":
        text = update.message.text
        #print(text)
        if len(text.split(":")) != 2 or len(text) != 45 or not text.split(":")[0].isdigit():
            update.message.reply_text(get_translation("Неверный API токен. Попробуйте ещё раз", lang), reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙", callback_data="back::referrer"),
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ]]))
        else:
            context.user_data[uid]['state'] = "pending"
            context.user_data[uid]['bot_list'] = list(set(context.user_data[uid]['bot_list'] + [text.split(":")[0]]))
            d = add_bot(text, False, uid)
            if d.startswith("@"):
                if lang == "ru":
                    d = f"Поздравляем! Бот {d} успешно добавлен. Напишите ему /start, чтобы он начал работать."
                else:
                    d = f"Congratulations! Bot {d} added successfully. Send him /start now to run it."
            else:
                d = get_translation(d, lang)
            update.message.reply_text(d)
            update.message.reply_text(get_translation("Теперь создадим запрос\nПросто зайдите в пункт меню “Добавить задачу” и там все поймете.", lang), reply_markup=get_menu(lang, str(update.message.chat_id) in admin_user_id))
    context.user_data = commit(update, context, "message")


def reply_handler(update, context):
    context.user_data = commit(update, context, "message")
    if str(update.message.reply_to_message.from_user["id"]) == str(context.bot.id):
        bot_id = str(context.bot.id)
        sheet_link = context.user_data[context.user_data[bot_id]["owner"]]["sheet"]
        if not sheet_link:
            context.bot.send_message(context.user_data[bot_id]["owner"], get_translation("Бот не может сохранить ответы. Пожалуйста, привяжите таблицу в главном меню.", context.user_data[admin_id][context.user_data[bot_id]["owner"]]["lang"]), reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏡", callback_data="::home::")
                        ]]))
        else:
            lang = context.user_data[admin_id][context.user_data[bot_id]["owner"]]["lang"]
            answer_time = str(update.message.date)
            answer_text = update.message.text
            original_message = update.message.reply_to_message
            query_time = str(original_message.date)
            query_text = original_message.text
            answerer = update.message.from_user
            answer_from = f"{answerer.first_name} (@{answerer.username})"
            chat_name = update.message.chat.title
            scope = ['https://spreadsheets.google.com/feeds']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                'client_secret.json', scope)
            gc = gspread.authorize(credentials)
            sh = gc.open_by_url(sheet_link)
            name = f"{get_translation('Ответы', lang)}_{context.bot.first_name} (@{context.bot.username})"
            #print(name)
            for i in sh.worksheets():
                if i.title == name:
                    worksheet = sh.worksheet(name)
                    #print(worksheet.title)
                    break
            else:
                sh.add_worksheet(title=name, rows="1000", cols="20")
                worksheet = sh.worksheet(name)
                #print(worksheet.title)
                worksheet.insert_row([get_translation("Дата и время ответа", lang), get_translation("Ответ", lang), get_translation("Дата и время запроса", lang), get_translation("Запрос", lang), get_translation("Пользователь", lang), get_translation("Чат", lang)], 1)
            worksheet.insert_row([answer_time, answer_text.strip("'"), query_time, query_text, answer_from, chat_name], 2)
            #print("done")
            name = f"{get_translation('Реакции', lang)}_{context.bot.first_name} (@{context.bot.username})"
            for i in sh.worksheets():
                if i.title == name:
                    worksheet = sh.worksheet(name)
                    break
            else:
                sh.add_worksheet(title=name, rows="1000", cols="20")
                worksheet = sh.worksheet(name)
                worksheet.insert_row([get_translation("Запрос бота", lang), get_translation("Ответ пользователя", lang),
                                      get_translation("Реакция", lang), get_translation(
                        "Чтобы пометить реакцию как стандартную, напишите в графе \"Ответ пользователя\" \"другое\"")],
                                     1)
            reactions = worksheet.get_all_values()
            #print(reactions)
            lang = "ru"
            if reactions and reactions[0][0] == "Bot query":
                lang = "en"
            otr = "другое" if lang == "ru" else "other"
            reactions = [i for i in reactions if i[0] == query_text]
            #print(reactions)
            if not answer_text.isdigit():
                answered = False
                for i in reactions:
                    if answer_text.lower() in i[1].lower():
                        update.message.reply_text(i[2])
                        answered = True
                        break
                if not answered:
                    for i in reactions:
                        if otr.lower() == i[1].lower() or answer_text.lower() in i[1].lower():
                            update.message.reply_text(i[2])
                            break
            else:
                a = []
                other = ""
                for i in reactions:
                    if otr.lower() in i[1].lower():
                        other = i[2]
                    else:
                        a.append((i[1], i[2]))
                a = [(0, "")] + list(sorted(a)) + [(float('inf'), "")]
                #print(a)
                amt = int(answer_text)
                for j in range(1, len(a) - 1):
                    if int(a[j - 1][0]) < amt <= int(a[j][0]):
                        update.message.reply_text(a[j][1])
                        break
                else:
                    if other:
                        update.message.reply_text(other)


def send_stats_user(bot, uid):
    with open("dumpp.json") as f:
        s = load(f)
        if s[admin_id][uid]["subscription_end"] == -1 or datetime.strptime(s[admin_id][uid]["subscription_end"], '%Y-%m-%d') >= datetime.now():
            try:
                if s[uid]["bot_list"].index(str(bot.id)) != 0:
                    return
            except Exception:
                return
        sheet_link = s[uid]["sheet"]
        lang = s[admin_id][uid]["lang"]
        if not sheet_link:
            return
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'client_secret.json', scope)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_url(sheet_link)
        try:
            bot.send_message(uid, get_translation("Ежедневная статистика, присылаемая администратору бота", lang), reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏡", callback_data="::home::")
            ]]))
        except Exception as e:
            bots[admin_id].send_message(uid, get_translation("Пожалуйста, напишите клиентскому боту ",
                                                             lang) + f"@{bot.username}" + get_translation(
                " без этого он не сможет отправить Вам статистику"), reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏡", callback_data="::home::")
            ]]))
            return
        with open("muted_chats.json") as f:
            muted = load(f)[uid]
        for i in sh.worksheets():
            if f"{get_translation('Ответы', lang)}_" in i.title and "(@" in i.title:
                #print(1)
                keys = i.row_values(1)
                cell_list = set(j.row for j in i.findall(re.compile(str(date.today()) + "*")))
                for j in cell_list:
                    vals = i.row_values(j)
                    #print(vals)
                    mtd = False
                    for j in muted:
                        if muted[j]["title"] == vals[-1]:
                            mtd = muted[j]["muted"]
                            break
                    if not mtd:
                        a = '\n'.join([f"{keys[i]}: {vals[i]}" for i in range(min(len(keys), len(vals)))])
                        try:
                            bot.send_message(uid, a, reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                        except Exception as e:
                            bots[admin_id].send_message(uid, get_translation("Пожалуйста, напишите клиентскому боту ", lang) + f"@{bot.username}" + get_translation(" без этого он не сможет отправить Вам статистику"), reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🏡", callback_data="::home::")
                            ]]))
                            return


def add_bot(token, from_main=False, uid=""):
    if not from_main:
        with open("tokens.json") as f:
            s = load(f)
            if token in s:
                return "Бот уже работает"
    #print("received token:", token)
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat))
    dp.add_handler(MessageHandler(Filters.reply, reply_handler))
    dp.add_handler(MessageHandler(Filters.text, texter))
    dp.add_error_handler(error)
    updater.start_polling()
    bot = updater.bot
    print(bots, token)
    bots[str(bot.id)] = bot
    #updater.idle()
    if not from_main:
        if token not in s:
            s[token] = token.split(":")[0]
            dump(s, open("tokens.json", 'w+', encoding="utf-8"), ensure_ascii=False, indent=4)
    #print("started working")
    s = load_db()
    if str(bot.id) in s:
        for uid in s[str(bot.id)]:
            if uid.isdigit():
                for k in s[str(bot.id)][uid]:
                    if k.isdigit():
                        if s[str(bot.id)][uid][k]["state"] == "running":
                            create_message(bot, s[str(bot.id)][uid][k], str(bot.id), uid, s[admin_id][uid]["lang"], True)
        schedule.every().day.at("23:00").do(send_stats_user, bot, s[str(bot.id)]["owner"])
    else:
        s[str(bot.id)] = {"owner": uid, "chat_list": {}}
    dump(s, open("dumpp.json", 'w+', encoding="utf-8"), ensure_ascii=False, indent=4)
    if not from_main:
        return f"@{bot.username}"


def dump_admin():
    with open("dumpp.json") as f:
        #print("start")
        s = load(f)
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'client_secret.json', scope)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_url(admin_gspread_link)
        name = "Статистика"
        for i in sh.worksheets():
            if i.title == name:
                break
        else:
            sh.add_worksheet(title=name, rows="1000", cols="20")
        worksheet = sh.worksheet(name)
        s = update_admin_stats(type=1, data=s) # ["stats"]["admin"]
        cell_list = worksheet.range('A1:F1')
        for i, val in enumerate(
                ["Время", "Кол-во пользователей", "Кол-во оплат", "Кол-во использования промокодов:", "Кол-во запросов созданных за сутки:", "Кол-во запросов отправленных за сутки:"]):
            cell_list[i].value = val
        worksheet.update_cells(cell_list)
        worksheet.insert_row([str(datetime.now()), s["stats"]["admin"]["users_count"], s["stats"]["admin"]["checkout_count"], s["stats"]["admin"]["promocode_usage_count"], s["stats"]["admin"]["tasks_created_day"], s["stats"]["admin"]["tasks_sent_day"]], 2)
        name = "Статистика пользователей"
        for i in sh.worksheets():
            if i.title == name:
                worksheet = sh.worksheet(name)
                break
        else:
            sh.add_worksheet(title=name, rows="1000", cols="20")
            worksheet = sh.worksheet(name)
            worksheet.insert_row(["id", "@username", "Дата регистрации", "Боты", "Количество запросов за последний месяц",
             "Количество софрмированных запросов", "Тариф", "Количество оплат RUB", "Количество оплат EUR", "Количество оплат USD", "Сумма оплат", "Промокоды",
             "Рефералы", "Когда закончится полный период"], 1)
        for uid in s[admin_id]:
            if uid.isdigit():
                #print(uid)
                bot_list = ', '.join(["@" + bots[i].username for i in s[uid]["bot_list"] if i != admin_id])
                plan = "Платный" if (s[admin_id][uid]["subscription_end"] == -1 or datetime.strptime(s[admin_id][uid]["subscription_end"], '%Y-%m-%d') >= datetime.now()) else "Бесплатный"
                payments = [s[uid]['checkouts_sum']['EUR'], s[uid]['checkouts_sum']['RUB'], s[uid]['checkouts_sum']['USD']]
                promocodes = ", ".join(s[uid]['promocodes'])
                referrals = []
                for i in s[admin_id][uid]["referrals"]:
                    try:
                        referrals.append(bots[admin_id].get_chat(i).username if bots[admin_id].get_chat(i).username else "hidden")
                    except Exception:
                        referrals.append("hidden")
                referrals = ", ".join(referrals)
                end_date = s[admin_id][uid]["subscription_end"] if s[admin_id][uid]["subscription_end"] != -1 else "Никогда (доступ на всю жизнь)"
                k = worksheet.findall(uid)
                if k:
                    k = k[0].row
                    #print(k)
                    cell_list = worksheet.range(f'A{k}:N{k}')
                    try:
                        name = bots[admin_id].get_chat(uid).username
                    except Exception:
                        name = "hidden"
                    for i, val in enumerate([uid, name,
                                  s[uid]["date_registered"], bot_list, s["stats"][uid]["requests_created"], s["stats"][uid]["requests_sent"],
                                  plan, s[uid]['checkouts_count'], *payments, promocodes, referrals, end_date]):
                        cell_list[i].value = val
                    worksheet.update_cells(cell_list)
                else:
                    try:
                        name = bots[admin_id].get_chat(uid).username
                    except Exception:
                        name = "hidden"
                    worksheet.insert_row([uid, name,
                                  s[uid]["date_registered"], bot_list, s["stats"][uid]["requests_created"], s["stats"][uid]["requests_sent"],
                                  plan, s[uid]['checkouts_count'], *payments, promocodes, referrals, end_date], 2)
        name = "Промокоды"
        for i in sh.worksheets():
            if i.title == name:
                worksheet = sh.worksheet(name)
                break
        else:
            sh.add_worksheet(title=name, rows="1000", cols="20")
            worksheet = sh.worksheet(name)
            worksheet.insert_row(["Промокод", "Количество использований"], 1)
        with open("promocodes.json") as f:
            t = load(f)
            for i in t:
                k = worksheet.findall(i)
                if k:
                    k = k[0].row
                    cell_list = worksheet.range(f'A{k}:B{k}')
                    for i, val in enumerate([i, t[i]["activated"]]):
                        cell_list[i].value = val
                    worksheet.update_cells(cell_list)
                else:
                    worksheet.insert_row([i, t[i]["activated"]], 2)
        #print("all-in")


def activate(update, context):
    context.user_data = commit(update, context, "command")
    username = ' '.join(update.message.text.split()[1:]).lstrip("@")
    if str(update.message.from_user.id) not in admin_user_id:
        update.message.reply_text("Этой командой может пользоваться только администратор", reply_markup=InlineKeyboardMarkup([[
                                                        InlineKeyboardButton("🏡", callback_data="::home::")
                                                    ]]))
    else:
        with open("users.json") as f:
            s = load(f)
            if username not in s:
                update.message.reply_text("Такой пользователь ещё у нас не зарегистрирован",
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("🏡", callback_data="::home::")
                                          ]]))
            else:
                context.user_data[admin_id][s[username]]["subscription_end"] = -1
                context.user_data = commit(update, context, "command")
                update.message.reply_text("Пользователю успешно подключен безлимит.",
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("🏡", callback_data="::home::")
                                          ]]))



def main():
    with open("tokens.json") as f:
        s = eval(f.read())
        #print(s)
        for i in s:
            #print(i)
            add_bot(i, True, "")
    schedule.every().minute.do(check_payments).run()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    bot = updater.bot
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CommandHandler("activate", activate))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat))
    dp.add_handler(MessageHandler(Filters.reply, reply_handler))
    dp.add_handler(MessageHandler(Filters.text, texter))
    dp.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
    dp.add_error_handler(error)
    updater.start_polling()
    #updater.idle()
    bots[str(bot.id)] = bot
    s = load_db()
    if str(bot.id) in s:
        for uid in s[str(bot.id)]:
            if uid.isdigit():
                notify(bot, uid)
    print("loaded messages")
    schedule.every(15).minutes.do(dump_admin).run()
    while True:
        print(schedule.jobs)
        print(datetime.now())
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    main()

