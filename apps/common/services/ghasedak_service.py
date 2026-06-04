import requests
import random
from django.conf import settings

class GhasedakService:
    def __init__(self):
        self.api_key = settings.GHASEDAK_API_KEY
        self.template_name = getattr(settings, 'GHASEDAK_TEMPLATE_NAME', 'Ghasedak')
        self.otp_url = "https://gateway.ghasedak.me/rest/api/v1/WebService/SendOtpSMS"
    
    def send_otp(self, phone: str, code: str = None):
        """ارسال کد OTP با استفاده از API قاصدک"""
        if not self.api_key:
            print("⚠️ API Key قاصدک تنظیم نشده است.")
            return False, None
        
        if code is None:
            code = str(random.randint(100000, 999999))
        
        headers = {
            "Content-Type": "application/json",
            "ApiKey": self.api_key
        }
        
        payload = {
            "receptors": [
                {"mobile": phone}
            ],
            "templateName": self.template_name,
            "inputs": [
                {"param": "code", "value": code}
            ],
            "udh": False,
            "isVoice": False
        }
        
        try:
            response = requests.post(self.otp_url, json=payload, headers=headers, timeout=10)
            
            # دریافت پاسخ به صورت دیکشنری
            result = response.json()
            
            print(f"Status Code: {response.status_code}")
            
            # بررسی مستقیم - اگر وضعیت 200 باشد و isSuccess وجود داشته باشد
            if response.status_code == 200:
                # چک کردن isSuccess در هر شکلی
                is_success = result.get("isSuccess", False)
                
                if is_success:
                    print(f"✅ OTP با موفقیت به {phone} ارسال شد")
                    print(f"📨 کد ارسالی: {code}")
                    return True, code
                else:
                    error_msg = result.get("message", "خطای ناشناخته")
                    print(f"❌ خطا: {error_msg}")
                    return False, code
            else:
                print(f"❌ خطای HTTP {response.status_code}")
                return False, code
                
        except Exception as e:
            print(f"❌ خطا: {e}")
            return False, code