from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🏗 پروژه جدید",callback_data="new_project"),InlineKeyboardButton("📂 پروژه‌های من",callback_data="projects")],
      [InlineKeyboardButton("🏢 اطلاعات ساختمان",callback_data="building_info")],
      [InlineKeyboardButton("🧱 بتن",callback_data="takeoff|concrete"),InlineKeyboardButton("🔩 میلگرد",callback_data="takeoff|rebar")],
      [InlineKeyboardButton("🪵 قالب‌بندی",callback_data="takeoff|formwork"),InlineKeyboardButton("🧱 مصالح",callback_data="takeoff|materials")],
      [InlineKeyboardButton("🔁 معادل‌سازی میلگرد",callback_data="rebar_equiv")],
      [InlineKeyboardButton("🏗 اجزای سازه",callback_data="continue_project"),InlineKeyboardButton("📋 ورودی‌های پروژه",callback_data="project_inputs")],
      [InlineKeyboardButton("📊 جدول جامع",callback_data="table"),InlineKeyboardButton("📄 PDF / Excel",callback_data="exports")],
      [InlineKeyboardButton("💰 برآورد ریالی",callback_data="pricing")],
      [InlineKeyboardButton("⚙️ تنظیمات",callback_data="settings"),InlineKeyboardButton("👤 حساب کاربری",callback_data="account")],
      [InlineKeyboardButton("❓ راهنما",callback_data="help"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
    ])
def calc_mode_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("⚡ متره سریع",callback_data="mode|quick"),InlineKeyboardButton("🧮 متره دقیق",callback_data="mode|detailed")],
      [InlineKeyboardButton("🏗 متره اجرایی/خرید",callback_data="mode|procurement")],
      [InlineKeyboardButton("🌐 زبان / Language",callback_data="language")],
      [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
    ])

def language_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🇮🇷 فارسی",callback_data="lang|fa"),InlineKeyboardButton("🇸🇦 العربية",callback_data="lang|ar")],
      [InlineKeyboardButton("🇬🇧 English",callback_data="lang|en"),InlineKeyboardButton("🇨🇳 中文",callback_data="lang|zh")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="home")]
    ])

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
      "سقف":["تیرچه تک","تیرچه دوبل","تیرچه یونولیتی تک","تیرچه یونولیتی دوبل","تیرچه بلوک سفالی تک","تیرچه بلوک سفالی دوبل","وافل","یوبوت","دال بتنی","دال تخت"],
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


def legacy_engineering_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 پروژه جدید", callback_data="new_project"), InlineKeyboardButton("📂 پروژه‌های من", callback_data="projects")],
        [InlineKeyboardButton("🧱 فونداسیون", callback_data="section|فونداسیون"), InlineKeyboardButton("🏛 ستون‌ها", callback_data="section|ستون")],
        [InlineKeyboardButton("➖ تیرها", callback_data="section|تیر"), InlineKeyboardButton("🏗 سقف‌ها", callback_data="section|سقف")],
        [InlineKeyboardButton("🧱 دیوارها", callback_data="walls_menu"), InlineKeyboardButton("🪜 راه‌پله", callback_data="section|پله")],
        [InlineKeyboardButton("📊 خلاصه پروژه", callback_data="summary"), InlineKeyboardButton("📋 بازبینی", callback_data="review")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"), InlineKeyboardButton("❓ راهنما", callback_data="help")],
    ])

def walls_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧱 دیوار برشی", callback_data="type|دیوار برشی"), InlineKeyboardButton("🧱 دیوار حائل", callback_data="type|دیوار حائل")],
        [InlineKeyboardButton("⬅️ بازگشت", callback_data="home")]
    ])


def takeoff_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🧱 بتن",callback_data="takeoff|concrete"),InlineKeyboardButton("🔩 میلگرد",callback_data="takeoff|rebar")],
      [InlineKeyboardButton("🪵 قالب‌بندی",callback_data="takeoff|formwork"),InlineKeyboardButton("🧱 مصالح",callback_data="takeoff|materials")],
      [InlineKeyboardButton("🏗 انتخاب اعضای سازه",callback_data="continue_project")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="home")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🌐 زبان",callback_data="language"),InlineKeyboardButton("📏 واحدها",callback_data="units")],
      [InlineKeyboardButton("🧮 حالت متره",callback_data="calc_mode"),InlineKeyboardButton("📐 استاندارد/مرجع",callback_data="standards")],
      [InlineKeyboardButton("🏗 مشخصات بتن",callback_data="concrete_settings"),InlineKeyboardButton("🔩 گرید میلگرد",callback_data="rebar_settings")],
      [InlineKeyboardButton("📏 طول شاخه میلگرد",callback_data="stock_length")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="home")]
    ])

def units_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🇮🇷 متریک (m, cm, mm)",callback_data="unit|metric")],
      [InlineKeyboardButton("🇬🇧 Imperial",callback_data="unit|imperial")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="settings")]
    ])

def standards_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🇮🇷 مقررات ملی ایران",callback_data="standard|iran")],
      [InlineKeyboardButton("🇺🇸 ACI 318",callback_data="standard|aci")],
      [InlineKeyboardButton("🇪🇺 Eurocode 2",callback_data="standard|ec2")],
      [InlineKeyboardButton("🇨🇳 China — GB/T 50010-2010(2024)",callback_data="standard|china")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="settings")]
    ])

def concrete_settings_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("C20",callback_data="concrete_grade|C20"),InlineKeyboardButton("C25",callback_data="concrete_grade|C25"),InlineKeyboardButton("C30",callback_data="concrete_grade|C30")],
      [InlineKeyboardButton("C35",callback_data="concrete_grade|C35"),InlineKeyboardButton("C40",callback_data="concrete_grade|C40")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="settings")]
    ])

def rebar_settings_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("A2",callback_data="rebar_grade|A2"),InlineKeyboardButton("A3",callback_data="rebar_grade|A3"),InlineKeyboardButton("A4",callback_data="rebar_grade|A4")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="settings")]
    ])

def rebar_equivalency_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("Φ8 ↔ Φ10",callback_data="eq|8|10"),InlineKeyboardButton("Φ10 ↔ Φ12",callback_data="eq|10|12")],
      [InlineKeyboardButton("Φ12 ↔ Φ14",callback_data="eq|12|14"),InlineKeyboardButton("Φ14 ↔ Φ16",callback_data="eq|14|16")],
      [InlineKeyboardButton("Φ16 ↔ Φ18",callback_data="eq|16|18"),InlineKeyboardButton("Φ18 ↔ Φ20",callback_data="eq|18|20")],
      [InlineKeyboardButton("Φ20 ↔ Φ22",callback_data="eq|20|22"),InlineKeyboardButton("Φ22 ↔ Φ25",callback_data="eq|22|25")],
      [InlineKeyboardButton("Φ25 ↔ Φ28",callback_data="eq|25|28"),InlineKeyboardButton("Φ28 ↔ Φ32",callback_data="eq|28|32")],
      [InlineKeyboardButton("⬅️ بازگشت",callback_data="home")]
    ])
