from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
import datetime
import calendar
from dateutil.relativedelta import relativedelta


def create_callback_data(action,year,month,day):
    """ Create the callback data associated to each button"""
    return ";".join([action,str(year),str(month),str(day)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_calendar(year=None, month=None, start_or_end="start"):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = [[InlineKeyboardButton("🔙", callback_data=f"back::{start_or_end}_calendar"),
                 InlineKeyboardButton("🏡", callback_data="::home::")]]
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
    keyboard.append(row)
    #Second row - Week Days
    row=[]
    for day in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
        row.append(InlineKeyboardButton(day,callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day),callback_data=create_callback_data("DAY",year,month,day)))
        keyboard.append(row)
    #Last row - Buttons
    row=[]
    row.append(InlineKeyboardButton("<",callback_data=create_callback_data("PREV-MONTH",year,month,day)))
    row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
    row.append(InlineKeyboardButton(">",callback_data=create_callback_data("NEXT-MONTH",year,month,day)))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def process_calendar_selection(update, context):
    ret_data = (False,None)
    query = update.callback_query
    print(query.data)
    (action,year,month,day) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)
    start_or_end = "start" if context.user_data[str(update.callback_query.from_user.id)]["state"] == "date" else "end"
    if action == "IGNORE":
        pass
        #bot.answer_callback_query(callback_query_id= query.id)
    elif action == "DAY":
        update.callback_query.edit_message_text(text=query.message.text)
        ret_data = True,datetime.datetime(int(year),int(month),int(day))
    elif action == "PREV-MONTH":
        pre = curr - relativedelta(days=1)
        update.callback_query.edit_message_text(text=query.message.text, reply_markup=create_calendar(int(pre.year),int(pre.month),start_or_end))
    elif action == "NEXT-MONTH":
        ne = curr + relativedelta(days=31)
        update.callback_query.edit_message_text(text=query.message.text, reply_markup=create_calendar(int(ne.year),int(ne.month),start_or_end))
    else:
        pass
        #bot.answer_callback_query(callback_query_id= query.id,text="Something went wrong!")
        # UNKNOWN
    return ret_data


