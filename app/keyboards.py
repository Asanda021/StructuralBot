from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗 پروژه جدید", callback_data="new_project"), InlineKeyboardButton("📂 پروژه‌ها", callback_data="projects"), InlineKeyboardButton("📊 آخرین برآورد", callback_data="reports")],
        [InlineKeyboardButton("🧱 مقادیر بتن", callback_data="takeoff_concrete"), InlineKeyboardButton("🪵 مقادیر قالب", callback_data="takeoff_formwork"), InlineKeyboardButton("🔩 مقادیر میلگرد", callback_data="takeoff_rebar")],
        [InlineKeyboardButton("💰 برآورد ریالی", callback_data="pricing"), InlineKeyboardButton("📄 گزارش و خروجی", callback_data="exports"), InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])

def cancel_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")]])

def back_home():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")]])

def report_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data="edit_project"), InlineKeyboardButton("🔄 بازخوانی برآورد", callback_data="recalc_project")],
        [InlineKeyboardButton("📄 گزارش و خروجی", callback_data="exports"), InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
    ])

def review_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأیید و محاسبه نهایی", callback_data="confirm_project")],
        [InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data="edit_current"), InlineKeyboardButton("↩️ مرحله قبل", callback_data="previous_step")],
        [InlineKeyboardButton("❌ لغو", callback_data="home")],
    ])
