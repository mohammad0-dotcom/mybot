import chess
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class ChessGame:
    def __init__(self):
        self.games = {}  # game_id: game_data
        self.challenges = {}  # chat_id: challenges
        logger.info("✅ بازی شطرنج راه‌اندازی شد")
    
    def board_to_text(self, board):
        """تبدیل صفحه شطرنج به متن"""
        pieces = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
            '.': '·'
        }
        
        board_str = str(board)
        lines = board_str.split('\n')
        
        result = "  a b c d e f g h\n"
        for i, line in enumerate(reversed(lines)):
            row = 8 - i
            result += f"{row} "
            for char in line.split():
                result += f"{pieces.get(char, char)} "
            result += f"{row}\n"
        result += "  a b c d e f g h"
        
        return result
    
    async def challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """چالش شطرنج"""
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ روی پیام کسی که می‌خوای باهاش بازی کنی ریپلای کن!\n"
                "مثال: روی پیام دوستت ریپلای کن و بزن /chess"
            )
            return
        
        opponent = update.message.reply_to_message.from_user
        user = update.message.from_user
        chat_id = update.message.chat_id
        
        if opponent.id == user.id:
            await update.message.reply_text("❌ نمی‌تونی با خودت بازی کنی!")
            return
        
        game_id = f"{user.id}_{opponent.id}_{random.randint(1000, 9999)}"
        
        # ذخیره چالش
        if chat_id not in self.challenges:
            self.challenges[chat_id] = {}
        
        self.challenges[chat_id][game_id] = {
            'player1': user.id,
            'player2': opponent.id,
            'player1_name': user.first_name,
            'player2_name': opponent.first_name,
            'status': 'pending'
        }
        
        keyboard = [
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"chess_accept_{game_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"chess_reject_{game_id}")
            ]
        ]
        
        await update.message.reply_text(
            f"🎮 **چالش شطرنج!**\n\n"
            f"👤 {user.first_name} می‌خواد با {opponent.first_name} بازی کنه!\n"
            f"⚪ سفید: {user.first_name}\n"
            f"⚫ سیاه: {opponent.first_name}\n\n"
            f"{opponent.first_name} قبول می‌کنی؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def accept_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قبول چالش"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        
        if chat_id not in self.challenges or game_id not in self.challenges[chat_id]:
            await query.edit_message_text("❌ این چالش دیگه وجود نداره!")
            return
        
        challenge = self.challenges[chat_id][game_id]
        
        if user_id != challenge['player2']:
            await query.answer("❌ این چالش مال تو نیست!")
            return
        
        # ساخت بازی جدید
        game = chess.Board()
        
        self.games[game_id] = {
            'board': game,
            'players': {
                challenge['player1']: {'name': challenge['player1_name'], 'color': 'white'},
                challenge['player2']: {'name': challenge['player2_name'], 'color': 'black'}
            },
            'turn': 'white',
            'chat_id': chat_id,
            'last_move': None,
            'selected_square': None
        }
        
        # حذف چالش
        del self.challenges[chat_id][game_id]
        
        # نمایش صفحه
        board_text = self.board_to_text(game)
        
        keyboard = self.get_move_keyboard(game_id)
        
        await query.edit_message_text(
            f"🎮 **بازی شروع شد!**\n\n"
            f"⚪ سفید: {challenge['player1_name']}\n"
            f"⚫ سیاه: {challenge['player2_name']}\n\n"
            f"```\n{board_text}\n```\n"
            f"نوبت: ⚪ سفید",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def reject_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رد چالش"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        chat_id = query.message.chat_id
        
        if chat_id in self.challenges and game_id in self.challenges[chat_id]:
            del self.challenges[chat_id][game_id]
            await query.edit_message_text("❌ چالش رد شد!")
    
    def get_move_keyboard(self, game_id):
        """صفحه کلید حرکات شطرنج"""
        keyboard = [
            [
                InlineKeyboardButton("a", callback_data=f"chess_square_{game_id}_a"),
                InlineKeyboardButton("b", callback_data=f"chess_square_{game_id}_b"),
                InlineKeyboardButton("c", callback_data=f"chess_square_{game_id}_c"),
                InlineKeyboardButton("d", callback_data=f"chess_square_{game_id}_d")
            ],
            [
                InlineKeyboardButton("e", callback_data=f"chess_square_{game_id}_e"),
                InlineKeyboardButton("f", callback_data=f"chess_square_{game_id}_f"),
                InlineKeyboardButton("g", callback_data=f"chess_square_{game_id}_g"),
                InlineKeyboardButton("h", callback_data=f"chess_square_{game_id}_h")
            ],
            [
                InlineKeyboardButton("1", callback_data=f"chess_row_{game_id}_1"),
                InlineKeyboardButton("2", callback_data=f"chess_row_{game_id}_2"),
                InlineKeyboardButton("3", callback_data=f"chess_row_{game_id}_3"),
                InlineKeyboardButton("4", callback_data=f"chess_row_{game_id}_4")
            ],
            [
                InlineKeyboardButton("5", callback_data=f"chess_row_{game_id}_5"),
                InlineKeyboardButton("6", callback_data=f"chess_row_{game_id}_6"),
                InlineKeyboardButton("7", callback_data=f"chess_row_{game_id}_7"),
                InlineKeyboardButton("8", callback_data=f"chess_row_{game_id}_8")
            ],
            [InlineKeyboardButton("✅ تایید حرکت", callback_data=f"chess_move_{game_id}")],
            [InlineKeyboardButton("↩️ لغو", callback_data=f"chess_cancel_{game_id}")]
        ]
        return keyboard
    
    async def square_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب خانه"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        square = data[3]
        
        if game_id not in self.games:
            await query.answer("❌ بازی وجود نداره!")
            return
        
        game = self.games[game_id]
        
        if game['selected_square'] is None:
            game['selected_square'] = square
            await query.answer(f"✅ خانه {square} انتخاب شد")
        else:
            await query.answer("❌ قبلاً یه خونه انتخاب کردی")
    
    async def row_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب ردیف"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        row = data[3]
        
        if game_id not in self.games:
            await query.answer("❌ بازی وجود نداره!")
            return
        
        game = self.games[game_id]
        
        if game['selected_square'] is None:
            await query.answer("❌ اول یه خونه انتخاب کن")
            return
        
        from_square = game['selected_square']
        to_square = f"{from_square}{row}"
        
        # اینجا باید حرکت رو بررسی کنی
        await query.answer(f"حرکت از {from_square} به {to_square}")
        
        # پاک کردن انتخاب
        game['selected_square'] = None
    
    async def make_move(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انجام حرکت"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        
        if game_id not in self.games:
            await query.answer("❌ بازی وجود نداره!")
            return
        
        game = self.games[game_id]
        user_id = query.from_user.id
        
        # چک کردن نوبت
        current_color = game['turn']
        player_color = game['players'][user_id]['color']
        
        if current_color != player_color:
            await query.answer("❌ الان نوبت تو نیست!")
            return
        
        await query.edit_message_text("🎮 بازی ادامه دارد... (در حال توسعه)")
    
    async def cancel_move(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو حرکت"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        game_id = data[2]
        
        if game_id in self.games:
            self.games[game_id]['selected_square'] = None
            await query.answer("✅ انتخاب لغو شد")
