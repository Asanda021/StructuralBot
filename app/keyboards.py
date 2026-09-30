from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗 پروژه‌های من", callback_data="projects"),
         InlineKeyboardButton("📐 محاسبات سازه", callback_data="calc")],
        [InlineKeyboardButton("🧮 برآورد مصالح", callback_data="quantity"),
         InlineKeyboardButton("🔩 میلگرد / BBS", callback_data="rebar")],
        [InlineKeyboardButton("📊 گزارش آخرین محاسبه", callback_data="reports"),
         InlineKeyboardButton("📚 آیین‌نامه‌ها", callback_data="codes")],
        [InlineKeyboardButton("🤖 دستیار هوشمند", callback_data="ai"),
         InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])

def calc_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧱 پی", callback_data="foundation"),
         InlineKeyboardButton("🏢 ستون", callback_data="column")],
        [InlineKeyboardButton("📏 تیر", callback_data="beam"),
         InlineKeyboardButton("⬜ سقف", callback_data="slab")],
        [InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")],
    ])

def rebar_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 معادل‌سازی قطر", callback_data="rebar_eq")],
        [InlineKeyboardButton("📋 BBS / Cut List", callback_data="bbs")],
        [InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")],
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")]])
