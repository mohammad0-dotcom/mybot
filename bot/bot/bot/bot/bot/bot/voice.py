from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import logging

logger = logging.getLogger(__name__)

class VoiceChatManager:
    def __init__(self, client):
        self.client = client
        self.call_client = PyTgCalls(client)
        self.active_calls = {}
        logger.info("✅ مدیریت کال صوتی راه‌اندازی شد")
    
    async def start(self):
        await self.call_client.start()
        logger.info("✅ کال صوتی فعال شد")
    
    async def join_voice(self, chat_id):
        """پیوستن به کال صوتی"""
        try:
            await self.call_client.join_group_call(
                chat_id,
                AudioPiped("silent.mp3")  # یه فایل صوتی سکوت
            )
            self.active_calls[chat_id] = {'status': 'connected'}
            return True, "✅ به کال وصل شدم!"
        except Exception as e:
            logger.error(f"خطا در اتصال به کال: {e}")
            return False, f"❌ خطا: {str(e)}"
    
    async def leave_voice(self, chat_id):
        """خروج از کال صوتی"""
        try:
            await self.call_client.leave_group_call(chat_id)
            if chat_id in self.active_calls:
                del self.active_calls[chat_id]
            return True, "✅ از کال خارج شدم!"
        except Exception as e:
            return False, f"❌ خطا: {str(e)}"
    
    async def play_audio(self, chat_id, audio_url):
        """پخش فایل صوتی"""
        try:
            await self.call_client.change_stream(
                chat_id,
                AudioPiped(audio_url)
            )
            return True, "✅ در حال پخش..."
        except Exception as e:
            return False, f"❌ خطا: {str(e)}"
    
    async def stop_audio(self, chat_id):
        """توقف پخش"""
        try:
            await self.call_client.change_stream(
                chat_id,
                AudioPiped("silent.mp3")
            )
            return True, "✅ پخش متوقف شد"
        except Exception as e:
            return False, f"❌ خطا: {str(e)}"
