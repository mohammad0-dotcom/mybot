import random
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class GuessGame:
    def __init__(self):
        self.games = {}  # chat_id: game_data
        logger.info("✅ بازی حدس عدد راه‌اندازی شد")
    
    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع بازی حدس عدد"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id in self.games:
            await update.message.reply_text("❌ همین الان یه بازی در جریانه!")
            return
        
        number = random.randint(1, 100)
        
        self.games[chat_id] = {
            'number': number,
            'players': {user_id: update.effective_user.first_name},
            'guesses': {},
            'min_range': 1,
            'max_range': 100,
            'active': True
        }
        
        await update.message.reply_text(
            f"🎯 **بازی حدس عدد شروع شد!**\n\n"
            f"من یه عدد بین ۱ تا ۱۰۰ انتخاب کردم.\n"
            f"هر کی زودتر حدس بزنه برنده‌ست!\n\n"
            f"برای حدس زدن، عدد رو بفرستید."
        )
    
    async def check_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بررسی حدس"""
        if not update.message or not update.message.text:
            return
        
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        text = update.message.text.strip()
        
        if chat_id not in self.games:
            return
        
        game = self.games[chat_id]
        
        if not game['active']:
            return
        
        # چک کردن عدد بودن
        try:
            guess = int(text)
        except ValueError:
            return
        
        if guess < 1 or guess > 100:
            await update.message.reply_text("❌ عدد باید بین ۱ تا ۱۰۰ باشه!")
            return
        
        # ذخیره حدس
        if user_id not in game['guesses']:
            game['guesses'][user_id] = []
        game['guesses'][user_id].append(guess)
        
        # چک کردن درستی حدس
        if guess == game['number']:
            # برنده شد
            game['active'] = False
            attempts = len(game['guesses'][user_id])
            
            await update.message.reply_text(
                f"🎉 **تبریک!**\n\n"
                f"👤 {update.effective_user.first_name}\n"
                f"🔢 عدد {game['number']} رو درست حدس زد!\n"
                f"📊 تعداد تلاش: {attempts}"
            )
            
            # پاک کردن بازی
            del self.games[chat_id]
            
        elif guess < game['number']:
            if guess > game['min_range']:
                game['min_range'] = guess + 1
            await update.message.reply_text(
                f"📈 عدد بزرگتره!\n"
                f"📌 محدوده: {game['min_range']} تا {game['max_range']}"
            )
        else:
            if guess < game['max_range']:
                game['max_range'] = guess - 1
            await update.message.reply_text(
                f"📉 عدد کوچیکتره!\n"
                f"📌 محدوده: {game['min_range']} تا {game['max_range']}"
            )
    
    async def give_up(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انصراف از بازی"""
        chat_id = update.message.chat_id
        
        if chat_id not in self.games:
            await update.message.reply_text("❌ هیچ بازی در جریان نیست!")
            return
        
        game = self.games[chat_id]
        
        await update.message.reply_text(
            f"😢 بازی تموم شد!\n"
            f"🔢 عدد من بود: {game['number']}"
        )
        
        del self.games[chat_id]
    
    async def hint(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """درخواست راهنمایی"""
        chat_id = update.message.chat_id
        
        if chat_id not in self.games:
            await update.message.reply_text("❌ هیچ بازی در جریان نیست!")
            return
        
        game = self.games[chat_id]
        
        if game['number'] % 2 == 0:
            hint_text = "🟢 عدد زوج"
        else:
            hint_text = "🔴 عدد فرد"
        
        await update.message.reply_text(f"💡 راهنمایی: {hint_text}")
