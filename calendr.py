from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from stuff import get_translation


def week(selected=[], lang="ru"):
    d = {
        "mo_week": 'Mo',
        "tu_week": 'Tu',
        "we_week": 'We',
        "th_week": 'Th',
        "fr_week": 'Fr',
        "sa_week": 'Sa',
        "su_week": 'Su'
    }
    keyboard = [[InlineKeyboardButton("🔙", callback_data="back::week")]]
    for i in d:
        if i in selected:
            keyboard.append([InlineKeyboardButton("{}✓".format(d[i]), callback_data=i)])
        else:
            keyboard.append([InlineKeyboardButton(d[i], callback_data=i)])
    keyboard.append([InlineKeyboardButton(get_translation("Подтвердить", lang), callback_data="confirm_week")])
    return InlineKeyboardMarkup(keyboard)


def days(selected=[], lang="ru"):
    keyboard = [[InlineKeyboardButton("🔙", callback_data="back::days")], []]
    for j in range(1, 32):
        if j % 5:
            i = str(j)
            if i.strip("_day") in selected:
                keyboard[-1].append(InlineKeyboardButton("{}✓".format(i), callback_data=i + "_day"))
            else:
                keyboard[-1].append(InlineKeyboardButton(i, callback_data=i + "_day"))
        else:
            i = str(j)
            if i.strip("_day") in selected:
                keyboard.append([InlineKeyboardButton("{}✓".format(i), callback_data=i + "_day")])
            else:
                keyboard.append([InlineKeyboardButton(i, callback_data=i + "_day")])
    keyboard.append([InlineKeyboardButton(get_translation("Подтвердить", lang), callback_data="confirm_days")])
    return InlineKeyboardMarkup(keyboard)


def time_hours(lang="ru"):
    keyboard = [[InlineKeyboardButton("🔙", callback_data="back::hours")]]
    for j in range(24):
        if j % 6:
            i = str(j)
            keyboard[-1].append(InlineKeyboardButton(i, callback_data=i + "_hr"))
        else:
            i = str(j)
            keyboard.append([InlineKeyboardButton(i, callback_data=i + "_hr")])
    return InlineKeyboardMarkup(keyboard)


def time_minutes(lang="ru"):
    keyboard = [[InlineKeyboardButton("🔙", callback_data="back::minutes")]]
    i = 0
    for j in range(10):
        a = [InlineKeyboardButton(str(i), callback_data=str(i) + "_min")]
        i += 1
        while i % 6:
            a.append(InlineKeyboardButton(str(i), callback_data=str(i) + "_min"))
            i += 1
        keyboard.append(a)
    return InlineKeyboardMarkup(keyboard)
