#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
import asyncio, json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
from openai import OpenAI

BOT_TOKEN = "8728811728:AAHEQCRrOXREEoSyDRBhRz2zWVhAvA-e1Q8"
OPENROUTER_API_KEY = "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"

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://localhost",
        "X-OpenRouter-Title": "UniHelper"
    },
    timeout=45.0
)

DB = "unihelper_stable.db"

COUNTRIES = {
    "ru": ["🇺🇸 Америка", "🇹🇷 Турция", "🇨🇳 Китай", "🇦🇪 ОАЭ", "🇲🇾 Малайзия"],
    "tj": ["🇺🇸 Амрико", "🇹🇷 Туркия", "🇨🇳 Чин", "🇦🇪 АМА", "🇲🇾 Малайзия"],
    "en": ["🇺🇸 USA", "🇹🇷 Turkey", "🇨🇳 China", "🇦🇪 UAE", "🇲🇾 Malaysia"],
    "zh": ["🇺🇸 美国", "🇹🇷 土耳其", "🇨🇳 中国", "🇦🇪 阿联酋", "🇲🇾 马来西亚"]
}

COUNTRY_CANON = {
    "🇺🇸 Америка": "USA",
    "🇹🇷 Турция": "Turkey",
    "🇨🇳 Китай": "China",
    "🇦🇪 ОАЭ": "UAE",
    "🇲🇾 Малайзия": "Malaysia",
    "🇺🇸 Амрико": "USA",
    "🇹🇷 Туркия": "Turkey",
    "🇨🇳 Чин": "China",
    "🇦🇪 АМА": "UAE",
    "🇺🇸 USA": "USA",
    "🇹🇷 Turkey": "Turkey",
    "🇨🇳 China": "China",
    "🇦🇪 UAE": "UAE",
    "🇲🇾 Malaysia": "Malaysia",
    "🇺🇸 美国": "USA",
    "🇹🇷 土耳其": "Turkey",
    "🇨🇳 中国": "China",
    "🇦🇪 阿联酋": "UAE",
    "🇲🇾 马来西亚": "Malaysia"
}

LEVELS = {
    "ru": ["🏫 Школа", "🎓 Колледж", "🎓 Бакалавр", "🎓 Магистр", "📚 Другое"],
    "tj": ["🏫 Мактаб", "🎓 Коллеҷ", "🎓 Бакалавр", "🎓 Магистр", "📚 Дигар"],
    "en": ["🏫 School", "🎓 College", "🎓 Bachelor", "🎓 Master", "📚 Other"],
    "zh": ["🏫 学校", "🎓 学院", "🎓 本科", "🎓 硕士", "📚 其他"]
}

LEVEL_CANON = {
    "🏫 Школа": "School",
    "🏫 Мактаб": "School",
    "🏫 School": "School",
    "🏫 学校": "School",
    "🎓 Колледж": "College",
    "🎓 College": "College",
    "🎓 学院": "College",
    "🎓 Бакалавр": "Bachelor",
    "🎓 Bachelor": "Bachelor",
    "🎓 本科": "Bachelor",
    "🎓 Магистр": "Master",
    "🎓 Master": "Master",
    "🎓 硕士": "Master",
    "📚 Другое": "Other",
    "📚 Дигар": "Other",
    "📚 Other": "Other",
    "📚 其他": "Other"
}

GPA_OPTIONS = {
    "ru": ["⭐ Очень высокий", "👍 Хороший", "👌 Средний", "⚠️ Низкий"],
    "tj": ["⭐ Хеле баланд", "👍 Хуб", "👌 Миёна", "⚠️ Паст"],
    "en": ["⭐ Very high", "👍 Good", "👌 Average", "⚠️ Low"],
    "zh": ["⭐ 很高", "👍 良好", "👌 一般", "⚠️ 较低"]
}

GPA_CANON = {
    "⭐ Очень высокий": "high",
    "👍 Хороший": "good",
    "👌 Средний": "average",
    "⚠️ Низкий": "low",
    "⭐ Хеле баланд": "high",
    "👍 Хуб": "good",
    "👌 Миёна": "average",
    "⚠️ Паст": "low",
    "⭐ Very high": "high",
    "👍 Good": "good",
    "👌 Average": "average",
    "⚠️ Low": "low",
    "⭐ 很高": "high",
    "👍 良好": "good",
    "👌 一般": "average",
    "⚠️ 较低": "low"
}

EXAMS = {
    "ru": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 Нет экзамена"],
    "tj": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 Имтиҳон нест"],
    "en": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 No exam"],
    "zh": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 没有考试"]
}

EXAM_CANON = {
    "📘 IELTS/TOEFL": "IELTS/TOEFL",
    "📕 HSK": "HSK",
    "📗 SAT": "SAT",
    "📙 Нет экзамена": "None",
    "📙 Имтиҳон нест": "None",
    "📙 No exam": "None",
    "📙 没有考试": "None"
}

BUDGET_OPTIONS = {
    "ru": ["💸 Низкий", "💰 Средний", "💎 Высокий"],
    "tj": ["💸 Паст", "💰 Миёна", "💎 Баланд"],
    "en": ["💸 Low", "💰 Medium", "💎 High"],
    "zh": ["💸 低", "💰 中", "💎 高"]
}

BUDGET_CANON = {
    "💸 Низкий": "low",
    "💰 Средний": "medium",
    "💎 Высокий": "high",
    "💸 Паст": "low",
    "💰 Миёна": "medium",
    "💎 Баланд": "high",
    "💸 Low": "low",
    "💰 Medium": "medium",
    "💎 High": "high",
    "💸 低": "low",
    "💰 中": "medium",
    "💎 高": "high"
}

MAJORS = {
    "ru": ["💻 IT", "💼 Бизнес", "⚕️ Медицина", "⚙️ Инженерия", "🎨 Дизайн", "📚 Другое"],
    "tj": ["💻 IT", "💼 Бизнес", "⚕️ Тиб", "⚙️ Муҳандисӣ", "🎨 Дизайн", "📚 Дигар"],
    "en": ["💻 IT", "💼 Business", "⚕️ Medicine", "⚙️ Engineering", "🎨 Design", "📚 Other"],
    "zh": ["💻 IT", "💼 商科", "⚕️ 医学", "⚙️ 工程", "🎨 设计", "📚 其他"]
}

MAJOR_CANON = {
    "💻 IT": "IT",
    "💼 Бизнес": "Business",
    "💼 Business": "Business",
    "💼 商科": "Business",
    "⚕️ Медицина": "Medicine",
    "⚕️ Тиб": "Medicine",
    "⚕️ Medicine": "Medicine",
    "⚕️ 医学": "Medicine",
    "⚙️ Инженерия": "Engineering",
    "⚙️ Муҳандисӣ": "Engineering",
    "⚙️ Engineering": "Engineering",
    "⚙️ 工程": "Engineering",
    "🎨 Дизайн": "Design",
    "🎨 Design": "Design",
    "🎨 设计": "Design",
    "📚 Другое": "Other",
    "📚 Дигар": "Other",
    "📚 Other": "Other",
    "📚 其他": "Other"
}

YESNO = {
    "ru": ["✅ Да", "❌ Нет"],
    "tj": ["✅ Ҳа", "❌ Не"],
    "en": ["✅ Yes", "❌ No"],
    "zh": ["✅ 是", "❌ 否"]
}

YESNO_CANON = {
    "✅ Да": True,
    "❌ Нет": False,
    "✅ Ҳа": True,
    "❌ Не": False,
    "✅ Yes": True,
    "❌ No": False,
    "✅ 是": True,
    "❌ 否": False
}

UNIVERSITIES = {
    "USA": {
        "IT": ["Massachusetts Institute of Technology", "Stanford University", "Carnegie Mellon University"],
        "Business": ["University of Pennsylvania", "New York University", "Boston University"],
        "Medicine": ["Johns Hopkins University", "Harvard University", "University of California San Diego"],
        "Engineering": ["MIT", "Purdue University", "Texas A&M University"],
        "Design": ["Parsons School of Design", "Rhode Island School of Design", "Pratt Institute"],
        "Other": ["Arizona State University", "University of South Florida", "Oregon State University"]
    },
    "Turkey": {
        "IT": ["Middle East Technical University", "Istanbul Technical University", "Bilkent University"],
        "Business": ["Koç University", "Sabancı University", "Bilkent University"],
        "Medicine": ["Hacettepe University", "Istanbul University", "Ankara University"],
        "Engineering": ["Middle East Technical University", "Istanbul Technical University", "Yildiz Technical University"],
        "Design": ["Mimar Sinan Fine Arts University", "Istanbul Bilgi University", "Yeditepe University"],
        "Other": ["Ankara University", "Ege University", "Marmara University"]
    },
    "China": {
        "IT": ["Tsinghua University", "Peking University", "Zhejiang University"],
        "Business": ["Fudan University", "Shanghai Jiao Tong University", "Renmin University of China"],
        "Medicine": ["Peking University Health Science Center", "Fudan University", "Sun Yat-sen University"],
        "Engineering": ["Tsinghua University", "Harbin Institute of Technology", "Tongji University"],
        "Design": ["Tongji University", "China Academy of Art", "Tsinghua University"],
        "Other": ["Wuhan University", "Nanjing University", "Xiamen University"]
    },
    "UAE": {
        "IT": ["Khalifa University", "University of Sharjah", "American University of Sharjah"],
        "Business": ["American University in Dubai", "University of Dubai", "Abu Dhabi University"],
        "Medicine": ["UAE University", "Gulf Medical University", "Mohammed Bin Rashid University"],
        "Engineering": ["Khalifa University", "American University of Sharjah", "University of Sharjah"],
        "Design": ["American University in Dubai", "University of Sharjah", "Abu Dhabi University"],
        "Other": ["Zayed University", "Ajman University", "Abu Dhabi University"]
    },
    "Malaysia": {
        "IT": ["University of Malaya", "Universiti Teknologi Malaysia", "Asia Pacific University"],
        "Business": ["Taylor's University", "Sunway University", "University of Malaya"],
        "Medicine": ["Monash University Malaysia", "Universiti Malaya", "International Medical University"],
        "Engineering": ["Universiti Teknologi Malaysia", "Universiti Sains Malaysia", "University of Malaya"],
        "Design": ["Taylor's University", "Limkokwing University", "UCSI University"],
        "Other": ["Universiti Kebangsaan Malaysia", "UCSI University", "Sunway University"]
    }
}

DEADLINES = {
    "USA": "November–January",
    "Turkey": "May–August",
    "China": "January–April",
    "UAE": "February–August",
    "Malaysia": "Flexible, often January–August"
}

DOCS_BASE = ["passport", "education_doc", "transcript", "photo", "language_certificate", "cv", "motivation_letter"]

TXT = {
    "lang_offer": {
        "ru": "👋 Добро пожаловать!\n\nЯ помогу тебе пройти путь от выбора страны до подачи заявки в университет.\n\n🌐 Пожалуйста, выбери удобный язык общения:",
        "tj": "👋 Хуш омадед!\n\nМан ба шумо кӯмак мекунам, ки аз интихоби давлат то супоридани ариза ба донишгоҳ расед.\n\n🌐 Лутфан забони муносибро интихоб кунед:",
        "en": "👋 Welcome!\n\nI will help you go from choosing a country to submitting your university application.\n\n🌐 Please choose your preferred language:",
        "zh": "👋 欢迎！\n\n我会帮助你从选择国家一直走到提交大学申请。\n\n🌐 请选择你方便的语言："
    },
    "language_selected": {
        "ru": "✅ Язык успешно изменён на русский.",
        "tj": "✅ Забон ба тоҷикӣ иваз карда шуд.",
        "en": "✅ Language has been changed to English.",
        "zh": "✅ 语言已切换为中文。"
    },
    "instruction_title": {
        "ru": "📘 Инструкция",
        "tj": "📘 Дастур",
        "en": "📘 Guide",
        "zh": "📘 使用说明"
    },
    "instruction_body": {
        "ru": "1️⃣ Сначала выбери язык.\n2️⃣ Нажми «🎓 Начать путь».\n3️⃣ Отвечай на вопросы кнопками.\n4️⃣ Получи персональный план поступления.\n5️⃣ Открой «🏫 Подбор вузов», чтобы увидеть подходящие университеты.\n6️⃣ Открой «🗂 Документы», чтобы следить за готовностью документов.\n7️⃣ Открой «🧭 Дорожная карта», чтобы понимать следующий шаг.\n8️⃣ Если у тебя сложный вопрос — используй «🤖 AI-консультант».\n9️⃣ В любой момент можешь открыть «👤 Мой профиль» или «🌐 Сменить язык».",
        "tj": "1️⃣ Аввал забонро интихоб кунед.\n2️⃣ «🎓 Оғози роҳ»-ро пахш кунед.\n3️⃣ Ба саволҳо бо тугмаҳо ҷавоб диҳед.\n4️⃣ Нақшаи шахсии дохилшавӣ гиред.\n5️⃣ «🏫 Интихоби донишгоҳҳо»-ро кушоед, то донишгоҳҳои мувофиқро бинед.\n6️⃣ «🗂 Ҳуҷҷатҳо»-ро кушоед, то омодагии ҳуҷҷатҳоро бинед.\n7️⃣ «🧭 Нақшаи роҳ»-ро кушоед, то қадами навбатиро фаҳмед.\n8️⃣ Агар саволи душвор дошта бошед — «🤖 Маслиҳатчии AI»-ро истифода баред.\n9️⃣ Ҳар вақт метавонед «👤 Профили ман» ё «🌐 Ивази забон»-ро кушоед.",
        "en": "1️⃣ First choose your language.\n2️⃣ Press “🎓 Start journey”.\n3️⃣ Answer the questions using buttons.\n4️⃣ Get your personal admission plan.\n5️⃣ Open “🏫 University matches” to see suitable universities.\n6️⃣ Open “🗂 Documents” to track your document readiness.\n7️⃣ Open “🧭 Roadmap” to understand your next step.\n8️⃣ If you have a difficult question, use “🤖 AI consultant”.\n9️⃣ At any time you can open “👤 My profile” or “🌐 Change language”.",
        "zh": "1️⃣ 先选择语言。\n2️⃣ 点击“🎓 开始申请之路”。\n3️⃣ 用按钮回答问题。\n4️⃣ 获得你的个性化申请计划。\n5️⃣ 打开“🏫 匹配大学”查看适合你的学校。\n6️⃣ 打开“🗂 文件”跟踪材料准备情况。\n7️⃣ 打开“🧭 路线图”了解下一步该做什么。\n8️⃣ 如果你有复杂问题，请使用“🤖 AI顾问”。\n9️⃣ 任何时候都可以打开“👤 我的资料”或“🌐 切换语言”。"
    },
    "after_lang": {
        "ru": "🎉 Отлично!\n\nТеперь бот полностью будет говорить с тобой на выбранном языке.\n\nЯ советую сначала открыть инструкцию, а потом начать путь поступления.",
        "tj": "🎉 Олиҷаноб!\n\nАкнун бот пурра бо шумо бо забони интихобшуда сӯҳбат мекунад.\n\nПешниҳод мекунам аввал дастурро бинед, баъд роҳро оғоз кунед。",
        "en": "🎉 Great!\n\nFrom now on the bot will fully communicate in your selected language.\n\nI recommend reading the guide first, then starting your admission journey.",
        "zh": "🎉 太好了！\n\n从现在开始，机器人将完全使用你选择的语言与你交流。\n\n我建议先阅读说明，然后开始申请之路。"
    },
    "main_menu_title": {
        "ru": "🏠 Главное меню\n\nВыбери нужный раздел:",
        "tj": "🏠 Менюи асосӣ\n\nҚисмати лозимаро интихоб кунед:",
        "en": "🏠 Main menu\n\nChoose the section you need:",
        "zh": "🏠 主菜单\n\n请选择你需要的功能："
    },
    "select_country": {
        "ru": "🌍 Выбери страну, в которой ты хочешь учиться:",
        "tj": "🌍 Давлатеро интихоб кунед, ки мехоҳед дар он таҳсил кунед:",
        "en": "🌍 Choose the country where you want to study:",
        "zh": "🌍 请选择你想留学的国家："
    },
    "select_level": {
        "ru": "🎓 Выбери свой текущий уровень образования:",
        "tj": "🎓 Сатҳи ҳозираи таҳсилатонро интихоб кунед:",
        "en": "🎓 Choose your current education level:",
        "zh": "🎓 请选择你当前的学历水平："
    },
    "ask_gpa": {
        "ru": "📊 Выбери свой уровень среднего балла:",
        "tj": "📊 Сатҳи баҳои миёнаро интихоб кунед:",
        "en": "📊 Choose your GPA level:",
        "zh": "📊 请选择你的平均成绩水平："
    },
    "select_exam": {
        "ru": "📝 Выбери экзамен или сертификат, который у тебя уже есть:",
        "tj": "📝 Имтиҳон ё сертификате, ки доред, интихоб кунед:",
        "en": "📝 Choose the exam or certificate you already have:",
        "zh": "📝 请选择你已经拥有的考试或证书："
    },
    "ask_budget": {
        "ru": "💰 Выбери свой примерный бюджет на обучение:",
        "tj": "💰 Буҷаи тахминии худро барои таҳсил интихоб кунед:",
        "en": "💰 Choose your approximate education budget:",
        "zh": "💰 请选择你的大概留学预算："
    },
    "select_major": {
        "ru": "📚 Выбери интересующее направление:",
        "tj": "📚 Самти ҷолибро интихоб кунед:",
        "en": "📚 Choose your preferred field:",
        "zh": "📚 请选择你感兴趣的专业方向："
    },
    "ask_scholarship": {
        "ru": "🎁 Тебя интересует стипендия или грант?",
        "tj": "🎁 Оё шуморо стипендия ё грант ҷолиб мекунад?",
        "en": "🎁 Are you interested in a scholarship or grant?",
        "zh": "🎁 你是否希望申请奖学金或资助？"
    },
    "profile_saved": {
        "ru": "✅ Твой профиль сохранён.\n\nТеперь я могу подобрать университеты, показать план действий и помочь тебе двигаться дальше.",
        "tj": "✅ Профили шумо нигоҳ дошта шуд.\n\nҲоло ман метавонам донишгоҳҳоро интихоб кунам, нақша нишон диҳам ва барои қадамҳои баъдӣ кӯмак расонам。",
        "en": "✅ Your profile has been saved.\n\nNow I can match universities, show your plan, and help you move forward.",
        "zh": "✅ 你的资料已保存。\n\n现在我可以为你匹配大学、显示路线图，并帮助你继续下一步。"
    },
    "profile_incomplete": {
        "ru": "⚠️ Сначала заполни профиль через «🎓 Начать путь», чтобы бот мог давать точные рекомендации.",
        "tj": "⚠️ Аввал профилро тавассути «🎓 Оғози роҳ» пур кунед, то бот тавсияҳои дақиқ диҳад。",
        "en": "⚠️ First complete your profile through “🎓 Start journey” so the bot can give accurate recommendations.",
        "zh": "⚠️ 请先通过“🎓 开始申请之路”完成资料，这样机器人才能给出准确建议。"
    },
    "universities_title": {
        "ru": "🏫 Подходящие университеты",
        "tj": "🏫 Донишгоҳҳои мувофиқ",
        "en": "🏫 Suitable universities",
        "zh": "🏫 适合你的大学"
    },
    "roadmap_title": {
        "ru": "🧭 Дорожная карта поступления",
        "tj": "🧭 Нақшаи роҳ барои дохилшавӣ",
        "en": "🧭 Admission roadmap",
        "zh": "🧭 申请路线图"
    },
    "documents_title": {
        "ru": "🗂 Контроль документов",
        "tj": "🗂 Назорати ҳуҷҷатҳо",
        "en": "🗂 Document control",
        "zh": "🗂 文件管理"
    },
    "deadlines_title": {
        "ru": "⏰ Примерные дедлайны",
        "tj": "⏰ Мӯҳлатҳои тахминӣ",
        "en": "⏰ Approximate deadlines",
        "zh": "⏰ 大致截止时间"
    },
    "progress_title": {
        "ru": "📈 Прогресс поступления",
        "tj": "📈 Пешрафти дохилшавӣ",
        "en": "📈 Admission progress",
        "zh": "📈 申请进度"
    },
    "ai_intro": {
        "ru": "🤖 AI-консультант готов.\n\nНапиши свой вопрос одним сообщением.",
        "tj": "🤖 Маслиҳатчии AI омода аст.\n\nСаволи худро дар як паём нависед.",
        "en": "🤖 The AI consultant is ready.\n\nSend your question in one message.",
        "zh": "🤖 AI顾问已准备好。\n\n请直接发送你的问题。"
    },
    "ai_reply_error": {
        "ru": "⚠️ Сейчас AI временно не ответил. Попробуй ещё раз чуть позже.",
        "tj": "⚠️ Ҳоло AI муваққатан ҷавоб надод. Каме баъдтар боз кӯшиш кунед。",
        "en": "⚠️ The AI did not reply this time. Please try again a bit later.",
        "zh": "⚠️ AI 这次暂时没有回复，请稍后再试。"
    },
    "motivation_ready": {
        "ru": "✍️ Ниже — черновик мотивационного письма на основе твоего профиля:",
        "tj": "✍️ Дар поён — намунаи мактуби ангеза дар асоси профили шумо:",
        "en": "✍️ Below is a draft motivation letter based on your profile:",
        "zh": "✍️ 以下是根据你的资料生成的动机信草稿："
    },
    "back_to_menu": {
        "ru": "⬅️ Возвращаю в главное меню.",
        "tj": "⬅️ Ба менюи асосӣ бармегардем。",
        "en": "⬅️ Returning to the main menu.",
        "zh": "⬅️ 正在返回主菜单。"
    },
    "thinking": {
        "ru": "⏳ Думаю над ответом...",
        "tj": "⏳ Ҷавобро омода карда истодаам...",
        "en": "⏳ Thinking about the answer...",
        "zh": "⏳ 正在思考你的问题..."
    },
    "cancelled": {
        "ru": "✅ Действие отменено. Возвращаю в главное меню.",
        "tj": "✅ Амал бекор карда шуд. Ба менюи асосӣ бармегардем。",
        "en": "✅ Action cancelled. Returning to the main menu.",
        "zh": "✅ 操作已取消。正在返回主菜单。"
    }
}

BUTTONS = {
    "ru": {
        "instruction": "📘 Инструкция",
        "start_journey": "🎓 Начать путь",
        "my_profile": "👤 Мой профиль",
        "universities": "🏫 Подбор вузов",
        "roadmap": "🧭 Дорожная карта",
        "documents": "🗂 Документы",
        "deadlines": "⏰ Дедлайны",
        "progress": "📈 Прогресс",
        "ai": "🤖 AI-консультант",
        "motivation": "✍️ Мотивационное письмо",
        "change_language": "🌐 Сменить язык",
        "back": "⬅️ Назад",
        "menu": "🏠 Главное меню",
        "reset_docs": "♻️ Сбросить документы"
    },
    "tj": {
        "instruction": "📘 Дастур",
        "start_journey": "🎓 Оғози роҳ",
        "my_profile": "👤 Профили ман",
        "universities": "🏫 Интихоби донишгоҳҳо",
        "roadmap": "🧭 Нақшаи роҳ",
        "documents": "🗂 Ҳуҷҷатҳо",
        "deadlines": "⏰ Мӯҳлатҳо",
        "progress": "📈 Пешрафт",
        "ai": "🤖 Маслиҳатчии AI",
        "motivation": "✍️ Мактуби ангеза",
        "change_language": "🌐 Ивази забон",
        "back": "⬅️ Бозгашт",
        "menu": "🏠 Менюи асосӣ",
        "reset_docs": "♻️ Аз нав оғоз кардан"
    },
    "en": {
        "instruction": "📘 Guide",
        "start_journey": "🎓 Start journey",
        "my_profile": "👤 My profile",
        "universities": "🏫 University matches",
        "roadmap": "🧭 Roadmap",
        "documents": "🗂 Documents",
        "deadlines": "⏰ Deadlines",
        "progress": "📈 Progress",
        "ai": "🤖 AI consultant",
        "motivation": "✍️ Motivation letter",
        "change_language": "🌐 Change language",
        "back": "⬅️ Back",
        "menu": "🏠 Main menu",
        "reset_docs": "♻️ Reset documents"
    },
    "zh": {
        "instruction": "📘 使用说明",
        "start_journey": "🎓 开始申请之路",
        "my_profile": "👤 我的资料",
        "universities": "🏫 匹配大学",
        "roadmap": "🧭 路线图",
        "documents": "🗂 文件",
        "deadlines": "⏰ 截止时间",
        "progress": "📈 进度",
        "ai": "🤖 AI顾问",
        "motivation": "✍️ 动机信",
        "change_language": "🌐 切换语言",
        "back": "⬅️ 返回",
        "menu": "🏠 主菜单",
        "reset_docs": "♻️ 重置文件"
    }
}

DOC_LABELS = {
    "passport": {"ru": "Паспорт", "tj": "Шиноснома", "en": "Passport", "zh": "护照"},
    "education_doc": {"ru": "Документ об образовании", "tj": "Ҳуҷҷати таҳсил", "en": "Education document", "zh": "学历文件"},
    "transcript": {"ru": "Табель / транскрипт", "tj": "Баҳонома / транскрипт", "en": "Transcript", "zh": "成绩单"},
    "photo": {"ru": "Фото", "tj": "Сурат", "en": "Photo", "zh": "照片"},
    "language_certificate": {"ru": "Языковой сертификат", "tj": "Сертификати забон", "en": "Language certificate", "zh": "语言证书"},
    "cv": {"ru": "CV / Resume", "tj": "CV / Resume", "en": "CV / Resume", "zh": "简历"},
    "motivation_letter": {"ru": "Мотивационное письмо", "tj": "Мактуби ангеза", "en": "Motivation letter", "zh": "动机信"}
}

class LanguageState(StatesGroup):
    choosing = State()

class OnboardingState(StatesGroup):
    country = State()
    level = State()
    gpa = State()
    exam = State()
    budget = State()
    major = State()
    scholarship = State()

class AIState(StatesGroup):
    asking = State()

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL)")
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT data FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return {
                "lang": None,
                "profile": {},
                "docs": {k: False for k in DOCS_BASE},
                "progress": {"profile_done": False, "applied": False, "accepted": False, "visa": False}
            }
        return json.loads(row[0])

async def save_user(user_id: int, data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO users (user_id, data) VALUES (?, ?)", (user_id, json.dumps(data, ensure_ascii=False)))
        await db.commit()

def tr(lang, key):
    return TXT[key][lang]

def b(lang, key):
    return BUTTONS[lang][key]

def make_kb(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True
    )

def lang_keyboard():
    return make_kb([
        ["🇹🇯 Тоҷикӣ", "🇷🇺 Русский"],
        ["🇬🇧 English", "🇨🇳 中文"]
    ])

def intro_keyboard(lang):
    return make_kb([
        [b(lang, "instruction")],
        [b(lang, "start_journey")],
        [b(lang, "menu")]
    ])

def main_menu(lang):
    return make_kb([
        [b(lang, "start_journey"), b(lang, "my_profile")],
        [b(lang, "universities"), b(lang, "roadmap")],
        [b(lang, "documents"), b(lang, "deadlines")],
        [b(lang, "progress"), b(lang, "motivation")],
        [b(lang, "ai")],
        [b(lang, "change_language")]
    ])

def back_menu(lang):
    return make_kb([[b(lang, "back")], [b(lang, "menu")]])

def countries_keyboard(lang):
    opts = COUNTRIES[lang]
    return make_kb([
        [opts[0], opts[1]],
        [opts[2], opts[3]],
        [opts[4]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def levels_keyboard(lang):
    opts = LEVELS[lang]
    return make_kb([
        [opts[0], opts[1]],
        [opts[2], opts[3]],
        [opts[4]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def gpa_keyboard(lang):
    opts = GPA_OPTIONS[lang]
    return make_kb([
        [opts[0], opts[1]],
        [opts[2], opts[3]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def exam_keyboard(lang):
    opts = EXAMS[lang]
    return make_kb([
        [opts[0], opts[1]],
        [opts[2], opts[3]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def budget_keyboard(lang):
    opts = BUDGET_OPTIONS[lang]
    return make_kb([
        [opts[0], opts[1], opts[2]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def major_keyboard(lang):
    opts = MAJORS[lang]
    return make_kb([
        [opts[0], opts[1]],
        [opts[2], opts[3]],
        [opts[4], opts[5]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def yesno_keyboard(lang):
    opts = YESNO[lang]
    return make_kb([
        [opts[0], opts[1]],
        [b(lang, "back"), b(lang, "menu")]
    ])

def docs_keyboard(lang):
    return make_kb([
        [DOC_LABELS["passport"][lang], DOC_LABELS["education_doc"][lang]],
        [DOC_LABELS["transcript"][lang], DOC_LABELS["photo"][lang]],
        [DOC_LABELS["language_certificate"][lang], DOC_LABELS["cv"][lang]],
        [DOC_LABELS["motivation_letter"][lang]],
        [b(lang, "reset_docs")],
        [b(lang, "back"), b(lang, "menu")]
    ])

def detect_lang_choice(text):
    mapping = {
        "🇹🇯 Тоҷикӣ": "tj",
        "🇷🇺 Русский": "ru",
        "🇬🇧 English": "en",
        "🇨🇳 中文": "zh"
    }
    return mapping.get(text)

def score_profile(profile):
    score = 0
    if profile.get("country"):
        score += 15
    if profile.get("level"):
        score += 10
    if profile.get("gpa") == "high":
        score += 25
    elif profile.get("gpa") == "good":
        score += 20
    elif profile.get("gpa") == "average":
        score += 12
    elif profile.get("gpa") == "low":
        score += 5
    if profile.get("exam") and profile.get("exam") != "None":
        score += 20
    if profile.get("budget") == "high":
        score += 15
    elif profile.get("budget") == "medium":
        score += 10
    elif profile.get("budget") == "low":
        score += 5
    if profile.get("scholarship") is True:
        score += 5
    if profile.get("major"):
        score += 10
    return min(score, 100)

def profile_complete(profile):
    return all(k in profile for k in ["country", "level", "gpa", "exam", "budget", "major", "scholarship"])

def roadmap_text(lang, profile):
    country = profile.get("country", "—")
    exam = profile.get("exam", "—")
    scholarship = profile.get("scholarship")
    scholarship_text = {
        "ru": "Да" if scholarship else "Нет",
        "tj": "Ҳа" if scholarship else "Не",
        "en": "Yes" if scholarship else "No",
        "zh": "是" if scholarship else "否"
    } if scholarship is not None else {"ru": "—", "tj": "—", "en": "—", "zh": "—"}
    if lang == "ru":
        return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Заполни профиль полностью.\n2️⃣ Подбери 3–5 университетов в стране: {country}.\n3️⃣ Проверь требования выбранных вузов.\n4️⃣ Подготовь документы.\n5️⃣ Сдай или подтверди экзамен: {exam}.\n6️⃣ Подготовь мотивационное письмо и CV.\n7️⃣ Подай заявку в университет.\n8️⃣ Если нужен грант: {scholarship_text[lang]} — подготовь отдельные документы на стипендию.\n9️⃣ После получения ответа подготовь визу и финальные бумаги.\n🔟 После зачисления следуй инструкциям университета。"
    if lang == "tj":
        return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Профилро пурра пур кунед.\n2️⃣ Дар давлати {country} 3–5 донишгоҳ интихоб кунед.\n3️⃣ Талаботи донишгоҳҳоро санҷед.\n4️⃣ Ҳуҷҷатҳоро омода кунед.\n5️⃣ Имтиҳонро супоред ё тасдиқ кунед: {exam}.\n6️⃣ Мактуби ангеза ва CV омода кунед.\n7️⃣ Аризаро ба донишгоҳ фиристед.\n8️⃣ Агар грант хоҳед: {scholarship_text[lang]} — ҳуҷҷатҳои иловагӣ омода кунед.\n9️⃣ Баъди гирифтани ҷавоб, барои виза ва ҳуҷҷатҳои охирин омода шавед.\n🔟 Баъди қабул, дастурҳои донишгоҳро иҷро кунед。"
    if lang == "en":
        return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Complete your profile.\n2️⃣ Choose 3–5 universities in {country}.\n3️⃣ Check the admission requirements.\n4️⃣ Prepare your documents.\n5️⃣ Take or confirm your exam: {exam}.\n6️⃣ Prepare your motivation letter and CV.\n7️⃣ Submit your applications.\n8️⃣ Scholarship needed: {scholarship_text[lang]} — prepare extra scholarship materials.\n9️⃣ After receiving results, prepare visa documents.\n🔟 After enrollment, follow the university instructions."
    return f"{tr(lang,'roadmap_title')}\n\n1️⃣ 完成你的资料。\n2️⃣ 在 {country} 选择 3–5 所大学。\n3️⃣ 查看大学申请要求。\n4️⃣ 准备文件。\n5️⃣ 参加或确认考试：{exam}。\n6️⃣ 准备动机信和简历。\n7️⃣ 提交大学申请。\n8️⃣ 是否需要奖学金：{scholarship_text[lang]} — 如需要，请准备额外奖学金材料。\n9️⃣ 收到结果后准备签证文件。\n🔟 被录取后按照学校要求完成后续步骤。"

def universities_text(lang, profile):
    country = profile.get("country")
    major = profile.get("major")
    if not country or not major:
        return None
    items = UNIVERSITIES.get(country, {}).get(major, UNIVERSITIES.get(country, {}).get("Other", []))
    if lang == "ru":
        return f"{tr(lang,'universities_title')}\n\nСтрана: {country}\nНаправление: {major}\n\n" + "\n".join(f"• {x}" for x in items)
    if lang == "tj":
        return f"{tr(lang,'universities_title')}\n\nДавлат: {country}\nСамт: {major}\n\n" + "\n".join(f"• {x}" for x in items)
    if lang == "en":
        return f"{tr(lang,'universities_title')}\n\nCountry: {country}\nField: {major}\n\n" + "\n".join(f"• {x}" for x in items)
    return f"{tr(lang,'universities_title')}\n\n国家：{country}\n专业方向：{major}\n\n" + "\n".join(f"• {x}" for x in items)

def deadlines_text(lang, profile):
    country = profile.get("country", "USA")
    d = DEADLINES.get(country, "—")
    if lang == "ru":
        return f"{tr(lang,'deadlines_title')}\n\nДля страны {country} ориентируйся на такой период подачи:\n• {d}\n\n⚠️ Это примерный диапазон. Перед реальной подачей всегда проверяй дедлайн на сайте конкретного университета."
    if lang == "tj":
        return f"{tr(lang,'deadlines_title')}\n\nБарои давлати {country} одатан муҳлати супоридан чунин аст:\n• {d}\n\n⚠️ Ин мӯҳлати тахминӣ аст. Пеш аз супоридани ариза ҳатман муҳлати расмиро дар сайти донишгоҳ санҷед."
    if lang == "en":
        return f"{tr(lang,'deadlines_title')}\n\nFor {country}, the application period is usually around:\n• {d}\n\n⚠️ This is an approximate range. Always check the official deadline on the university website."
    return f"{tr(lang,'deadlines_title')}\n\n对于 {country}，申请时间通常大致为：\n• {d}\n\n⚠️ 这只是大致范围，正式申请前请务必查看大学官网的官方截止日期。"

def docs_text(lang, docs):
    lines = [tr(lang, "documents_title"), ""]
    for key in DOCS_BASE:
        status = "✅" if docs.get(key) else "❌"
        lines.append(f"{status} {DOC_LABELS[key][lang]}")
    return "\n".join(lines)

def progress_text(lang, user):
    docs = user["docs"]
    p = user["progress"]
    done_docs = sum(1 for x in docs.values() if x)
    total_docs = len(docs)
    profile_done = "✅" if p.get("profile_done") else "❌"
    applied = "✅" if p.get("applied") else "❌"
    accepted = "✅" if p.get("accepted") else "❌"
    visa = "✅" if p.get("visa") else "❌"
    if lang == "ru":
        return f"{tr(lang,'progress_title')}\n\n{profile_done} Профиль заполнен\n✅ Документов готово: {done_docs}/{total_docs}\n{applied} Заявка подана\n{accepted} Есть зачисление\n{visa} Виза готова"
    if lang == "tj":
        return f"{tr(lang,'progress_title')}\n\n{profile_done} Профил пур шудааст\n✅ Ҳуҷҷатҳои тайёр: {done_docs}/{total_docs}\n{applied} Ариза фиристода шудааст\n{accepted} Қабул ҳаст\n{visa} Виза омода аст"
    if lang == "en":
        return f"{tr(lang,'progress_title')}\n\n{profile_done} Profile completed\n✅ Documents ready: {done_docs}/{total_docs}\n{applied} Application submitted\n{accepted} Admission received\n{visa} Visa ready"
    return f"{tr(lang,'progress_title')}\n\n{profile_done} 资料已完成\n✅ 已准备文件：{done_docs}/{total_docs}\n{applied} 已提交申请\n{accepted} 已获得录取\n{visa} 签证已准备"

async def ai_answer(lang, user, question):
    profile = user["profile"]
    system_prompts = {
        "ru": "Ты профессиональный и вежливый консультант по поступлению за границу. Отвечай очень понятно, пошагово и без лишней воды. Пиши на русском языке.",
        "tj": "Ту мушовири касбӣ ва хушмуомила оид ба дохилшавӣ ба донишгоҳҳои хориҷӣ ҳастӣ. Равшан, қадам ба қадам ва фаҳмо ҷавоб деҳ. Ба забони тоҷикӣ навис.",
        "en": "You are a professional and polite study abroad admissions consultant. Answer clearly, step by step, in simple language. Write in English.",
        "zh": "你是一位专业且礼貌的留学申请顾问。请用简单、清晰、分步骤的方式回答。请用中文回答。"
    }
    try:
        resp = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": system_prompts[lang]},
                {"role": "user", "content": f"User profile: {json.dumps(profile, ensure_ascii=False)}\nQuestion: {question}"}
            ],
            temperature=0.7,
            max_tokens=900
        )
        if not resp or not resp.choices:
            return TXT["ai_reply_error"][lang]
        content = resp.choices[0].message.content
        if not content:
            return TXT["ai_reply_error"][lang]
        return content.strip()
    except Exception as e:
        return f"⚠️ AI error:\n{e}"

async def ai_motivation(lang, user):
    profile = user["profile"]
    prompts = {
        "ru": f"Напиши сильный, аккуратный и понятный черновик мотивационного письма для поступления в университет. Профиль: {json.dumps(profile, ensure_ascii=False)}. Пиши по-русски.",
        "tj": f"Бар асоси ин профил як матни хуб ва фаҳмои мактуби ангеза барои дохилшавӣ ба донишгоҳ навис. Профил: {json.dumps(profile, ensure_ascii=False)}. Ба тоҷикӣ навис.",
        "en": f"Write a strong, clear, realistic motivation letter draft for university admission. Profile: {json.dumps(profile, ensure_ascii=False)}. Write in English.",
        "zh": f"请根据以下资料写一封清晰、自然、有说服力的大学申请动机信草稿。资料：{json.dumps(profile, ensure_ascii=False)}。请用中文写。"
    }
    try:
        resp = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": "Write polished, realistic, beginner-friendly motivation letters."},
                {"role": "user", "content": prompts[lang]}
            ],
            temperature=0.8,
            max_tokens=1200
        )
        if not resp or not resp.choices:
            return TXT["ai_reply_error"][lang]
        content = resp.choices[0].message.content
        if not content:
            return TXT["ai_reply_error"][lang]
        return content.strip()
    except Exception as e:
        return f"⚠️ AI error:\n{e}"

async def show_main_menu(message: Message, lang: str):
    await message.answer(tr(lang, "main_menu_title"), reply_markup=main_menu(lang))

async def show_intro(message: Message, lang: str):
    await message.answer(TXT["after_lang"][lang], reply_markup=intro_keyboard(lang))

async def reset_to_main(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(tr(lang, "back_to_menu"), reply_markup=main_menu(lang))

@dp.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user.get("lang") or "en"
    await state.clear()
    await message.answer(TXT["cancelled"][lang], reply_markup=main_menu(lang) if user.get("lang") else lang_keyboard())

@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    await save_user(message.from_user.id, user)
    text = (
        f"{TXT['lang_offer']['ru']}\n\n"
        f"{TXT['lang_offer']['tj']}\n\n"
        f"{TXT['lang_offer']['en']}\n\n"
        f"{TXT['lang_offer']['zh']}"
    )
    await message.answer(text, reply_markup=lang_keyboard())
    await state.set_state(LanguageState.choosing)

@dp.message(LanguageState.choosing)
async def choose_language(message: Message, state: FSMContext):
    lang = detect_lang_choice(message.text)
    if not lang:
        await message.answer("🇹🇯 Тоҷикӣ / 🇷🇺 Русский / 🇬🇧 English / 🇨🇳 中文", reply_markup=lang_keyboard())
        return
    user = await get_user(message.from_user.id)
    user["lang"] = lang
    await save_user(message.from_user.id, user)
    await state.clear()
    await message.answer(TXT["language_selected"][lang], reply_markup=ReplyKeyboardRemove())
    await show_intro(message, lang)

@dp.message(F.text.in_(["🇹🇯 Тоҷикӣ", "🇷🇺 Русский", "🇬🇧 English", "🇨🇳 中文"]))
async def change_language_global(message: Message, state: FSMContext):
    lang = detect_lang_choice(message.text)
    if not lang:
        return
    user = await get_user(message.from_user.id)
    user["lang"] = lang
    await save_user(message.from_user.id, user)
    await state.clear()
    await message.answer(TXT["language_selected"][lang], reply_markup=ReplyKeyboardRemove())
    await show_intro(message, lang)

@dp.message(OnboardingState.country)
async def onboarding_country(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in COUNTRIES[lang]:
        await message.answer(tr(lang, "select_country"), reply_markup=countries_keyboard(lang))
        return
    user["profile"]["country"] = COUNTRY_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.level)
    await message.answer(tr(lang, "select_level"), reply_markup=levels_keyboard(lang))

@dp.message(OnboardingState.level)
async def onboarding_level(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in LEVELS[lang]:
        await message.answer(tr(lang, "select_level"), reply_markup=levels_keyboard(lang))
        return
    user["profile"]["level"] = LEVEL_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.gpa)
    await message.answer(tr(lang, "ask_gpa"), reply_markup=gpa_keyboard(lang))

@dp.message(OnboardingState.gpa)
async def onboarding_gpa(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in GPA_OPTIONS[lang]:
        await message.answer(tr(lang, "ask_gpa"), reply_markup=gpa_keyboard(lang))
        return
    user["profile"]["gpa"] = GPA_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.exam)
    await message.answer(tr(lang, "select_exam"), reply_markup=exam_keyboard(lang))

@dp.message(OnboardingState.exam)
async def onboarding_exam(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in EXAMS[lang]:
        await message.answer(tr(lang, "select_exam"), reply_markup=exam_keyboard(lang))
        return
    user["profile"]["exam"] = EXAM_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.budget)
    await message.answer(tr(lang, "ask_budget"), reply_markup=budget_keyboard(lang))

@dp.message(OnboardingState.budget)
async def onboarding_budget(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in BUDGET_OPTIONS[lang]:
        await message.answer(tr(lang, "ask_budget"), reply_markup=budget_keyboard(lang))
        return
    user["profile"]["budget"] = BUDGET_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.major)
    await message.answer(tr(lang, "select_major"), reply_markup=major_keyboard(lang))

@dp.message(OnboardingState.major)
async def onboarding_major(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in MAJORS[lang]:
        await message.answer(tr(lang, "select_major"), reply_markup=major_keyboard(lang))
        return
    user["profile"]["major"] = MAJOR_CANON[message.text]
    await save_user(message.from_user.id, user)
    await state.set_state(OnboardingState.scholarship)
    await message.answer(tr(lang, "ask_scholarship"), reply_markup=yesno_keyboard(lang))

@dp.message(OnboardingState.scholarship)
async def onboarding_scholarship(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in YESNO[lang]:
        await message.answer(tr(lang, "ask_scholarship"), reply_markup=yesno_keyboard(lang))
        return
    user["profile"]["scholarship"] = YESNO_CANON[message.text]
    user["progress"]["profile_done"] = True
    await save_user(message.from_user.id, user)
    await state.clear()
    await message.answer(tr(lang, "profile_saved"), reply_markup=main_menu(lang))
    await message.answer(roadmap_text(lang, user["profile"]), reply_markup=main_menu(lang))

@dp.message(AIState.asking)
async def ai_chat_handler(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    await message.answer(tr(lang, "thinking"), reply_markup=back_menu(lang))
    answer = await ai_answer(lang, user, message.text)
    await message.answer(answer, reply_markup=back_menu(lang))

@dp.message(StateFilter(None))
async def main_menu_router(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user.get("lang")

    if not lang:
        text = (
            f"{TXT['lang_offer']['ru']}\n\n"
            f"{TXT['lang_offer']['tj']}\n\n"
            f"{TXT['lang_offer']['en']}\n\n"
            f"{TXT['lang_offer']['zh']}"
        )
        await message.answer(text, reply_markup=lang_keyboard())
        await state.set_state(LanguageState.choosing)
        return

    if message.text == b(lang, "instruction"):
        await message.answer(f"{tr(lang,'instruction_title')}\n\n{tr(lang,'instruction_body')}", reply_markup=intro_keyboard(lang))
        return

    if message.text == b(lang, "menu"):
        await show_main_menu(message, lang)
        return

    if message.text == b(lang, "change_language"):
        text = (
            f"{TXT['lang_offer']['ru']}\n\n"
            f"{TXT['lang_offer']['tj']}\n\n"
            f"{TXT['lang_offer']['en']}\n\n"
            f"{TXT['lang_offer']['zh']}"
        )
        await message.answer(text, reply_markup=lang_keyboard())
        await state.set_state(LanguageState.choosing)
        return

    if message.text == b(lang, "start_journey"):
        await state.clear()
        await state.set_state(OnboardingState.country)
        await message.answer(tr(lang, "select_country"), reply_markup=countries_keyboard(lang))
        return

    if message.text == b(lang, "my_profile"):
        profile = user["profile"]
        if not profile_complete(profile):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang))
            return
        score = score_profile(profile)
        if lang == "ru":
            txt = f"👤 Твой профиль\n\n🌍 Страна: {profile.get('country')}\n🎓 Уровень: {profile.get('level')}\n📊 Балл: {profile.get('gpa')}\n📝 Экзамен: {profile.get('exam')}\n💰 Бюджет: {profile.get('budget')}\n📚 Направление: {profile.get('major')}\n🎁 Грант: {'Да' if profile.get('scholarship') else 'Нет'}\n\n⭐ Общая оценка профиля: {score}/100"
        elif lang == "tj":
            txt = f"👤 Профили шумо\n\n🌍 Давлат: {profile.get('country')}\n🎓 Сатҳ: {profile.get('level')}\n📊 Баҳо: {profile.get('gpa')}\n📝 Имтиҳон: {profile.get('exam')}\n💰 Буҷет: {profile.get('budget')}\n📚 Самт: {profile.get('major')}\n🎁 Грант: {'Ҳа' if profile.get('scholarship') else 'Не'}\n\n⭐ Арзёбии умумии профил: {score}/100"
        elif lang == "en":
            txt = f"👤 Your profile\n\n🌍 Country: {profile.get('country')}\n🎓 Level: {profile.get('level')}\n📊 GPA level: {profile.get('gpa')}\n📝 Exam: {profile.get('exam')}\n💰 Budget: {profile.get('budget')}\n📚 Field: {profile.get('major')}\n🎁 Scholarship: {'Yes' if profile.get('scholarship') else 'No'}\n\n⭐ Overall profile score: {score}/100"
        else:
            txt = f"👤 你的资料\n\n🌍 国家：{profile.get('country')}\n🎓 学历：{profile.get('level')}\n📊 成绩水平：{profile.get('gpa')}\n📝 考试：{profile.get('exam')}\n💰 预算：{profile.get('budget')}\n📚 专业方向：{profile.get('major')}\n🎁 奖学金：{'是' if profile.get('scholarship') else '否'}\n\n⭐ 综合评分：{score}/100"
        await message.answer(txt, reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "universities"):
        if not profile_complete(user["profile"]):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang))
            return
        txt = universities_text(lang, user["profile"])
        await message.answer(txt, reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "roadmap"):
        if not profile_complete(user["profile"]):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang))
            return
        await message.answer(roadmap_text(lang, user["profile"]), reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "deadlines"):
        if not profile_complete(user["profile"]):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang))
            return
        await message.answer(deadlines_text(lang, user["profile"]), reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "progress"):
        await message.answer(progress_text(lang, user), reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "documents"):
        await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang))
        return

    if message.text == b(lang, "reset_docs"):
        user["docs"] = {k: False for k in DOCS_BASE}
        await save_user(message.from_user.id, user)
        await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang))
        return

    doc_names = [DOC_LABELS[k][lang] for k in DOCS_BASE]
    if message.text in doc_names:
        for k in DOCS_BASE:
            if message.text == DOC_LABELS[k][lang]:
                user["docs"][k] = not user["docs"][k]
                break
        await save_user(message.from_user.id, user)
        await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang))
        return

    if message.text == b(lang, "motivation"):
        if not profile_complete(user["profile"]):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang))
            return
        await message.answer(tr(lang, "thinking"), reply_markup=main_menu(lang))
        letter = await ai_motivation(lang, user)
        await message.answer(f"{tr(lang,'motivation_ready')}\n\n{letter}", reply_markup=main_menu(lang))
        return

    if message.text == b(lang, "ai"):
        await state.clear()
        await state.set_state(AIState.asking)
        await message.answer(tr(lang, "ai_intro"), reply_markup=back_menu(lang))
        return

    if message.text == b(lang, "back"):
        await show_main_menu(message, lang)
        return

    await show_main_menu(message, lang)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
