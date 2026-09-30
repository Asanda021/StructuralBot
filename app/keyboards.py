from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗 پروژه جدید",callback_data="new_project"),InlineKeyboardButton("📂 پروژه‌ها",callback_data="projects"),InlineKeyboardButton("📊 آخرین گزارش",callback_data="reports")],
        [InlineKeyboardButton("➕ ادامه/افزودن متره",callback_data="continue_project"),InlineKeyboardButton("📋 جدول جامع",callback_data="table"),InlineKeyboardButton("📄 خروجی",callback_data="exports")],
        [InlineKeyboardButton("💰 قیمت‌گذاری",callback_data="pricing"),InlineKeyboardButton("⚙️ تنظیمات",callback_data="settings"),InlineKeyboardButton("❓ راهنما",callback_data="help")]
    ])
def back_home(): return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]])
def cancel_menu(): return back_home()
def section_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧱 فونداسیون",callback_data="sec|فونداسیون"),InlineKeyboardButton("🏢 ستون",callback_data="sec|ستون")],
        [InlineKeyboardButton("📏 تیر",callback_data="sec|تیر"),InlineKeyboardButton("⬜ سقف",callback_data="sec|سقف")],
        [InlineKeyboardButton("🧱 دیوار",callback_data="sec|دیوار"),InlineKeyboardButton("🪜 پله",callback_data="sec|پله")],
        [InlineKeyboardButton("🔩 آرماتور و اجزای فولادی",callback_data="sec|آرماتور")],
        [InlineKeyboardButton("➕ آیتم سفارشی",callback_data="sec|سایر")],
        [InlineKeyboardButton("🏁 پایان متره",callback_data="finish_takeoff"),InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
    ])
def item_menu(section):
    common={
      "فونداسیون":["پی منفرد","پی نواری","پی گسترده","پی مرکب","شناژ","بتن مگر","میلگرد پی","میلگرد انتظار","قالب پی"],
      "ستون":["بتن ستون","قالب ستون","میلگرد طولی ستون","خاموت ستون","سنجاقی ستون","میلگرد انتظار ستون"],
      "تیر":["بتن تیر","قالب تیر","میلگرد طولی تیر","خاموت تیر","سنجاقی تیر","میلگرد منفی تیر"],
      "سقف":["بتن سقف","یونولیت","تیرچه","میلگرد حرارتی","میلگرد منفی","اتکا","سنجاقی","ژوئن","کلاف میانی","قالب سقف"],
      "دیوار":["بتن دیوار","قالب دیوار","میلگرد قائم دیوار","میلگرد افقی دیوار","تقویت اطراف بازشو"],
      "پله":["بتن پله","قالب پله","میلگرد اصلی پله","میلگرد حرارتی پله"],
      "آرماتور":["میلگرد سفارشی","وصله/کوپلر","بولت","صفحه مدفون"],
      "سایر":["آیتم سفارشی"]
    }
    buttons=[]; row=[]
    for i,name in enumerate(common.get(section,["آیتم سفارشی"])):
        row.append(InlineKeyboardButton(name,callback_data=f"item|{i}|{name}"))
        if len(row)==2: buttons.append(row); row=[]
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ انتخاب بخش دیگر",callback_data="choose_section")])
    buttons.append([InlineKeyboardButton("🏁 پایان متره",callback_data="finish_takeoff")])
    return InlineKeyboardMarkup(buttons)
def report_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("➕ افزودن/اصلاح متره",callback_data="continue_project"),InlineKeyboardButton("📋 جدول جامع",callback_data="table")],
      [InlineKeyboardButton("📊 Excel + PDF",callback_data="exports"),InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
    ])
def review_menu():
    return InlineKeyboardMarkup([
      [InlineKeyboardButton("✅ ثبت و محاسبه نهایی",callback_data="confirm_project")],
      [InlineKeyboardButton("✏️ ویرایش آیتم‌ها",callback_data="continue_project"),InlineKeyboardButton("❌ لغو",callback_data="home")]
    ])
