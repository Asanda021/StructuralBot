# StructuralBot Lite

نسخه سبک و پایدار ربات تلگرام محاسبات و برآورد سازه.

## معماری
- یک CallbackQueryHandler برای تمام دکمه‌ها
- یک MessageHandler برای تمام ورودی‌ها
- SQLite سبک
- اجرای Telegram با run_polling
- health server فقط با کتابخانه استاندارد Python
- بدون Webhook سفارشی، Flask، routing چندلایه یا سرویس‌های اضافی

## امکانات
- پروژه‌ها
- محاسبه حجم بتن پی، ستون، تیر و سقف
- برآورد بتن با 5٪ پرت
- معادل‌سازی سطح مقطع میلگرد
- ذخیره و نمایش آخرین محاسبه
- حساب کاربری و تنظیمات پایه
- جایگاه آماده برای AI، پرداخت، کدهای طراحی و گزارش حرفه‌ای

## اجرا
```bash
pip install -r requirements.txt
BOT_TOKEN="YOUR_TOKEN" python bot.py
```

روی Render فقط BOT_TOKEN لازم است. سرویس روی PORT داخلی Render یک health endpoint سبک اجرا می‌کند و تلگرام با polling مدیریت می‌شود.
