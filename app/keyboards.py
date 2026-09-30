from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🧮 شروع برآورد",callback_data="start_estimate"),
       InlineKeyboardButton("➕ ادامه برآورد",callback_data="continue_project")],
      [InlineKeyboardButton("📋 جدول جامع",callback_data="table"),
       InlineKeyboardButton("📊 آخرین گزارش",callback_data="reports")],
      [InlineKeyboardButton("📤 Excel + PDF",callback_data="exports"),
       InlineKeyboardButton("🔁 معادل‌سازی میلگرد",callback_data="rebar_equiv")],
      [InlineKeyboardButton("⚙️ تنظیمات",callback_data="settings"),
       InlineKeyboardButton("🌐 زبان",callback_data="language")],
      [InlineKeyboardButton("👤 حساب کاربری",callback_data="account"),
       InlineKeyboardButton("❓ راهنما",callback_data="help")],
      [InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
    ])

def calc_mode_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("🧮 شروع برآورد",callback_data="start_estimate")],
      [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
    ])

def language_menu(initial=False):
    rows=[
      [InlineKeyboardButton("🇮🇷 فارسی",callback_data="lang|fa"),InlineKeyboardButton("🇸🇦 العربية",callback_data="lang|ar")],
      [InlineKeyboardButton("🇬🇧 English",callback_data="lang|en"),InlineKeyboardButton("🇨🇳 中文",callback_data="lang|zh")],
    ]
    if not initial:
        rows.append([InlineKeyboardButton("⬅️ بازگشت",callback_data="home")])
    return InlineKeyboardMarkup(rows)


def persistent_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🏠 خانه"), KeyboardButton("📂 پروژه‌ها"), KeyboardButton("🧮 شروع برآورد")]
    ], resize_keyboard=True, one_time_keyboard=False, is_persistent=True,
       input_field_placeholder="خانه | پروژه‌ها | شروع برآورد")

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
      [InlineKeyboardButton("📤 خروجی نهایی",callback_data="exports"),InlineKeyboardButton("📋 خروجی قابل کپی",callback_data="copy_output")],
      [InlineKeyboardButton("➕ افزودن/اصلاح",callback_data="continue_project"),InlineKeyboardButton("📋 جدول جامع",callback_data="table")],
      [InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")]
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
    diameters=[8,10,12,14,16,18,20,22,25,28,32]
    rows=[]
    row=[]
    for d in diameters:
        row.append(InlineKeyboardButton(f"Φ{d}",callback_data=f"eqsrc|{d}"))
        if len(row)==3:
            rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ بازگشت",callback_data="home")])
    return InlineKeyboardMarkup(rows)

def rebar_equiv_target_menu(source):
    diameters=[8,10,12,14,16,18,20,22,25,28,32]
    rows=[]
    row=[]
    for d in diameters:
        if d==source: continue
        row.append(InlineKeyboardButton(f"Φ{d}",callback_data=f"eqdst|{source}|{d}"))
        if len(row)==3:
            rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ قطر مبدأ",callback_data="rebar_equiv")])
    return InlineKeyboardMarkup(rows)


def input_keyboard(values=None, unit=""):
    """Preset picker plus manual entry. Presets are shortcuts, never design decisions."""
    rows=[]
    if values:
        row=[]
        for v in values:
            row.append(KeyboardButton(f"⚡ {v} {unit}"))
            if len(row)==2:
                rows.append(row); row=[]
        if row: rows.append(row)
    rows.append([KeyboardButton("✏️ ورود دستی")])
    rows.append([KeyboardButton("⬅️ مرحله قبل"), KeyboardButton("📋 ورودی‌ها")])
    rows.append([KeyboardButton("❌ لغو عضو")])
    rows.append([KeyboardButton("🏠 خانه"), KeyboardButton("📂 پروژه‌ها"), KeyboardButton("🧮 شروع برآورد")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False, is_persistent=True,
                               input_field_placeholder="مقدار آماده را انتخاب کن یا ورود دستی بزن")

def field_menu(values=None, unit=""):
    rows=[]
    if values:
        row=[]
        for v in values:
            row.append(InlineKeyboardButton(f"⚡ {v} {unit}",callback_data=f"ready|{v}"))
            if len(row)==2:
                rows.append(row); row=[]
        if row: rows.append(row)
    rows.append([InlineKeyboardButton("✏️ ورود دستی",callback_data="manual")])
    rows.append([
        InlineKeyboardButton("⬅️ مرحله قبل",callback_data="back_field"),
        InlineKeyboardButton("📋 ورودی‌ها",callback_data="show_inputs")
    ])
    rows.append([
        InlineKeyboardButton("❌ لغو عضو",callback_data="cancel_member"),
        InlineKeyboardButton("🏠 منو",callback_data="home")
    ])
    rows.append([InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")])
    return InlineKeyboardMarkup(rows)

def ask_text(name,fields,section,typ,values=None):
    label,unit=fields[0]
    if values:
        shown="  |  ".join(str(v) for v in values)
        ready=f"\n\n⚡ <b>مقادیر آماده:</b> {shown} {unit}"
    else:
        ready=""
    return f"✏️ <b>{name}</b>\n\n<b>{label}</b> ({unit}){ready}\n\nیکی از مقادیر آماده را انتخاب کن یا «✏️ ورود دستی» را بزن.\n\n⚠️ مقادیر آماده فقط میانبر ورود هستند؛ مقدار نهایی را با نقشه کنترل کن."


