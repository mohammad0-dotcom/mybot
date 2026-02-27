import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class MafiaGame:
    def __init__(self):
        self.games = {}  # chat_id: game_data
        self.roles_description = {
            # شهروندان (۷ نقش)
            "شهروند ساده": "👤 یه شهروند معمولی. فقط روزها رای میدی.",
            "دکتر": "💊 هر شب می‌تونی یه نفر رو نجات بدی (خودت نمی‌تونی)",
            "کارآگاه": "🔍 هر شب می‌تونی نقش یه نفر رو ببینی",
            "تک‌تیرانداز": "🎯 یه بار توی بازی می‌تونی شب یه نفر رو بکشی",
            "روزنامه‌نگار": "📰 صبح که میشه، یه نکته از شب قبل می‌فهمی",
            "بدل": "🎭 اولین باری که مافیا بهت حمله کنه، بهشون برمی‌گرده",
            "شهردار": "🏛️ رای تو توی روز دوتا حساب میشه",
            
            # مافیا (۵ نقش)
            "مافیای ساده": "🔪 شب‌ها با مافیاها یکی رو میکشید",
            "رئیس مافیا": "👑 رای مافیا رو آخرین نفر اعلام می‌کنی",
            "مخفی‌کار": "🕵️ کارآگاه نقش تو رو شهروند می‌بینه",
            "زهرمار": "☠️ اگه دکتر نجاتت بده، دکتر میمیره",
            "جادوگر": "🪄 می‌تونی یه بار قتل رو به یه نفر دیگه بندازی",
            
            # مستقل (۳ نقش)
            "گرگ تنها": "🐺 تنها بازی می‌کنی، هر شب یه نفر رو میکشی",
            "دیوانه": "🎪 هر شب یه نفر رو انتخاب می‌کنی، ممکنه بکشی یا نجات بدی",
            "فرشته": "😇 یکی رو انتخاب می‌کنی که باید تا آخر زنده بمونه"
        }
        logger.info("✅ بازی مافیا راه‌اندازی شد")
    
    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع بازی مافیا"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id in self.games:
            await update.message.reply_text("❌ همین الان یه بازی در این گروه در جریانه!")
            return
        
        keyboard = [[InlineKeyboardButton("✅ من هستم", callback_data="mafia_join")]]
        
        msg = await update.message.reply_text(
            "🎮 **شروع بازی مافیا**\n\n"
            "👥 کسایی که می‌خوان بازی کنن دکمه پایین رو بزنن\n"
            "📌 حداقل ۵ نفر، حداکثر ۱۵ نفر\n\n"
            f"👤 بازیکنان: ۱ نفر",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        self.games[chat_id] = {
            'players': {user_id: {'name': update.effective_user.first_name, 'ready': True}},
            'phase': 'waiting',
            'host': user_id,
            'message_id': msg.message_id,
            'roles': {},
            'alive': [],
            'dead': [],
            'votes': {},
            'night_actions': {},
            'day': 1
        }
    
    async def join_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیوستن به بازی"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        user_name = query.from_user.first_name
        
        if chat_id not in self.games:
            await query.edit_message_text("❌ این بازی وجود نداره!")
            return
        
        game = self.games[chat_id]
        
        if len(game['players']) >= 15:
            await query.answer("❌ ظرفیت تکمیل شده!")
            return
        
        if user_id in game['players']:
            await query.answer("❌ تو قبلاً اومدی!")
            return
        
        # اضافه کردن بازیکن
        game['players'][user_id] = {'name': user_name, 'ready': True}
        
        # ساخت لیست بازیکنان
        players_list = "\n".join([f"👤 {p['name']}" for p in game['players'].values()])
        
        keyboard = [[InlineKeyboardButton("✅ من هستم", callback_data="mafia_join")]]
        
        if len(game['players']) >= 5:
            keyboard.append([InlineKeyboardButton("🎮 شروع بازی", callback_data="mafia_start")])
        
        await query.edit_message_text(
            f"🎮 **بازی مافیا**\n\n"
            f"👥 بازیکنان ({len(game['players'])}):\n{players_list}\n\n"
            f"{'✅ آماده شروع!' if len(game['players']) >= 5 else '⏳ منتظر بقیه...'}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def start_game_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع بازی بعد از کلیک روی دکمه"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        
        if chat_id not in self.games:
            await query.edit_message_text("❌ بازی وجود نداره!")
            return
        
        game = self.games[chat_id]
        
        if len(game['players']) < 5:
            await query.answer("❌ حداقل ۵ نفر نیازه!")
            return
        
        await query.edit_message_text("🎭 **در حال توزیع نقش‌ها...**")
        await self.assign_roles(chat_id, context)
    
    async def assign_roles(self, chat_id, context):
        """توزیع نقش‌ها بین بازیکنان"""
        game = self.games[chat_id]
        players = list(game['players'].keys())
        random.shuffle(players)
        num_players = len(players)
        
        # تعیین تعداد نقش‌ها
        num_mafia = max(2, num_players // 4)
        num_independent = max(1, num_players // 6)
        num_citizen = num_players - num_mafia - num_independent
        
        roles = []
        
        # نقش‌های مافیا
        mafia_roles = ["مافیای ساده", "مافیای ساده", "رئیس مافیا", "مخفی‌کار", "زهرمار", "جادوگر"]
        for i in range(num_mafia):
            roles.append(mafia_roles[i % len(mafia_roles)])
        
        # نقش‌های مستقل
        independent_roles = ["گرگ تنها", "دیوانه", "فرشته"]
        for i in range(num_independent):
            roles.append(independent_roles[i % len(independent_roles)])
        
        # نقش‌های شهروند
        citizen_roles = ["شهروند ساده", "دکتر", "کارآگاه", "تک‌تیرانداز", "روزنامه‌نگار", "بدل", "شهردار"]
        for i in range(num_citizen):
            roles.append(citizen_roles[i % len(citizen_roles)])
        
        random.shuffle(roles)
        
        # تخصیص نقش‌ها
        roles_dict = {}
        alive_list = []
        
        for i, player_id in enumerate(players):
            role = roles[i]
            roles_dict[player_id] = {
                'role': role,
                'description': self.roles_description[role],
                'alive': True,
                'night_action': False,
                'action_target': None,
                'role_used': False
            }
            alive_list.append(player_id)
        
        game['roles'] = roles_dict
        game['alive'] = alive_list
        
        # ارسال نقش‌ها به صورت خصوصی
        for player_id in players:
            role_data = roles_dict[player_id]
            role_text = f"🎭 **نقش تو: {role_data['role']}**\n\n{role_data['description']}\n\n"
            
            # اطلاعات اضافه برای مافیاها
            if "مافیا" in role_data['role']:
                mafia_team = []
                for pid, r in roles_dict.items():
                    if "مافیا" in r['role'] and pid != player_id:
                        mafia_team.append(game['players'][pid]['name'])
                
                if mafia_team:
                    role_text += f"👥 مافیاهای دیگه: {', '.join(mafia_team)}\n"
            
            try:
                await context.bot.send_message(chat_id=player_id, text=role_text)
            except:
                pass
        
        # اعلام شروع بازی
        await context.bot.send_message(
            chat_id=chat_id,
            text="🌙 **شب اول شروع شد**\nنقش‌های خاص می‌تونن عمل کنن..."
        )
        
        # شروع شب
        await self.start_night(chat_id, context)
    
    async def start_night(self, chat_id, context):
        """شروع فاز شب"""
        game = self.games[chat_id]
        game['phase'] = 'night'
        game['night_actions'] = {}
        
        # جمع‌آوری نقش‌هایی که می‌تونن عمل کنن
        for player_id, role_data in game['roles'].items():
            if not role_data['alive']:
                continue
            
            role = role_data['role']
            alive_others = [p for p in game['alive'] if p != player_id]
            
            if not alive_others:
                continue
            
            # مافیاها
            if "مافیا" in role:
                keyboard = []
                for target_id in alive_others[:10]:
                    target_name = game['players'][target_id]['name']
                    keyboard.append([InlineKeyboardButton(
                        f"🔪 {target_name}",
                        callback_data=f"mafia_night_kill_{player_id}_{target_id}"
                    )])
                
                try:
                    await context.bot.send_message(
                        chat_id=player_id,
                        text="🌙 کی رو می‌خوای بکشی؟",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass
            
            # دکتر
            elif role == "دکتر":
                keyboard = []
                for target_id in game['alive']:
                    target_name = game['players'][target_id]['name']
                    keyboard.append([InlineKeyboardButton(
                        f"💊 {target_name}",
                        callback_data=f"mafia_night_save_{player_id}_{target_id}"
                    )])
                
                try:
                    await context.bot.send_message(
                        chat_id=player_id,
                        text="🌙 کی رو می‌خوای نجات بدی؟",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass
            
            # کارآگاه
            elif role == "کارآگاه":
                keyboard = []
                for target_id in alive_others:
                    target_name = game['players'][target_id]['name']
                    keyboard.append([InlineKeyboardButton(
                        f"🔍 {target_name}",
                        callback_data=f"mafia_night_detect_{player_id}_{target_id}"
                    )])
                
                try:
                    await context.bot.send_message(
                        chat_id=player_id,
                        text="🌙 کی رو می‌خوای بررسی کنی؟",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass
        
        # تایمر شب (۲ دقیقه)
        await asyncio.sleep(120)
        
        if chat_id in self.games:
            await self.end_night(chat_id, context)
    
    async def night_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ثبت اقدام شب"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        action = data[2]
        player_id = int(data[3])
        target_id = int(data[4])
        chat_id = query.message.chat_id
        
        if chat_id not in self.games:
            await query.edit_message_text("❌ بازی تموم شده!")
            return
        
        game = self.games[chat_id]
        game['night_actions'][player_id] = {
            'type': action,
            'target': target_id
        }
        
        await query.edit_message_text("✅ اقدامت ثبت شد، منتظر بقیه...")
    
    async def end_night(self, chat_id, context):
        """پایان شب و شروع روز"""
        game = self.games[chat_id]
        actions = game['night_actions']
        
        killed_by_mafia = []
        saved_by_doctor = None
        investigated = {}
        
        # پردازش اقدامات
        for player_id, action in actions.items():
            if action['type'] == 'kill':
                killed_by_mafia.append(action['target'])
            elif action['type'] == 'save':
                saved_by_doctor = action['target']
            elif action['type'] == 'detect':
                investigated[player_id] = action['target']
        
        # مشخص کردن کشته شده
        killed = None
        if killed_by_mafia:
            from collections import Counter
            vote_count = Counter(killed_by_mafia)
            killed = vote_count.most_common(1)[0][0]
            
            # نجات توسط دکتر
            if killed == saved_by_doctor:
                killed = None
        
        if killed:
            game['roles'][killed]['alive'] = False
            game['alive'].remove(killed)
            game['dead'].append(killed)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"💀 صبح شد... {game['players'][killed]['name']} مرده!"
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="☀️ صبح شد... خوشبختانه کسی نمرده!"
            )
        
        # گزارش کارآگاه
        for investigator, target in investigated.items():
            role = game['roles'][target]['role']
            is_mafia = "مافیا" in role
            await context.bot.send_message(
                chat_id=investigator,
                text=f"🔍 {game['players'][target]['name']} {'مافیا' if is_mafia else 'شهروند'} است!"
            )
        
        # چک پایان بازی
        if await self.check_game_end(chat_id, context):
            return
        
        # شروع روز
        await self.start_day(chat_id, context)
    
    async def start_day(self, chat_id, context):
        """شروع فاز روز"""
        game = self.games[chat_id]
        game['phase'] = 'day'
        game['votes'] = {}
        
        mafia_count = sum(1 for r in game['roles'].values() if r['alive'] and "مافیا" in r['role'])
        citizen_count = len(game['alive']) - mafia_count
        
        # ساخت صفحه کلید رای‌گیری
        keyboard = []
        for player_id in game['alive']:
            player_name = game['players'][player_id]['name']
            keyboard.append([InlineKeyboardButton(
                f"🗳️ {player_name}",
                callback_data=f"mafia_vote_{player_id}"
            )])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"☀️ **روز {game['day']}**\n"
                 f"👥 زنده: {len(game['alive'])} نفر\n"
                 f"🔪 مافیا: {mafia_count} نفر\n\n"
                 f"به کی رای می‌دین؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # تایمر روز (۳ دقیقه)
        await asyncio.sleep(180)
        
        if chat_id in self.games:
            await self.end_day(chat_id, context)
    
    async def vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ثبت رای"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        target_id = int(data[2])
        voter_id = query.from_user.id
        chat_id = query.message.chat_id
        
        if chat_id not in self.games:
            await query.answer("❌ بازی تموم شده!")
            return
        
        game = self.games[chat_id]
        
        if not game['roles'][voter_id]['alive']:
            await query.answer("❌ تو مرده‌ای!")
            return
        
        game['votes'][voter_id] = target_id
        await query.answer("✅ رای ثبت شد!")
    
    async def end_day(self, chat_id, context):
        """پایان روز"""
        game = self.games[chat_id]
        votes = game['votes']
        
        if not votes:
            await context.bot.send_message(
                chat_id=chat_id,
                text="😴 هیچکس رای نداد، شب شد..."
            )
            game['day'] += 1
            await self.start_night(chat_id, context)
            return
        
        # شمارش رای‌ها
        from collections import Counter
        vote_count = Counter(votes.values())
        
        max_votes = max(vote_count.values())
        max_voted = [p for p, c in vote_count.items() if c == max_votes]
        
        if len(max_voted) > 1:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🤝 رای‌ها مساوی شد، کسی اعدام نشد!"
            )
        else:
            executed = max_voted[0]
            game['roles'][executed]['alive'] = False
            game['alive'].remove(executed)
            game['dead'].append(executed)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚖️ {game['players'][executed]['name']} با رای مردم اعدام شد!"
            )
        
        # چک پایان بازی
        if await self.check_game_end(chat_id, context):
            return
        
        game['day'] += 1
        await self.start_night(chat_id, context)
    
    async def check_game_end(self, chat_id, context):
        """چک کردن پایان بازی"""
        game = self.games[chat_id]
        
        mafia_count = sum(1 for r in game['roles'].values() if r['alive'] and "مافیا" in r['role'])
        citizen_count = sum(1 for r in game['roles'].values() if r['alive'] and "شهروند" in r['role'])
        independent_count = len(game['alive']) - mafia_count - citizen_count
        
        # شهروندان پیروز
        if mafia_count == 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 **شهروندان پیروز شدن!**\nهمه مافیاها کشته شدن!"
            )
            del self.games[chat_id]
            return True
        
        # مافیا پیروز
        if mafia_count >= citizen_count:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔪 **مافیاها پیروز شدن!**\nتعدادشون از شهرونا بیشتر شد!"
            )
            del self.games[chat_id]
            return True
        
        return False
