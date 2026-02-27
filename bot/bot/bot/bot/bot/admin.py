from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import OWNER_ID, logger
from bot.database import Database
from bot.utils import Utils

class AdminTools:
    def __init__(self):
        self.db = Database()
        self.utils = Utils()
        logger.info("✅ ابزارهای مدیریت راه‌اندازی شد")
    
    async def ban_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بن کردن کاربر با ریپلای"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text("❌ روی پیام کاربر ریپلای کن!")
                return
            
            target = update.message.reply_to_message.from_user
            admin = update.message.from_user
            chat_id = update.message.chat_id
            
            if not self.db.is_admin(chat_id, admin.id) and admin.id != OWNER_ID:
                await update.message.reply_text("⛔ دسترسی نداری!")
                return
            
            await context.bot.ban_chat_member(chat_id, target.id)
            self.db.ban_user(target.id)
            
            await update.message.reply_text(
                f"✅ {target.first_name} بن شد!\n"
                f"🆔 آیدی: {target.id}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def kick_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اخراج کاربر با ریپلای"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text("❌ روی پیام کاربر ریپلای کن!")
                return
            
            target = update.message.reply_to_message.from_user
            admin = update.message.from_user
            chat_id = update.message.chat_id
            
            if not self.db.is_admin(chat_id, admin.id) and admin.id != OWNER_ID:
                await update.message.reply_text("⛔ دسترسی نداری!")
                return
            
            await context.bot.ban_chat_member(chat_id, target.id)
            await context.bot.unban_chat_member(chat_id, target.id)
            
            await update.message.reply_text(f"✅ {target.first_name} اخراج شد!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def warn_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اخطار دادن با ریپلای"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text("❌ روی پیام کاربر ریپلای کن!")
                return
            
            target = update.message.reply_to_message.from_user
            admin = update.message.from_user
            chat_id = update.message.chat_id
            
            if not self.db.is_admin(chat_id, admin.id) and admin.id != OWNER_ID:
                await update.message.reply_text("⛔ دسترسی نداری!")
                return
            
            self.db.add_warning(target.id)
            user_data = self.db.get_user(target.id)
            warnings = user_data[3] if user_data else 1
            
            await update.message.reply_text(
                f"⚠️ {target.first_name} اخطار گرفت!\n"
                f"📌 تعداد اخطارها: {warnings}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def clean_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن پیام‌ها"""
        try:
            if not context.args:
                await update.message.reply_text("❌ تعداد رو مشخص کن!\nمثال: /clean 10")
                return
            
            count = int(context.args[0])
            if count > 100:
                await update.message.reply_text("❌ حداکثر ۱۰۰ تا می‌تونم پاک کنم")
                return
            
            chat_id = update.message.chat_id
            message_id = update.message.message_id
            
            deleted = 0
            for i in range(message_id - count, message_id):
                try:
                    await context.bot.delete_message(chat_id, i)
                    deleted += 1
                except:
                    pass
            
            await update.message.reply_text(f"✅ {deleted} پیام پاک شد!")
            
        except ValueError:
            await update.message.reply_text("❌ عدد صحیح وارد کن!")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def group_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تنظیمات گروه"""
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(chat_id, user_id) and user_id != OWNER_ID:
            await update.message.reply_text("⛔ دسترسی نداری!")
            return
        
        group = self.db.get_group(chat_id)
        
        keyboard = [
            [
                InlineKeyboardButton("🔗 ضد لینک", callback_data=f"toggle_link_{chat_id}"),
                InlineKeyboardButton("🔄 ضد فوروارد", callback_data=f"toggle_fwd_{chat_id}")
            ],
            [
                InlineKeyboardButton("⚠️ ضد اسپم", callback_data=f"toggle_spam_{chat_id}"),
                InlineKeyboardButton("📝 حد اخطار", callback_data=f"set_warn_{chat_id}")
            ],
            [
                InlineKeyboardButton("🚫 لیست فیلتر", callback_data=f"show_filters_{chat_id}"),
                InlineKeyboardButton("👥 مدیران", callback_data=f"show_admins_{chat_id}")
            ]
        ]
        
        text = f"⚙️ **تنظیمات گروه**\n\n"
        if group:
            text += f"🔗 ضد لینک: {'✅ فعال' if group[2] else '❌ غیرفعال'}\n"
            text += f"🔄 ضد فوروارد: {'✅ فعال' if group[3] else '❌ غیرفعال'}\n"
            text += f"⚠️ ضد اسپم: {'✅ فعال' if group[4] else '❌ غیرفعال'}\n"
            text += f"📝 حد اخطار: {group[5]}\n"
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اضافه کردن کلمه به فیلتر"""
        try:
            if not context.args:
                await update.message.reply_text("❌ کلمه رو وارد کن!\nمثال: /addfilter بد")
                return
            
            word = ' '.join(context.args)
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id
            
            if not self.db.is_admin(chat_id, user_id) and user_id != OWNER_ID:
                await update.message.reply_text("⛔ دسترسی نداری!")
                return
            
            self.db.add_filter(chat_id, word, user_id)
            await update.message.reply_text(f"✅ کلمه '{word}' به لیست فیلتر اضافه شد!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def remove_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف کلمه از فیلتر"""
        try:
            if not context.args:
                await update.message.reply_text("❌ کلمه رو وارد کن!\nمثال: /removefilter بد")
                return
            
            word = ' '.join(context.args)
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id
            
            if not self.db.is_admin(chat_id, user_id) and user_id != OWNER_ID:
                await update.message.reply_text("⛔ دسترسی نداری!")
                return
            
            self.db.remove_filter(chat_id, word)
            await update.message.reply_text(f"✅ کلمه '{word}' از لیست فیلتر حذف شد!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
