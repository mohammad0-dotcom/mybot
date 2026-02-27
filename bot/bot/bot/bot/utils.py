import re
import time
from datetime import datetime, timedelta

class Utils:
    @staticmethod
    def is_valid_link(text):
        """چک کردن لینک"""
        pattern = r'https?://\S+|www\.\S+'
        return bool(re.search(pattern, text))
    
    @staticmethod
    def extract_mentions(text):
        """استخراج یوزرنیم"""
        return re.findall(r'@(\w+)', text)
    
    @staticmethod
    def format_time(seconds):
        """فرمت زمان"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours} ساعت {minutes} دقیقه"
        elif minutes > 0:
            return f"{minutes} دقیقه {secs} ثانیه"
        else:
            return f"{secs} ثانیه"
    
    @staticmethod
    def get_rank(score):
        """دریافت رتبه بر اساس امتیاز"""
        if score < 100:
            return "🥉 نوآموز"
        elif score < 500:
            return "🥈 حرفه‌ای"
        elif score < 1000:
            return "🥇 استاد"
        else:
            return "👑 افسانه"
    
    @staticmethod
    def is_admin(user_id, admins):
        """چک کردن ادمین بودن"""
        return user_id in admins
