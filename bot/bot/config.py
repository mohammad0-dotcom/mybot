import os
import logging
from dotenv import load_dotenv

# لود متغیرهای محیطی
load_dotenv()

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن‌ها و آی‌دی‌ها
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# دیتابیس
DATABASE_NAME = "bot_database.db"

# تنظیمات وب
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD")
WEB_SECRET_TOKEN = os.getenv("WEB_SECRET_TOKEN")

# چک کردن مقادیر ضروری
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN پیدا نشد! فایل .env را چک کن")
if not WEB_PASSWORD:
    raise ValueError("❌ WEB_PASSWORD پیدا نشد! فایل .env را چک کن")
