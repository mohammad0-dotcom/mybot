import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class WordGame:
    def __init__(self):
        self.games = {}  # chat_id: game_data
        self.words = [
            "سیب", "کتاب", "ماه", "خورشید", "گل", "درخت", "آب", "آتش",
            "دوست", "خانه", "مادر", "پدر", "برادر", "خواهر", "مدرسه",
            "دانشگاه", "کار", "زندگی", "عشق", "امید", "شادی", "غم",
            "شب", "روز", "صبح", "عصر", "بهار", "تابستان", "پاییز", "زمستان"
        ]
        logger.info("✅ بازی کلمات راه‌اندازی شد")
    
    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع بازی کلمات"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id in self.games:
            await update.message.reply_text("❌ همین الان یه بازی در این گروه در جریانه!")
            return
        
        first_word = random.choice(self.words)
        last_letter = first_word[-1]
        
        self.games[chat_id] = {
            'current_word': first_word,
            'last_letter': last_letter,
            'players': {user_id: update.effective_user.first_name},
            'last_player': user_id,
            'scores': {user_id: 0},
            'used_words': [first_word],
            'round': 1
        }
        
        await update.message.reply_text(
            f"🎮 **بازی کلمات شروع شد!**\n\n"
            f"کلمه اول: **{first_word}**\n"
            f"حرف آخر: **{last_letter}**\n\n"
            f"حالا نوبت بقیه‌ست!\n"
            f"با حرف {last_letter} یه کلمه بگید."
        )
    
    async def check_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بررسی کلمه ارسال شده"""
        if not update.message or not update.message.text:
            return
        
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        text = update.message.text.strip()
        
        if chat_id not in self.games:
            return
        
        game = self.games[chat_id]
        
        # چک کردن نوبت
        if user_id == game['last_player']:
            await update.message.reply_text("❌ صبر کن بقیه هم بازی کنن!")
            return
        
        # چک کردن حرف اول
        if not text.startswith(game['last_letter']):
            await update.message.reply_text(
                f"❌ کلمه باید با حرف **{game['last_letter']}** شروع بشه!"
            )
            return
        
        # چک کردن تکراری نبودن
        if text in game['used_words']:
            await update.message.reply_text("❌ این کلمه قبلاً گفته شده!")
            return
        
        # کلمه درسته
        game['used_words'].append(text)
        game['current_word'] = text
        game['last_letter'] = text[-1]
        game['last_player'] = user_id
        
        # امتیاز
        if user_id not in game['scores']:
            game['scores'][user_id] = 0
        game['scores'][user_id] += 1
        
        await update.message.reply_text(
            f"✅ کلمه قبول شد!\n"
            f"📌 کلمه جدید: **{text}**\n"
            f"🔤 حرف بعدی: **{game['last_letter']}**\n\n"
            f"🏆 امتیاز شما: {game['scores'][user_id]}"
        )
    
    async def show_scores(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش امتیازات"""
        chat_id = update.message.chat_id
        
        if chat_id not in self.games:
            await update.message.reply_text("❌ هیچ بازی در جریان نیست!")
            return
        
        game = self.games[chat_id]
        
        scores_text = "🏆 **امتیازات:**\n\n"
        sorted_scores = sorted(game['scores'].items(), key=lambda x: x[1], reverse=True)
        
        for i, (user_id, score) in enumerate(sorted_scores, 1):
            name = game['players'].get(user_id, f"کاربر {user_id}")
            scores_text += f"{i}. {name}: {score} امتیاز\n"
        
        await update.message.reply_text(scores_text)
    
    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پایان بازی"""
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        
        if chat_id not in self.games:
            await update.message.reply_text("❌ هیچ بازی در جریان نیست!")
            return
        
        game = self.games[chat_id]
        
        # پیدا کردن برنده
        winner_id = max(game['scores'], key=game['scores'].get)
        winner_name = game['players'].get(winner_id, f"کاربر {winner_id}")
        winner_score = game['scores'][winner_id]
        
        await update.message.reply_text(
            f"🎮 **بازی تموم شد!**\n\n"
            f"🏆 برنده: {winner_name}\n"
            f"✨ با {winner_score} امتیاز\n\n"
            f"📊 کلمات استفاده شده: {len(game['used_words'])} کلمه"
        )
        
        # پاک کردن بازی
        del self.games[chat_id]
