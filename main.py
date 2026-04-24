import asyncio
import json
import logging
import os
from pathlib import Path

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free").strip()
DB = os.getenv("DATABASE_PATH", "unihelper.db")
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is empty. Add BOT_TOKEN in Railway Variables.")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

client = None
if OPENROUTER_API_KEY:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://railway.app", "X-OpenRouter-Title": "UniHelper"},
        timeout=45.0,
    )

COUNTRIES = {
    "ru": ["🇺🇸 Америка", "🇹🇷 Турция", "🇨🇳 Китай", "🇦🇪 ОАЭ", "🇲🇾 Малайзия"],
    "tj": ["🇺🇸 Амрико", "🇹🇷 Туркия", "🇨🇳 Чин", "🇦🇪 АМА", "🇲🇾 Малайзия"],
    "en": ["🇺🇸 USA", "🇹🇷 Turkey", "🇨🇳 China", "🇦🇪 UAE", "🇲🇾 Malaysia"],
    "zh": ["🇺🇸 美国", "🇹🇷 土耳其", "🇨🇳 中国", "🇦🇪 阿联酋", "🇲🇾 马来西亚"],
}

COUNTRY_CANON = {
    "🇺🇸 Америка": "USA", "🇹🇷 Турция": "Turkey", "🇨🇳 Китай": "China", "🇦🇪 ОАЭ": "UAE", "🇲🇾 Малайзия": "Malaysia",
    "🇺🇸 Амрико": "USA", "🇹🇷 Туркия": "Turkey", "🇨🇳 Чин": "China", "🇦🇪 АМА": "UAE",
    "🇺🇸 USA": "USA", "🇹🇷 Turkey": "Turkey", "🇨🇳 China": "China", "🇦🇪 UAE": "UAE", "🇲🇾 Malaysia": "Malaysia",
    "🇺🇸 美国": "USA", "🇹🇷 土耳其": "Turkey", "🇨🇳 中国": "China", "🇦🇪 阿联酋": "UAE", "🇲🇾 马来西亚": "Malaysia",
}

LEVELS = {
    "ru": ["🏫 Школа", "🎓 Колледж", "🎓 Бакалавр", "🎓 Магистр", "📚 Другое"],
    "tj": ["🏫 Мактаб", "🎓 Коллеҷ", "🎓 Бакалавр", "🎓 Магистр", "📚 Дигар"],
    "en": ["🏫 School", "🎓 College", "🎓 Bachelor", "🎓 Master", "📚 Other"],
    "zh": ["🏫 学校", "🎓 学院", "🎓 本科", "🎓 硕士", "📚 其他"],
}

LEVEL_CANON = {
    "🏫 Школа": "School", "🏫 Мактаб": "School", "🏫 School": "School", "🏫 学校": "School",
    "🎓 Колледж": "College", "🎓 Коллеҷ": "College", "🎓 College": "College", "🎓 学院": "College",
    "🎓 Бакалавр": "Bachelor", "🎓 Bachelor": "Bachelor", "🎓 本科": "Bachelor",
    "🎓 Магистр": "Master", "🎓 Master": "Master", "🎓 硕士": "Master",
    "📚 Другое": "Other", "📚 Дигар": "Other", "📚 Other": "Other", "📚 其他": "Other",
}

GPA_OPTIONS = {
    "ru": ["⭐ Очень высокий", "👍 Хороший", "👌 Средний", "⚠️ Низкий"],
    "tj": ["⭐ Хеле баланд", "👍 Хуб", "👌 Миёна", "⚠️ Паст"],
    "en": ["⭐ Very high", "👍 Good", "👌 Average", "⚠️ Low"],
    "zh": ["⭐ 很高", "👍 良好", "👌 一般", "⚠️ 较低"],
}

GPA_CANON = {
    "⭐ Очень высокий": "high", "👍 Хороший": "good", "👌 Средний": "average", "⚠️ Низкий": "low",
    "⭐ Хеле баланд": "high", "👍 Хуб": "good", "👌 Миёна": "average", "⚠️ Паст": "low",
    "⭐ Very high": "high", "👍 Good": "good", "👌 Average": "average", "⚠️ Low": "low",
    "⭐ 很高": "high", "👍 良好": "good", "👌 一般": "average", "⚠️ 较低": "low",
}

EXAMS = {
    "ru": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 Нет экзамена"],
    "tj": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 Имтиҳон нест"],
    "en": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 No exam"],
    "zh": ["📘 IELTS/TOEFL", "📕 HSK", "📗 SAT", "📙 没有考试"],
}

EXAM_CANON = {"📘 IELTS/TOEFL": "IELTS/TOEFL", "📕 HSK": "HSK", "📗 SAT": "SAT", "📙 Нет экзамена": "None", "📙 Имтиҳон нест": "None", "📙 No exam": "None", "📙 没有考试": "None"}

BUDGET_OPTIONS = {
    "ru": ["💸 Низкий", "💰 Средний", "💎 Высокий"],
    "tj": ["💸 Паст", "💰 Миёна", "💎 Баланд"],
    "en": ["💸 Low", "💰 Medium", "💎 High"],
    "zh": ["💸 低", "💰 中", "💎 高"],
}

BUDGET_CANON = {"💸 Низкий": "low", "💰 Средний": "medium", "💎 Высокий": "high", "💸 Паст": "low", "💰 Миёна": "medium", "💎 Баланд": "high", "💸 Low": "low", "💰 Medium": "medium", "💎 High": "high", "💸 低": "low", "💰 中": "medium", "💎 高": "high"}

MAJORS = {
    "ru": ["💻 IT", "💼 Бизнес", "⚕️ Медицина", "⚙️ Инженерия", "🎨 Дизайн", "📚 Другое"],
    "tj": ["💻 IT", "💼 Бизнес", "⚕️ Тиб", "⚙️ Муҳандисӣ", "🎨 Дизайн", "📚 Дигар"],
    "en": ["💻 IT", "💼 Business", "⚕️ Medicine", "⚙️ Engineering", "🎨 Design", "📚 Other"],
    "zh": ["💻 IT", "💼 商科", "⚕️ 医学", "⚙️ 工程", "🎨 设计", "📚 其他"],
}

MAJOR_CANON = {
    "💻 IT": "IT", "💼 Бизнес": "Business", "💼 Business": "Business", "💼 商科": "Business",
    "⚕️ Медицина": "Medicine", "⚕️ Тиб": "Medicine", "⚕️ Medicine": "Medicine", "⚕️ 医学": "Medicine",
    "⚙️ Инженерия": "Engineering", "⚙️ Муҳандисӣ": "Engineering", "⚙️ Engineering": "Engineering", "⚙️ 工程": "Engineering",
    "🎨 Дизайн": "Design", "🎨 Design": "Design", "🎨 设计": "Design",
    "📚 Другое": "Other", "📚 Дигар": "Other", "📚 Other": "Other", "📚 其他": "Other",
}

YESNO = {"ru": ["✅ Да", "❌ Нет"], "tj": ["✅ Ҳа", "❌ Не"], "en": ["✅ Yes", "❌ No"], "zh": ["✅ 是", "❌ 否"]}
YESNO_CANON = {"✅ Да": True, "❌ Нет": False, "✅ Ҳа": True, "❌ Не": False, "✅ Yes": True, "❌ No": False, "✅ 是": True, "❌ 否": False}

UNIVERSITIES = {
    "USA": {"IT": ["MIT", "Stanford University", "Carnegie Mellon University", "Georgia Tech", "UC Berkeley"], "Business": ["University of Pennsylvania", "NYU", "Boston University", "University of Michigan"], "Medicine": ["Johns Hopkins University", "Harvard University", "UC San Diego"], "Engineering": ["MIT", "Purdue University", "Texas A&M", "Georgia Tech"], "Design": ["Parsons School of Design", "Rhode Island School of Design", "Pratt Institute"], "Other": ["Arizona State University", "University of South Florida", "Oregon State University"]},
    "Turkey": {"IT": ["METU", "Istanbul Technical University", "Bilkent University", "Sabancı University"], "Business": ["Koç University", "Sabancı University", "Bilkent University"], "Medicine": ["Hacettepe University", "Istanbul University", "Ankara University"], "Engineering": ["METU", "Istanbul Technical University", "Yildiz Technical University"], "Design": ["Mimar Sinan Fine Arts University", "Istanbul Bilgi University", "Yeditepe University"], "Other": ["Ankara University", "Ege University", "Marmara University"]},
    "China": {"IT": ["Tsinghua University", "Peking University", "Zhejiang University", "Shanghai Jiao Tong University"], "Business": ["Fudan University", "Shanghai Jiao Tong University", "Renmin University of China"], "Medicine": ["Peking University Health Science Center", "Fudan University", "Sun Yat-sen University"], "Engineering": ["Tsinghua University", "Harbin Institute of Technology", "Tongji University"], "Design": ["Tongji University", "China Academy of Art", "Tsinghua University"], "Other": ["Wuhan University", "Nanjing University", "Xiamen University"]},
    "UAE": {"IT": ["Khalifa University", "University of Sharjah", "American University of Sharjah"], "Business": ["American University in Dubai", "University of Dubai", "Abu Dhabi University"], "Medicine": ["UAE University", "Gulf Medical University", "Mohammed Bin Rashid University"], "Engineering": ["Khalifa University", "American University of Sharjah", "University of Sharjah"], "Design": ["American University in Dubai", "University of Sharjah", "Abu Dhabi University"], "Other": ["Zayed University", "Ajman University", "Abu Dhabi University"]},
    "Malaysia": {"IT": ["University of Malaya", "Universiti Teknologi Malaysia", "Asia Pacific University"], "Business": ["Taylor's University", "Sunway University", "University of Malaya"], "Medicine": ["Monash University Malaysia", "Universiti Malaya", "International Medical University"], "Engineering": ["Universiti Teknologi Malaysia", "Universiti Sains Malaysia", "University of Malaya"], "Design": ["Taylor's University", "Limkokwing University", "UCSI University"], "Other": ["Universiti Kebangsaan Malaysia", "UCSI University", "Sunway University"]},
}

DEADLINES = {"USA": "November–January", "Turkey": "May–August", "China": "January–April", "UAE": "February–August", "Malaysia": "Flexible, often January–August"}
DOCS_BASE = ["passport", "education_doc", "transcript", "photo", "language_certificate", "cv", "motivation_letter"]

TXT = {
    "lang_offer": {"ru": "👋 Добро пожаловать!\n\nЯ помогу выбрать страну, университеты, документы и шаги для поступления.\n\n🌐 Выбери язык:", "tj": "👋 Хуш омадед!\n\nМан ба шумо барои интихоби давлат, донишгоҳҳо, ҳуҷҷатҳо ва қадамҳои дохилшавӣ кӯмак мекунам.\n\n🌐 Забонро интихоб кунед:", "en": "👋 Welcome!\n\nI will help you choose a country, universities, documents and admission steps.\n\n🌐 Choose your language:", "zh": "👋 欢迎！\n\n我会帮助你选择国家、大学、材料和申请步骤。\n\n🌐 请选择语言："},
    "language_selected": {"ru": "✅ Язык изменён на русский.", "tj": "✅ Забон ба тоҷикӣ иваз карда шуд.", "en": "✅ Language changed to English.", "zh": "✅ 语言已切换为中文。"},
    "after_lang": {"ru": "🎉 Отлично! Советую сначала открыть инструкцию, а потом начать путь поступления.", "tj": "🎉 Олиҷаноб! Аввал дастурро кушоед, баъд роҳро оғоз кунед.", "en": "🎉 Great! I recommend opening the guide first, then starting your journey.", "zh": "🎉 很好！建议先阅读说明，然后开始申请之路。"},
    "instruction_title": {"ru": "📘 Инструкция", "tj": "📘 Дастур", "en": "📘 Guide", "zh": "📘 使用说明"},
    "instruction_body": {"ru": "1️⃣ Нажми «🎓 Начать путь».\n2️⃣ Ответь на вопросы кнопками.\n3️⃣ Получи персональный план.\n4️⃣ Открой подбор вузов, документы и дедлайны.\n5️⃣ Задавай сложные вопросы AI-консультанту.\n6️⃣ В любой момент можно сменить язык.", "tj": "1️⃣ «🎓 Оғози роҳ»-ро пахш кунед.\n2️⃣ Бо тугмаҳо ҷавоб диҳед.\n3️⃣ Нақшаи шахсӣ гиред.\n4️⃣ Донишгоҳҳо, ҳуҷҷатҳо ва муҳлатҳоро бинед.\n5️⃣ Саволҳои душворро ба AI диҳед.\n6️⃣ Ҳар вақт забонро иваз кардан мумкин аст.", "en": "1️⃣ Press “🎓 Start journey”.\n2️⃣ Answer with buttons.\n3️⃣ Get a personal plan.\n4️⃣ Open universities, documents and deadlines.\n5️⃣ Ask hard questions to the AI consultant.\n6️⃣ You can change language anytime.", "zh": "1️⃣ 点击“🎓 开始申请之路”。\n2️⃣ 用按钮回答问题。\n3️⃣ 获得个人计划。\n4️⃣ 查看大学、文件和截止时间。\n5️⃣ 向AI顾问提问复杂问题。\n6️⃣ 可随时切换语言。"},
    "main_menu_title": {"ru": "🏠 Главное меню\n\nВыбери раздел:", "tj": "🏠 Менюи асосӣ\n\nҚисматро интихоб кунед:", "en": "🏠 Main menu\n\nChoose a section:", "zh": "🏠 主菜单\n\n请选择功能："},
    "select_country": {"ru": "🌍 Где хочешь учиться?", "tj": "🌍 Дар куҷо таҳсил кардан мехоҳед?", "en": "🌍 Where do you want to study?", "zh": "🌍 你想去哪里留学？"},
    "select_level": {"ru": "🎓 Твой текущий уровень образования:", "tj": "🎓 Сатҳи таҳсилатон:", "en": "🎓 Your current education level:", "zh": "🎓 你的当前学历："},
    "ask_gpa": {"ru": "📊 Какой у тебя средний балл?", "tj": "📊 Баҳои миёнаи шумо чӣ гуна аст?", "en": "📊 What is your GPA level?", "zh": "📊 你的成绩水平如何？"},
    "select_exam": {"ru": "📝 Какой экзамен/сертификат уже есть?", "tj": "📝 Кадом имтиҳон/сертификат доред?", "en": "📝 Which exam/certificate do you already have?", "zh": "📝 你已有哪个考试/证书？"},
    "ask_budget": {"ru": "💰 Примерный бюджет на обучение:", "tj": "💰 Буҷаи тахминии таҳсил:", "en": "💰 Approximate study budget:", "zh": "💰 大概留学预算："},
    "select_major": {"ru": "📚 Какое направление интересно?", "tj": "📚 Кадом соҳа ҷолиб аст?", "en": "📚 Preferred field:", "zh": "📚 感兴趣的专业方向："},
    "ask_scholarship": {"ru": "🎁 Хочешь стипендию/грант?", "tj": "🎁 Стипендия/грант мехоҳед?", "en": "🎁 Do you want a scholarship/grant?", "zh": "🎁 你想申请奖学金吗？"},
    "profile_saved": {"ru": "✅ Профиль сохранён. Теперь я могу подобрать вузы и план действий.", "tj": "✅ Профил нигоҳ дошта шуд. Акнун метавонам донишгоҳҳо ва нақшаро нишон диҳам.", "en": "✅ Profile saved. Now I can match universities and show your plan.", "zh": "✅ 资料已保存。现在我可以匹配大学并显示计划。"},
    "profile_incomplete": {"ru": "⚠️ Сначала заполни профиль через «🎓 Начать путь».", "tj": "⚠️ Аввал профилро бо «🎓 Оғози роҳ» пур кунед.", "en": "⚠️ First complete your profile through “🎓 Start journey”.", "zh": "⚠️ 请先通过“🎓 开始申请之路”完成资料。"},
    "universities_title": {"ru": "🏫 Подходящие университеты", "tj": "🏫 Донишгоҳҳои мувофиқ", "en": "🏫 Suitable universities", "zh": "🏫 适合你的大学"},
    "roadmap_title": {"ru": "🧭 Дорожная карта", "tj": "🧭 Нақшаи роҳ", "en": "🧭 Roadmap", "zh": "🧭 路线图"},
    "documents_title": {"ru": "🗂 Документы", "tj": "🗂 Ҳуҷҷатҳо", "en": "🗂 Documents", "zh": "🗂 文件"},
    "deadlines_title": {"ru": "⏰ Дедлайны", "tj": "⏰ Мӯҳлатҳо", "en": "⏰ Deadlines", "zh": "⏰ 截止时间"},
    "progress_title": {"ru": "📈 Прогресс", "tj": "📈 Пешрафт", "en": "📈 Progress", "zh": "📈 进度"},
    "ai_intro": {"ru": "🤖 AI-консультант готов. Напиши вопрос одним сообщением.", "tj": "🤖 AI омода аст. Саволро дар як паём нависед.", "en": "🤖 AI consultant is ready. Send one question.", "zh": "🤖 AI顾问已准备好。请发送一个问题。"},
    "ai_reply_error": {"ru": "⚠️ AI сейчас недоступен. Проверь OPENROUTER_API_KEY или попробуй позже.", "tj": "⚠️ AI ҳоло дастрас нест. OPENROUTER_API_KEY-ро санҷед ё баъдтар кӯшиш кунед.", "en": "⚠️ AI is unavailable. Check OPENROUTER_API_KEY or try later.", "zh": "⚠️ AI暂时不可用。请检查OPENROUTER_API_KEY或稍后再试。"},
    "thinking": {"ru": "⏳ Думаю...", "tj": "⏳ Фикр мекунам...", "en": "⏳ Thinking...", "zh": "⏳ 思考中..."},
    "back_to_menu": {"ru": "⬅️ Возвращаю в главное меню.", "tj": "⬅️ Ба менюи асосӣ бармегардем.", "en": "⬅️ Returning to the main menu.", "zh": "⬅️ 返回主菜单。"},
    "cancelled": {"ru": "✅ Отменено.", "tj": "✅ Бекор шуд.", "en": "✅ Cancelled.", "zh": "✅ 已取消。"},
    "motivation_ready": {"ru": "✍️ Черновик мотивационного письма:", "tj": "✍️ Нусхаи мактуби ангеза:", "en": "✍️ Motivation letter draft:", "zh": "✍️ 动机信草稿："},
}

BUTTONS = {
    "ru": {"instruction": "📘 Инструкция", "start_journey": "🎓 Начать путь", "my_profile": "👤 Мой профиль", "universities": "🏫 Подбор вузов", "roadmap": "🧭 Дорожная карта", "documents": "🗂 Документы", "deadlines": "⏰ Дедлайны", "progress": "📈 Прогресс", "ai": "🤖 AI-консультант", "motivation": "✍️ Мотивационное письмо", "change_language": "🌐 Сменить язык", "back": "⬅️ Назад", "menu": "🏠 Главное меню", "reset_docs": "♻️ Сбросить документы"},
    "tj": {"instruction": "📘 Дастур", "start_journey": "🎓 Оғози роҳ", "my_profile": "👤 Профили ман", "universities": "🏫 Интихоби донишгоҳҳо", "roadmap": "🧭 Нақшаи роҳ", "documents": "🗂 Ҳуҷҷатҳо", "deadlines": "⏰ Мӯҳлатҳо", "progress": "📈 Пешрафт", "ai": "🤖 Маслиҳатчии AI", "motivation": "✍️ Мактуби ангеза", "change_language": "🌐 Ивази забон", "back": "⬅️ Бозгашт", "menu": "🏠 Менюи асосӣ", "reset_docs": "♻️ Аз нав оғоз кардан"},
    "en": {"instruction": "📘 Guide", "start_journey": "🎓 Start journey", "my_profile": "👤 My profile", "universities": "🏫 University matches", "roadmap": "🧭 Roadmap", "documents": "🗂 Documents", "deadlines": "⏰ Deadlines", "progress": "📈 Progress", "ai": "🤖 AI consultant", "motivation": "✍️ Motivation letter", "change_language": "🌐 Change language", "back": "⬅️ Back", "menu": "🏠 Main menu", "reset_docs": "♻️ Reset documents"},
    "zh": {"instruction": "📘 使用说明", "start_journey": "🎓 开始申请之路", "my_profile": "👤 我的资料", "universities": "🏫 匹配大学", "roadmap": "🧭 路线图", "documents": "🗂 文件", "deadlines": "⏰ 截止时间", "progress": "📈 进度", "ai": "🤖 AI顾问", "motivation": "✍️ 动机信", "change_language": "🌐 切换语言", "back": "⬅️ 返回", "menu": "🏠 主菜单", "reset_docs": "♻️ 重置文件"},
}

DOC_LABELS = {
    "passport": {"ru": "Паспорт", "tj": "Шиноснома", "en": "Passport", "zh": "护照"},
    "education_doc": {"ru": "Документ об образовании", "tj": "Ҳуҷҷати таҳсил", "en": "Education document", "zh": "学历文件"},
    "transcript": {"ru": "Табель / транскрипт", "tj": "Баҳонома / транскрипт", "en": "Transcript", "zh": "成绩单"},
    "photo": {"ru": "Фото", "tj": "Сурат", "en": "Photo", "zh": "照片"},
    "language_certificate": {"ru": "Языковой сертификат", "tj": "Сертификати забон", "en": "Language certificate", "zh": "语言证书"},
    "cv": {"ru": "CV / Resume", "tj": "CV / Resume", "en": "CV / Resume", "zh": "简历"},
    "motivation_letter": {"ru": "Мотивационное письмо", "tj": "Мактуби ангеза", "en": "Motivation letter", "zh": "动机信"},
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
    Path(DB).parent.mkdir(parents=True, exist_ok=True) if Path(DB).parent != Path(".") else None
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL)")
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT data FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row:
            data = json.loads(row[0])
            data.setdefault("docs", {k: False for k in DOCS_BASE})
            data.setdefault("progress", {"profile_done": False, "applied": False, "accepted": False, "visa": False})
            data.setdefault("profile", {})
            return data
    return {"lang": None, "profile": {}, "docs": {k: False for k in DOCS_BASE}, "progress": {"profile_done": False, "applied": False, "accepted": False, "visa": False}}

async def save_user(user_id, data):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, json.dumps(data, ensure_ascii=False)))
        await db.commit()

def tr(lang, key): return TXT[key][lang]
def b(lang, key): return BUTTONS[lang][key]
def kb(rows): return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=x) for x in row] for row in rows], resize_keyboard=True, input_field_placeholder="Choose an option")
def lang_keyboard(): return kb([["🇹🇯 Тоҷикӣ", "🇷🇺 Русский"], ["🇬🇧 English", "🇨🇳 中文"]])
def intro_keyboard(lang): return kb([[b(lang, "instruction")], [b(lang, "start_journey")], [b(lang, "menu")]])
def main_menu(lang): return kb([[b(lang, "start_journey"), b(lang, "my_profile")], [b(lang, "universities"), b(lang, "roadmap")], [b(lang, "documents"), b(lang, "deadlines")], [b(lang, "progress"), b(lang, "motivation")], [b(lang, "ai")], [b(lang, "change_language")]])
def back_menu(lang): return kb([[b(lang, "back")], [b(lang, "menu")]])
def opt_keyboard(options, lang, two=True):
    rows = [options[i:i + (2 if two else 3)] for i in range(0, len(options), 2 if two else 3)]
    rows.append([b(lang, "back"), b(lang, "menu")])
    return kb(rows)
def countries_keyboard(lang): return opt_keyboard(COUNTRIES[lang], lang)
def levels_keyboard(lang): return opt_keyboard(LEVELS[lang], lang)
def gpa_keyboard(lang): return opt_keyboard(GPA_OPTIONS[lang], lang)
def exam_keyboard(lang): return opt_keyboard(EXAMS[lang], lang)
def budget_keyboard(lang): return opt_keyboard(BUDGET_OPTIONS[lang], lang, False)
def major_keyboard(lang): return opt_keyboard(MAJORS[lang], lang)
def yesno_keyboard(lang): return opt_keyboard(YESNO[lang], lang)
def docs_keyboard(lang): return kb([[DOC_LABELS["passport"][lang], DOC_LABELS["education_doc"][lang]], [DOC_LABELS["transcript"][lang], DOC_LABELS["photo"][lang]], [DOC_LABELS["language_certificate"][lang], DOC_LABELS["cv"][lang]], [DOC_LABELS["motivation_letter"][lang]], [b(lang, "reset_docs")], [b(lang, "back"), b(lang, "menu")]])
def detect_lang_choice(text): return {"🇹🇯 Тоҷикӣ": "tj", "🇷🇺 Русский": "ru", "🇬🇧 English": "en", "🇨🇳 中文": "zh"}.get(text)
def profile_complete(p): return all(k in p for k in ["country", "level", "gpa", "exam", "budget", "major", "scholarship"])

def score_profile(p):
    score = 0
    score += 15 if p.get("country") else 0
    score += 10 if p.get("level") else 0
    score += {"high": 25, "good": 20, "average": 12, "low": 5}.get(p.get("gpa"), 0)
    score += 20 if p.get("exam") and p.get("exam") != "None" else 0
    score += {"high": 15, "medium": 10, "low": 5}.get(p.get("budget"), 0)
    score += 5 if p.get("scholarship") is True else 0
    score += 10 if p.get("major") else 0
    return min(score, 100)

def roadmap_text(lang, p):
    country, exam = p.get("country", "—"), p.get("exam", "—")
    if lang == "ru": return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Выбери 3–5 вузов в стране: <b>{country}</b>.\n2️⃣ Проверь требования каждого вуза.\n3️⃣ Подготовь паспорт, аттестат/диплом, транскрипт, фото, CV и мотивационное письмо.\n4️⃣ Экзамен/сертификат: <b>{exam}</b>.\n5️⃣ Подай заявку до дедлайна.\n6️⃣ После ответа готовь визу и финальные документы."
    if lang == "tj": return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Дар давлати <b>{country}</b> 3–5 донишгоҳ интихоб кунед.\n2️⃣ Талаботҳоро санҷед.\n3️⃣ Ҳуҷҷатҳо, CV ва мактуби ангезаро омода кунед.\n4️⃣ Имтиҳон/сертификат: <b>{exam}</b>.\n5️⃣ Аризаро то муҳлат фиристед.\n6️⃣ Баъд виза ва ҳуҷҷатҳои охиринро омода кунед."
    if lang == "en": return f"{tr(lang,'roadmap_title')}\n\n1️⃣ Pick 3–5 universities in <b>{country}</b>.\n2️⃣ Check each university requirement.\n3️⃣ Prepare passport, education document, transcript, photo, CV and motivation letter.\n4️⃣ Exam/certificate: <b>{exam}</b>.\n5️⃣ Apply before the deadline.\n6️⃣ After results, prepare visa documents."
    return f"{tr(lang,'roadmap_title')}\n\n1️⃣ 在 <b>{country}</b> 选择3–5所大学。\n2️⃣ 检查每所大学要求。\n3️⃣ 准备护照、学历文件、成绩单、照片、简历和动机信。\n4️⃣ 考试/证书：<b>{exam}</b>。\n5️⃣ 截止日期前提交申请。\n6️⃣ 收到结果后准备签证文件。"

def universities_text(lang, p):
    items = UNIVERSITIES.get(p.get("country"), {}).get(p.get("major"), []) or UNIVERSITIES.get(p.get("country"), {}).get("Other", [])
    title = tr(lang, "universities_title")
    return f"{title}\n\n🌍 <b>{p.get('country')}</b>\n📚 <b>{p.get('major')}</b>\n\n" + "\n".join(f"• {x}" for x in items)

def deadlines_text(lang, p):
    return f"{tr(lang,'deadlines_title')}\n\n🌍 {p.get('country')}\n• {DEADLINES.get(p.get('country'), '—')}\n\n⚠️ Always check official university websites before applying."

def docs_text(lang, docs):
    return tr(lang, "documents_title") + "\n\n" + "\n".join(("✅" if docs.get(k) else "❌") + " " + DOC_LABELS[k][lang] for k in DOCS_BASE)

def progress_text(lang, user):
    docs_done = sum(user["docs"].values())
    profile = "✅" if user["progress"].get("profile_done") else "❌"
    return f"{tr(lang,'progress_title')}\n\n{profile} Profile\n✅ Documents: {docs_done}/{len(DOCS_BASE)}\n⭐ Score: {score_profile(user['profile'])}/100"

def profile_text(lang, p):
    score = score_profile(p)
    names = {"ru": ["Твой профиль", "Страна", "Уровень", "Балл", "Экзамен", "Бюджет", "Направление", "Грант", "Да", "Нет", "Оценка"], "tj": ["Профили шумо", "Давлат", "Сатҳ", "Баҳо", "Имтиҳон", "Буҷет", "Самт", "Грант", "Ҳа", "Не", "Арзёбӣ"], "en": ["Your profile", "Country", "Level", "GPA", "Exam", "Budget", "Field", "Scholarship", "Yes", "No", "Score"], "zh": ["你的资料", "国家", "学历", "成绩", "考试", "预算", "专业", "奖学金", "是", "否", "评分"]}[lang]
    return f"👤 <b>{names[0]}</b>\n\n🌍 {names[1]}: {p.get('country')}\n🎓 {names[2]}: {p.get('level')}\n📊 {names[3]}: {p.get('gpa')}\n📝 {names[4]}: {p.get('exam')}\n💰 {names[5]}: {p.get('budget')}\n📚 {names[6]}: {p.get('major')}\n🎁 {names[7]}: {names[8] if p.get('scholarship') else names[9]}\n\n⭐ {names[10]}: {score}/100"

async def ai_answer(lang, user, question, motivation=False):
    if not client:
        return tr(lang, "ai_reply_error")
    profile = json.dumps(user.get("profile", {}), ensure_ascii=False)
    system = {"ru": "Ты опытный консультант по поступлению за границу. Пиши понятно, уверенно, пошагово и без воды на русском.", "tj": "Ту мушовири касбии дохилшавӣ ба хориҷ ҳастӣ. Ба тоҷикӣ, фаҳмо ва қадам ба қадам ҷавоб деҳ.", "en": "You are a professional study abroad consultant. Answer clearly and step by step in English.", "zh": "你是专业留学顾问。请用中文清晰分步骤回答。"}[lang]
    prompt = f"User profile: {profile}\n\nTask: {'Write a strong realistic motivation letter draft.' if motivation else question}"
    try:
        resp = await asyncio.to_thread(client.chat.completions.create, model=OPENROUTER_MODEL, messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}], temperature=0.7, max_tokens=1200)
        content = resp.choices[0].message.content if resp and resp.choices else ""
        return content.strip() if content else tr(lang, "ai_reply_error")
    except Exception as e:
        logging.exception("AI error")
        return f"⚠️ AI error: {e}"

async def send_start_language(message, state):
    await state.clear()
    await message.answer(TXT["lang_offer"]["ru"] + "\n\n" + TXT["lang_offer"]["tj"] + "\n\n" + TXT["lang_offer"]["en"] + "\n\n" + TXT["lang_offer"]["zh"], reply_markup=lang_keyboard())
    await state.set_state(LanguageState.choosing)

async def show_main_menu(message, lang): await message.answer(tr(lang, "main_menu_title"), reply_markup=main_menu(lang))
async def reset_to_main(message, state, lang):
    await state.clear()
    await message.answer(tr(lang, "back_to_menu"), reply_markup=main_menu(lang))

@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await save_user(message.from_user.id, user)
    await send_start_language(message, state)

@dp.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user.get("lang") or "en"
    await state.clear()
    await message.answer(tr(lang, "cancelled"), reply_markup=main_menu(lang) if user.get("lang") else lang_keyboard())

@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        return
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cur.fetchone())[0]
    await message.answer(f"📊 Users: {count}")

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
    await message.answer(tr(lang, "language_selected"), reply_markup=ReplyKeyboardRemove())
    await message.answer(tr(lang, "after_lang"), reply_markup=intro_keyboard(lang))

@dp.message(F.text.in_(["🇹🇯 Тоҷикӣ", "🇷🇺 Русский", "🇬🇧 English", "🇨🇳 中文"]))
async def change_language_global(message: Message, state: FSMContext):
    await choose_language(message, state)

async def next_step(message, state, key, options, canon, next_state, next_text, next_kb):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    if message.text not in options:
        await message.answer(tr(lang, next_text if key == "country" else {"level":"select_level","gpa":"ask_gpa","exam":"select_exam","budget":"ask_budget","major":"select_major","scholarship":"ask_scholarship"}[key]), reply_markup=next_kb(lang) if key == "country" else None)
        return
    user["profile"][key] = canon[message.text]
    if key == "scholarship":
        user["progress"]["profile_done"] = True
    await save_user(message.from_user.id, user)
    await state.set_state(next_state)
    await message.answer(tr(lang, next_text), reply_markup=next_kb(lang))

@dp.message(OnboardingState.country)
async def s_country(message, state): await next_step(message, state, "country", COUNTRIES[(await get_user(message.from_user.id))["lang"]], COUNTRY_CANON, OnboardingState.level, "select_level", levels_keyboard)
@dp.message(OnboardingState.level)
async def s_level(message, state): await next_step(message, state, "level", LEVELS[(await get_user(message.from_user.id))["lang"]], LEVEL_CANON, OnboardingState.gpa, "ask_gpa", gpa_keyboard)
@dp.message(OnboardingState.gpa)
async def s_gpa(message, state): await next_step(message, state, "gpa", GPA_OPTIONS[(await get_user(message.from_user.id))["lang"]], GPA_CANON, OnboardingState.exam, "select_exam", exam_keyboard)
@dp.message(OnboardingState.exam)
async def s_exam(message, state): await next_step(message, state, "exam", EXAMS[(await get_user(message.from_user.id))["lang"]], EXAM_CANON, OnboardingState.budget, "ask_budget", budget_keyboard)
@dp.message(OnboardingState.budget)
async def s_budget(message, state): await next_step(message, state, "budget", BUDGET_OPTIONS[(await get_user(message.from_user.id))["lang"]], BUDGET_CANON, OnboardingState.major, "select_major", major_keyboard)
@dp.message(OnboardingState.major)
async def s_major(message, state): await next_step(message, state, "major", MAJORS[(await get_user(message.from_user.id))["lang"]], MAJOR_CANON, OnboardingState.scholarship, "ask_scholarship", yesno_keyboard)

@dp.message(OnboardingState.scholarship)
async def s_scholarship(message, state):
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
async def ai_handler(message, state):
    user = await get_user(message.from_user.id)
    lang = user["lang"]
    if message.text in [b(lang, "back"), b(lang, "menu")]:
        await reset_to_main(message, state, lang)
        return
    await message.answer(tr(lang, "thinking"), reply_markup=back_menu(lang))
    await message.answer(await ai_answer(lang, user, message.text), reply_markup=back_menu(lang))

@dp.message(StateFilter(None))
async def menu_router(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang = user.get("lang")
    if not lang:
        await send_start_language(message, state)
        return
    text = message.text
    if text == b(lang, "instruction"):
        await message.answer(f"{tr(lang,'instruction_title')}\n\n{tr(lang,'instruction_body')}", reply_markup=intro_keyboard(lang)); return
    if text == b(lang, "menu") or text == b(lang, "back"):
        await show_main_menu(message, lang); return
    if text == b(lang, "change_language"):
        await send_start_language(message, state); return
    if text == b(lang, "start_journey"):
        await state.set_state(OnboardingState.country)
        await message.answer(tr(lang, "select_country"), reply_markup=countries_keyboard(lang)); return
    if text == b(lang, "my_profile"):
        await message.answer(profile_text(lang, user["profile"]) if profile_complete(user["profile"]) else tr(lang, "profile_incomplete"), reply_markup=main_menu(lang)); return
    if text == b(lang, "universities"):
        await message.answer(universities_text(lang, user["profile"]) if profile_complete(user["profile"]) else tr(lang, "profile_incomplete"), reply_markup=main_menu(lang)); return
    if text == b(lang, "roadmap"):
        await message.answer(roadmap_text(lang, user["profile"]) if profile_complete(user["profile"]) else tr(lang, "profile_incomplete"), reply_markup=main_menu(lang)); return
    if text == b(lang, "deadlines"):
        await message.answer(deadlines_text(lang, user["profile"]) if profile_complete(user["profile"]) else tr(lang, "profile_incomplete"), reply_markup=main_menu(lang)); return
    if text == b(lang, "progress"):
        await message.answer(progress_text(lang, user), reply_markup=main_menu(lang)); return
    if text == b(lang, "documents"):
        await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang)); return
    if text == b(lang, "reset_docs"):
        user["docs"] = {k: False for k in DOCS_BASE}
        await save_user(message.from_user.id, user)
        await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang)); return
    for k in DOCS_BASE:
        if text == DOC_LABELS[k][lang]:
            user["docs"][k] = not user["docs"].get(k, False)
            await save_user(message.from_user.id, user)
            await message.answer(docs_text(lang, user["docs"]), reply_markup=docs_keyboard(lang)); return
    if text == b(lang, "motivation"):
        if not profile_complete(user["profile"]):
            await message.answer(tr(lang, "profile_incomplete"), reply_markup=main_menu(lang)); return
        await message.answer(tr(lang, "thinking"), reply_markup=main_menu(lang))
        await message.answer(f"{tr(lang,'motivation_ready')}\n\n{await ai_answer(lang, user, '', True)}", reply_markup=main_menu(lang)); return
    if text == b(lang, "ai"):
        await state.set_state(AIState.asking)
        await message.answer(tr(lang, "ai_intro"), reply_markup=back_menu(lang)); return
    await show_main_menu(message, lang)

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("UniHelper started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
