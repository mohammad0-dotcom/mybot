import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from bot.config import BOT_TOKEN, OWNER_ID, logger
from bot.database import Database
from bot.admin import AdminTools
from bot.utils import Utils
from bot.voice import VoiceChatManager
import signal

class Bot:
    def __init__(self):
        self.db = Database()
        self.admin = AdminTools()
        self.utils = Utils()
        self.voice = None
        self.application = None
        self.is_running = True
        logger.info("🤖 ربات راه‌اندازی شد")
    
    def signal_handler(self, signum, frame):
        logger.info("در حال خاموش شدن...")
        self.is_running = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور استارت"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name)
        self.db.update_user_activity(user.id)
        
        await update.message.reply_text(
            f"👋 سلام {user.first_name} عزیز!\n\n"
            f"🤖 به ربات مدیریت گروه خوش اومدی\n"
            f"📌 برای دیدن دستورات /help رو بزن"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور راهنما"""
        help_text = """
📚 **راهنمای ربات**

🎮 **بازی‌ها:**
/mafia - شروع بازی مافیا (۱۵ نقش)
/chess - بازی شطرنج دونفره
/wordgame - بازی کلمات گروهی
/guess - حدس عدد

🛡️ **مدیریت گروه:**
/ban [ریپلای] - بن کاربر
/kick [ریپلای] - اخراج کاربر
/warn [ریپلای] - اخطار به کاربر
/clean [تعداد] - پاک کردن پیام
/addfilter [کلمه] - اضافه به فیلتر
/removefilter [کلمه] - حذف از فیلتر
/settings - تنظیمات گروه

🧠 **هوش مصنوعی:**
/ai [متن] - سوال از هوش مصنوعی

📊 **متفرقه:**
/stats - آمار خودت
/top [بازی] - برترین‌ها
/id - نمایش آیدی
        """
        await update.message.reply_text(help_text)
    
    async def ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """چت با هوش مصنوعی"""
        if not context.args:
            await update.message.reply_text("❌ یه چیزی بنویس!\nمثال: /ai سلام چطوری؟")
            return
        
        text = ' '.join(context.args)
        await update.message.reply_chat_action("typing")
        
        # اینجا می‌تونی DeepSeek رو وصل کنی
        response = f"🧠 شما گفت: {text}\n\n(هوش مصنوعی در حال توسعه)"
        await update.message.reply_text(response)
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """آمار کاربر"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        if user_data:
            text = f"📊 **آمار {user.first_name}**\n\n"
            text += f"🆔 آیدی: {user.id}\n"
            text += f"⚠️ اخطارها: {user_data[3]}\n"
            text += f"🏆 امتیاز: {user_data[6]}\n"
            text += f"🎮 بازی‌ها: {user_data[7]}\n"
            text += f"🥇 بردها: {user_data[8]}\n"
        else:
            text = "❌ اطلاعاتی پیدا نشد!"
        
        await update.message.reply_text(text)
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آیدی"""
        user = update.effective_user
        chat = update.effective_chat
        
        text = f"👤 **آیدی شما:** `{user.id}`\n"
        if user.username:
            text += f"📌 یوزرنیم: @{user.username}\n"
        text += f"👥 **آیدی گروه:** `{chat.id}`"
        
        await update.message.reply_text(text)
    
    async def top_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """برترین بازیکنان"""
        game = context.args[0] if context.args else "all"
        top = self.db.get_top_players(game)
        
        text = f"🏆 **برترین‌های {game}**\n\n"
        for i, (user_id, wins, score) in enumerate(top, 1):
            try:
                user = await context.bot.get_chat(user_id)
                name = user.first_name
            except:
                name = f"کاربر {user_id}"
            
            text += f"{i}. {name}: {score} امتیاز ({wins} برد)\n"
        
        await update.message.reply_text(text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت پیام‌ها"""
        if not update.message or not update.message.text:
            return
        
        user = update.effective_user
        chat = update.effective_chat
        
        # آپدیت آخرین فعالیت
        self.db.update_user_activity(user.id)
        
        # چک کردن بن بودن
        if self.db.is_banned(user.id):
            await update.message.delete()
            return
        
        # چک کردن گروه
        if chat.type in ['group', 'supergroup']:
            group = self.db.get_group(chat.id)
            if not group:
                self.db.add_group(chat.id, chat.title)
                group = self.db.get_group(chat.id)
            
            # ضد لینک
            if group[2] and self.utils.is_valid_link(update.message.text):
                await update.message.delete()
                await update.message.reply_text(f"@{user.username} ارسال لینک ممنوع!")
                return
            
            # فیلتر کلمات
            filters = self.db.get_filters(chat.id)
            for word in filters:
                if word in update.message.text:
                    await update.message.delete()
                    self.db.add_warning(user.id)
                    await update.message.reply_text(
                        f"@{user.username} کلمه '{word}' ممنوعه!\n"
                        f"⚠️ اخطار {self.db.get_user(user.id)[3]}"
                    )
                    return
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت کلیک روی دکمه‌ها"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('toggle_link_'):
            chat_id = int(data.split('_')[2])
            group = self.db.get_group(chat_id)
            new_value = 0 if group[2] else 1
            self.db.update_group(chat_id, 'anti_link', new_value)
            await query.edit_message_text("✅ تنظیمات بروز شد")
        
        elif data.startswith('toggle_fwd_'):
            chat_id = int(data.split('_')[2])
            group = self.db.get_group(chat_id)
            new_value = 0 if group[3] else 1
            self.db.update_group(chat_id, 'anti_forward', new_value)
            await query.edit_message_text("✅ تنظیمات بروز شد")
        
        elif data.startswith('toggle_spam_'):
            chat_id = int(data.split('_')[2])
            group = self.db.get_group(chat_id)
            new_value = 0 if group[4] else 1
            self.db.update_group(chat_id, 'anti_spam', new_value)
            await query.edit_message_text("✅ تنظیمات بروز شد")
        
        elif data.startswith('show_filters_'):
            chat_id = int(data.split('_')[2])
            filters = self.db.get_filters(chat_id)
            if filters:
                text = "🚫 **کلمات فیلتر شده:**\n" + "\n".join([f"• {w}" for w in filters])
            else:
                text = "📝 هیچ کلمه فیلتر شده‌ای نیست"
            await query.edit_message_text(text)
    
    def setup_handlers(self):
        """تنظیم همه هندلرها"""
        # دستورات عمومی
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("ai", self.ai))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("id", self.id_command))
        self.application.add_handler(CommandHandler("top", self.top_players))
        
        # دستورات مدیریت
        self.application.add_handler(CommandHandler("ban", self.admin.ban_reply))
        self.application.add_handler(CommandHandler("kick", self.admin.kick_reply))
        self.application.add_handler(CommandHandler("warn", self.admin.warn_reply))
        self.application.add_handler(CommandHandler("clean", self.admin.clean_messages))
        self.application.add_handler(CommandHandler("settings", self.admin.group_settings))
        self.application.add_handler(CommandHandler("addfilter", self.admin.add_filter))
        self.application.add_handler(CommandHandler("removefilter", self.admin.remove_filter))
        
        # کالبک
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # پیام‌ها
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("✅ همه هندلرها تنظیم شدن")
    
    async def run(self):
        """اجرای ربات"""
        # تنظیم سیگنال
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # ساختن اپلیکیشن
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # تنظیم هندلرها
        self.setup_handlers()
        
        # راه‌اندازی
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ ربات فعال شد!")
        
        # حلقه اصلی
        while self.is_running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    bot = Bot()
    asyncio.run(bot.run())
