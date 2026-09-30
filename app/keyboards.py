from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🏗 پروژه جدید",callback_data="new_project"),InlineKeyboardButton("📂 پروژه‌ها",callback_data="projects"),InlineKeyboardButton("📊 آخرین گزارش",callback_data="reports")],
      [InlineKeyboardButton("➕ ادامه متره",callback_data="continue_project"),InlineKeyboardButton("📋 جدول جامع",callback_data="table"),InlineKeyboardButton("📄 خروجی",callback_data="exports")],
      [InlineKeyboardButton("💰 قیمت‌گذاری",callback_data="pricing"),InlineKeyboardButton("⚙️ تنظیمات",callback_data="settings"),InlineKeyboardButton("❓ راهنما",callback_data="help")]
    ])

def calc_mode_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🧮 شروع محاسبه",callback_data="calc_mode")], [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]])

def persistent_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]])

def back_home(extra=None):
    rows=[]
    if extra: rows.append(extra)
    rows.append([InlineKeyboardButton("⬅️ مرحله قبل",callback_data="back"),InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")])
    return InlineKeyboardMarkup(rows)

def section_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🧱 فونداسیون",callback_data="sec|فونداسیون"),InlineKeyboardButton("🏢 ستون",callback_data="sec|ستون")],
      [InlineKeyboardButton("📏 تیر",callback_data="sec|تیر"),InlineKeyboardButton("⬜ سقف",callback_data="sec|سقف")],
      [InlineKeyboardButton("🧱 دیوار",callback_data="sec|دیوار"),InlineKeyboardButton("🪜 پله",callback_data="sec|پله")],
      [InlineKeyboardButton("🔩 آرماتور/مدفون",callback_data="sec|آرماتور")],
      [InlineKeyboardButton("➕ آیتم سفارشی",callback_data="sec|سایر")],
      [InlineKeyboardButton("🏁 پایان متره",callback_data="finish_takeoff")],[InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
    ])

def type_menu(section):
    types={
      "فونداسیون":["پی منفرد","پی نواری","پی گسترده","پی مرکب","شناژ","بتن مگر"],
      "ستون":["30×30","35×35","40×40","40×50","50×50","سفارشی"],
      "تیر":["30×50","30×60","35×60","40×70","سفارشی"],
      "سقف":["تیرچه یونولیتی تک","تیرچه یونولیتی دوبل","تیرچه بلوک سفالی تک","تیرچه بلوک سفالی دوبل","وافل","دال بتنی","دال تخت"],
      "دیوار":["دیوار بتنی","دیوار حائل","دیوار برشی","سفارشی"],
      "پله":["پله بتنی"],
      "آرماتور":["میلگرد سفارشی","وصله/کوپلر","بولت","صفحه مدفون"],
      "سایر":["آیتم سفارشی"]}
    rows=[]; row=[]
    for t in types.get(section,["سفارشی"]):
        row.append(InlineKeyboardButton(t,callback_data=f"member|{section}|{t}"))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ مرحله قبل",callback_data="choose_section")])
    return InlineKeyboardMarkup(rows)

def review_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("✏️ اصلاح/حذف",callback_data="edit_members"),InlineKeyboardButton("➕ افزودن",callback_data="choose_section")],
      [InlineKeyboardButton("✅ تأیید نهایی",callback_data="confirm_project")],
      [InlineKeyboardButton("⬅️ مرحله قبل",callback_data="back"),InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
    ])

def report_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("➕ افزودن/اصلاح",callback_data="continue_project"),InlineKeyboardButton("📋 جدول جامع",callback_data="table")],
      [InlineKeyboardButton("📊 Excel + PDF",callback_data="exports")],[InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
    ])
