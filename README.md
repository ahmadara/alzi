# پروژه پایه جنگو با Unfold Admin

## ویژگی‌ها
- ✅ Django 4.2 + Unfold Admin
- ✅ احراز هویت با رمز عبور
- ✅ احراز هویت با پیامک (قاصدک)
- ✅ اپلیکیشن اخبار (مدیریت مقالات)
- ✅ طراحی واکنش‌گرا با Tailwind CSS
- ✅ قالب‌های آماده (خانه، درباره، تماس، تعرفه، فرصت شغلی)

## نصب و راه‌اندازی

\`\`\`bash
# 1. کلون کنید
git clone your-repo-url
cd project-name

# 2. ساخت محیط مجازی
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# 3. نصب پکیج‌ها
pip install -r requirements.txt

# 4. کپی فایل تنظیمات
cp .env.example .env
# تنظیم SECRET_KEY و دیگر متغیرها

# 5. مایگریشن و اجرا
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
\`\`\`

## ساختار پروژه
\`\`\`
project/
├── apps/
│   ├── accounts/    # مدیریت کاربران
│   ├── news/        # اخبار و مقالات
│   └── common/      # ابزارهای مشترک
├── core/            # تنظیمات اصلی
├── static/          # فایل‌های استاتیک
├── templates/       # قالب‌های HTML
└── media/           # فایل‌های آپلودی
\`\`\`