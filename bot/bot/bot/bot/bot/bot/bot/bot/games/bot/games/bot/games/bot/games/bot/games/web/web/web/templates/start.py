#!/usr/bin/env python3
import threading
import time
import logging
from web.server import start_web_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """اجرای ربات با قابلیت ری‌استارت خودکار"""
    try:
        from bot.main import Bot
        import asyncio
        bot = Bot()
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"❌ خطا در ربات: {e}")
        logger.info("🔄 ری‌استارت در ۵ ثانیه...")
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    # شروع وب سرور در ترد جداگانه
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    logger.info("✅ وب سرور راه‌اندازی شد")
    
    # اجرای ربات
    run_bot()
