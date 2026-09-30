from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗 پروژه جدید", callback_data="new_project"),
         InlineKeyboardButton("📂 پروژه‌های من", callback_data="projects")],
        [InlineKeyboardButton("🧱 متره بتن", callback_data="takeoff_concrete"),
         InlineKeyboardButton("🔩 متره میلگرد", callback_data="takeoff_rebar")],
        [InlineKeyboardButton("🪵 متره قالب‌بندی", callback_data="takeoff_formwork"),
         InlineKeyboardButton("💰 برآورد ریالی", callback_data="pricing")],
        [InlineKeyboardButton("📊 گزارش پروژه", callback_data="reports"),
         InlineKeyboardButton("📄 خروجی", callback_data="exports")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
         InlineKeyboardButton("❓ راهنما", callback_data="help")],
    ])

def project_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗 شروع متره ساختمان بتنی", callback_data="new_project")],
        [InlineKeyboardButton("📂 پروژه‌های من", callback_data="projects")],
        [InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")],
    ])

def cancel_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="home")]])

def back_home():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")]])

def report_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش پروژه", callback_data="edit_project")],
        [InlineKeyboardButton("🔄 محاسبه مجدد", callback_data="recalc_project")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
    ])
