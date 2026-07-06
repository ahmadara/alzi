# مدل آموزش‌دیده

فایل‌های زیر را بعد از اجرای `notebooks/alzheimer_model_training.ipynb` در گوگل کولب، اینجا کپی کنید:

- `alzheimer_model.keras`
- `class_names.json`

سپس در `core/settings.py`: `DEMO_MODE = False`

این پوشه در `.gitignore` قرار دارد (فایل مدل حجیم است)؛ کد بارگذاری آن در `apps/diagnosis/ml_inference.py` است.
