from datetime import datetime


def get_help(lang="ru"):
    if lang == "ru":
        return "/start - начать диалог с ботом\n/menu - показать главное меню\nhttps://clck.ru/JG6Dn - подробная инструкция к боту\nПо всем вопросам обращаться: Pushistbot@yandex.ru"
    return "/start - start conversation with the bot\n/menu - get main menu\nhttps://clck.ru/JG6Dn - detailed bot instructions\nAny questions: Pushistbot@yandex.ru"


def get_payment_ad(lang="ru"):
    if lang == "ru":
        return """У вас всего 1 доступный запрос и ответы на запрос не выгружаются в гугл таблицу.
Этот бот даст тебе от 20 до 60 минут свободного времени и изменит твою жизнь.
Кнопка “Получить доступ” - переход к меню оплаты.
        """
    return """You have only 1 free task and these are not extracted to google sheets.
This bot 'll give you 20-60 free minutes every day and, moreover, it'll change your entire life.
“Checkout” button is your entry point to the better future.
    """


def get_translation(query, lang="ru"):
    if lang == "ru":
        return query
    return tr[query]


def get_token_desc(lang="ru"):
    if lang == "ru":
        return """https://clck.ru/JG6Dn
        Теперь перейди в @botfather, создай бота и пришли мне API токен. После этого ты получишь бесплатную неделю премиум-доступа бесплатно!
        """
    return "https://clck.ru/JG6Dn\nSend a /newbot to @botfather, follow the instructions and send me the token. After that you'll get a premium for a week, completely free!"


def get_menu_text(update, context, uid, admin_id, lang):
    if lang == "ru":
        if context.user_data[admin_id][uid]["subscription_end"] == -1:
            paid = "✅️Оплаченный"
            end_time = "навсегда."
        else:
            if datetime.strptime(context.user_data[admin_id][uid]["subscription_end"], '%Y-%m-%d') >= datetime.now():
                paid = "✅️Оплаченный"
                end_time = f"до {context.user_data[admin_id][uid]['subscription_end']}. Доступны все функции."
            else:
                paid = "❌️Неоплаченный."
                end_time = "Доступно 1 уведомление в день."
        return f"""Добро пожаловать в личный кабинет!
Здесь информация по ботам, задачам, оплате и приглашенным.
Статус:
{paid} {end_time}
        """
    if context.user_data[admin_id][uid]["subscription_end"] == -1:
        paid = "✅Paid"
        end_time = "forever."
    else:
        if datetime.strptime(context.user_data[admin_id][uid]["subscription_end"], '%Y-%m-%d') >= datetime.now():
            paid = "✅Paid"
            end_time = f"till {context.user_data[admin_id][uid]['subscription_end']}. All features available."
        else:
            paid = "❌Unpaid."
            end_time = "Only 1 message a day available."
    return f"""Welcome to your profile!
Here is info about your bots, tasks,  payments and referrals.
Status:
{paid} {end_time}
            """


def get_admin_stats(admin_stats, lang):
    if lang == "ru":
        return f"""Кол-во пользователей: {admin_stats['users_count']}

Кол-во оплат: {admin_stats['checkout_count']}

Кол-во использования промокодов: {admin_stats['promocode_usage_count']}

Кол-во запросов созданных за сутки: {admin_stats['tasks_created_day']}

Кол-во запросов отправленных за сутки: {admin_stats['tasks_sent_day']}

Пользователи
        """
    return f"""Users count: {admin_stats['users_count']}

Checkout count: {admin_stats['checkout_count']}

Promocode usage count: {admin_stats['promocode_usage_count']}

Tasks created for the last day: {admin_stats['tasks_created_day']}

Tasks sent for the last day: {admin_stats['tasks_sent_day']}

Users
            """


def get_buy_text(lang):
    if lang == "ru":
        return "Оплаченный аккаунт даёт вам:\n- неограниченное количество уведомлений\n- выгрузка ответов в GoogleSheets\n- настройка реакций бота на конкретный ответ пользователя\n- финальный отчёт со всех чатов в конце дня в ЛС\n- возможность использовать несколько ботов в разных чатах\n- от 20 до 60 минут в день дополнительного свободного времени\n- контроль всех сотрудников без повседневного вмешательства"
    return "Paid account provides you with:\n- unlimited tasks\n- GoogleSheets integration\n- Bot reactions to specific user responses\n- Daily report of all chats in direct messages\n- Multiple bots in chats\n- From 20 to 60 minutes free every day\n- Control over employees"


def get_referral_text(lang):
    if lang == "ru":
        return "Сейчас рефералов нет. Вы и ваш друг получите дополнительно по 1 месяцу расширенного доступа, если ваш друг при регистрации введёт ваш логин и оплатит хотя бы один месяц."
    return "Currently no referrals. You and your friend will get 1 month of premium access if he enters your login at registration and purchases at least 1 month."


tr = {
    "Чем могу помочь?": "Hello! How can i help?",
    "Всем работягам привет!": "Hello, chat!",
    "Извините, из этого бота можно создавать только других ботов": "Sorry, from main bot you can only create other bots",
    "Извините, создавать задачи может только администратор бота.": "Sorry, only bot admin can create tasks",
    "В бесплатном аккаунте доступна только 1 задача. Приобретите расширенные возможности на /buy": "You are only able to create one task while on a free account. Upgrade at /buy",
    "Чатов нет;(\nДобавьте меня хотя бы в один чат:)": "No chats.:(\nAdd me to at least one chat:)",
    "Выберите чат:": "Choose chat:",
    "Привет!": "Hi!",
    "Введите текст сообщения": "Enter message text:",
    "Выберите дату окончания:": "Enter end date:",
    "Выберите дату начала:": "Enter start date:",
    "Рассылка успешно создана!": "Mailing created successfully!",
    "1 день": "1 day",
    "2 дня": "2 days",
    "3 дня": "3 days",
    "4 дня": "4 days",
    "5 дней": "5 days",
    "6 дней": "6 days",
    "7 дней": "7 days",
    "Выходные": "Weekends",
    "Будние": "Weekdays",
    "Каждое конкретный день в неделе": "Custom days in week",
    "Последний день месяца.": "End of each month",
    "Каждое конкретное число в месяце": "Custom days of month",
    "Выберите дни недели:": "Choose days of week",
    "Выберите дни месяца:": "Choose days of month",
    "Введите текст сообщения.": "Enter message text:",
    "Выберите часы отправки:": "Enter mailing hours:",
    "Выберите дату окончания рассылки:": "Enter date of mailing end:",
    "Ботов можно добавлять только в основном боте": "Bots can only be added in the main bot",
    "В бесплатном аккаунте доступен только 1 бот. Приобретите расширенные возможности на /buy": "You are only able to have one bot while on a free account. Upgrade at /buy",
    "Введите токен (@BotFather):": "Enter token (@BotFather):",
    "Бот уже работает": "This bot is already working",
    "Поздравляем! Бот успешно добавлен. Напишите ему /start, чтобы он начал работать.": "Congrats! Bot added successfully. Write to him to start creating tasks!",
    "1 месяц": "1 month",
    "3 месяца (15% скидка)": "3 months (15% off)",
    "6 месяцев (20% скидка)": "6 months (20% off)",
    "12 месяцев (30% скидка)": "12 months (30% off)",
    "Безлимит": "Unlimited",
    "Приобретите премиум, чтобы получить безлимит на ботов и задания в чатах": "Buy premium to get unlimited bots and tasks in chats",
    "У вас уже есть реферер.": "You have a referrer already",
    "Введите ID человека, который Вас пригласил": "Enter ID of the person who invited you",
    "Такого пользователя не нашлось, попробуйте ещё раз": "No such person in the database, please try again",
    "Рефералов пока нет": "No referrals yet",
    "Выберите язык": "Choose your language",
    "Приостановить": "Pause",
    "Удалить": "Delete",
    "Возобновить": "Resume",
    "Задача успешно удалена": "Task deleted successfully",
    "Вы выбрали ": "You selected ",
    "Подтвердить": "Confirm",
    "Выберите минуты отправки:": "Enter mailing minutes:",
    "Задач пока нет. Создайте их!:) /message": "No tasks yet. Create them!:) /message",
    "Выбрать другую": "Choose another",
    "Выберите периодичность:": "Choose periodicity",
    "В бесплатной версии доступна только первая созданная задача на первом боте": "With a free subscription you are allowed only to run first created task of your first bot.",
    "Неверный API токен. Попробуйте ещё раз": "Invalid API token. Please try again",
    "Главное меню": "Main menu",
    "Стартовое меню": "Start menu",
    "Добавить задачу📝": "Add task📝",
    "Список моих задач": "My task list",
    "Добавить бота🖥️": "Add bot🖥️",
    "Указать реферера": "Enter referrer",
    "Мои рефералы📣": "My referrals📣",
    "Сменить язык🎌": "Switch language🎌",
    "Справка📖": "Get help 📖",
    "Ваши задачи": "Your tasks",
    "Магазин": "Shop",
    "Не забудьте поделиться с рефералами своим id:": "Don't forget to share the ID with your referrals",
    "Реферрер успешно добавлен": "Referrer added successfully",
    "Рассылка прошла успешно": "User mailing successful",
    "Работает": "Running",
    "Приостановлено": "Paused",
    "Ботов пока нет": "No bots yet",
    "Выберите бота": "Choose bot",
    "Оплата💸": "Checkout💸",
    "Ваши боты": "Your bots",
    "Премиум доступ": "Premium plan",
    "Вы уже зарегистрированы!:)": "You are already signed in!:)",
    "Привет, начнем же процедуру регистрации твоего первого личного бота. Введи @username человека, который тебя пригласил.\nПосле оплаты вы оба получите приятный бонус": "So let's register your first bot. Enter @username of the person who invited you.\nBoth of you will have a special bonus after purchase",
    "Спасибо, я учту это.": "Thanks, I'll keep it in mind.",
    "Теперь создадим запрос\nПросто зайдите в пункт меню “Создать запрос” и там все поймете.": "Yet let's create our first task. Navigate to “Add task” in the menu and you'll get it",
    "Мои боты🤖": "My bots🤖",
    "АДМИНИСТРАТОРСКАЯ ПАНЕЛЬ": "ADMIN PANEL",
    "Нет реферера": "No referrer",
    "Таблица📈": "Spreadsheet📈",
    "Добавление задач": "Task management",
    "Добавить задачу": "Add task",
    "Активировать промокод🎁": "Activate a promocode🎁",
    "Введите промокод": "Enter your promocode",
    "Такого промокода не нашлось, попробуйте ещё раз": "No such promocode, please try again",
    "Промокод успешно активирован": "Promocode activation successful",
    "Бот не может сохранить ответы. Пожалуйста, привяжите таблицу в главном меню.": "Bot can not save answers. Please, link the spreadsheet in main menu",
    "Ваша таблица": "Your spreadsheet",
    "Привязать другую": "Change link",
    "У вас пока нет действующей таблицы (spreadsheets.google.com). Привяжите её, чтобы начать получать ответы сотрудников.": "You haven't linked a spreadsheet yet (spreadsheets.google.com). Link one to start receiving employee answers.",
    "Привязать таблицу": "Link a spreadsheet",
    "Введите ссылку на Вашу таблицу. Не забудьте открыть доступ ": "Enter your spreadsheet link. Don't forget to open it for editing for  ️",
    " на редактирование⚠️": " for editing⚠",
    "Бот не может получить доступ к таблице. Пожалуйста, проверьте настройки на spreadsheets.google.com и попробуйте ещё раз": "Our bot can not get access to your spreadsheet. Please, check permissions at spreadsheets.google.com and try again.",
    'Извините, задачи может смотреть только администратор бота': "Only bot admin can view bot tasks.",
    "Хочу получать статистику в чат: ": "Want to get stats in chat: ",
    "да": "yes",
    "нет": "no",
    "На всю жизнь": "Forever",
    "Чатов пока нет. Добавляйте своих ботов в чаты, чтобы настраивать уведомления": "No chats yet. Start adding your bots to chats to make this feature available",
    "Ваши чаты": "Your chats",
    "Возврат в меню": "Back to menu",
    "Вы уже вводили этот промокод": "You have already entered this promocode once",
    "Ответы": "Answers",
    "Запрос бота": "Bot query",
    "Дата и время ответа": "Response datetime",
    "Ответ": "Response",
    "Дата и время запроса": "Query datetime",
    "Запрос": "Query",
    "Пользователь": "User",
    "Чат": "Chat",
    "Ответ пользователя": "User response",
    "Реакция": "Bot reaction",
    "Чтобы пометить реакцию как стандартную, напишите в графе \"Ответ пользователя\" \"другое\"": "To mark reaction as default, enter in \"User response\" \"other\"",
    "Настройка уведомлений из чатов💬": "Chat notifications settings💬",
    "Задач пока нет. Создайте их!:)": "No tasks yet. Try create them!:)",
    "Реакции": "Responses",
    "Промокод успешно создан": "Promocode created successfully",
    "Таблица успешно привязана": "Spreadsheet linked successfully",
    "Ежедневная статистика, присылаемая администратору бота": "Stats daily sent to bot admin",
    "Ещё": "More",
    "Пожалуйста, не меняйте комментарий и сумму перевода, иначе оплата может быть не учтена. (откройте ссылку в браузере)\n\n": "Please don't change amount and comment, as otherwise your purchase could not be registered. (open lonk in browser)\n\n",
    "Пожалуйста, напишите клиентскому боту ": "Please, send a message to ",
    " без этого он не сможет отправить Вам статистику": " as otherwise he can not send you usage stats.",
    "Ссылка": "Link",
    "Не забудьте открыть доступ ": "Don't forget to open it to editing for ",
    " (все остальные задачи будут временно приостановлены, приобретите полную версию, чтобы иметь сразу несколько активных задач)": " (all other tasks will be temporarily paused, buy subscription to run multiple tasks in parallel)",
    "Получить доступ": "Get full access",
    "Спасибо за покупку!": "Thank you for your payment!",
    "Ваш премиум-доступ!": "Your premium access!",
    "Оплачивать можно только из основного бота @pushist_bot": "You can only pay from the main bot @pushist_bot",
    "\nБанковская карта:": "\nBank card:",
    "Введите вашу временную зону:": "Enter your timezone:",
    "Ваша таблица: ": "Your spreadsheet: ",
    "Выберите чат": "Choose chat"
}


