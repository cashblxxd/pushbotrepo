import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from datetime import date


'''
def bought(update, context):
    context.user_data = commit(update, context, "message")
    uid = str(update.message.from_user.id)
    bot_id = str(context.bot.id)
    d = {
        "1months": relativedelta(months=1),
        "3months": relativedelta(months=3),
        "6months": relativedelta(months=6),
        "12months": relativedelta(months=12),
        "unlimited": -1
    }
    if length != "unlimited" and context.user_data[bot_id][uid]["subscription_end"] != -1:
        context.user_data[admin_id][uid]["subscription_end"] = str(datetime.strptime(context.user_data[bot_id][uid]["subscription_end"], '%Y-%m-%d') + d[length])
    else:
        context.user_data[admin_id][uid]["subscription_end"] = -1
    for bot_id in context.user_data[uid]:
        for i in range(context.user_data[bot_id][uid]["id"]):
            context.user_data[bot_id][uid][str(i)]["state"] = "running"
    rfid = context.user_data[admin_id][uid]["referrer"]
    if rfid:
        context.user_data[admin_id][rfid]["subscription_end"] = str(datetime.strptime(context.user_data[admin_id][uid]["subscription_end"], '%Y-%m-%d') + relativedelta(months=1))
        context.user_data[admin_id][rfid]["referrals"]["uid"]["payment_date"] = str(datetime.now())
    context.user_data = commit(update, context, "message")
'''



def update_db():
    sheet_link = "https://docs.google.com/spreadsheets/d/1B0_iirzerj352AWzLG1JziBKor2PfOsiThrIAoX6lFA/edit?usp=drivesdk"
    if not sheet_link:
        return
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'client_secret.json', scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_url(sheet_link)
    for i in sh.worksheets():
        if "_" in i.title and "(@" in i.title:
            print(1)
            keys = i.row_values(1)
            cell_list = set(j.row for j in i.findall(re.compile(str(date.today()) + "*")))
            for j in cell_list:
                print(i.row_values(j))
    ''''''


update_db()