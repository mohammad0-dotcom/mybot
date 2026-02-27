import sqlite3
from datetime import datetime
from bot.config import logger

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        logger.info("✅ دیتابیس راه‌اندازی شد")
    
    def create_tables(self):
        # جدول کاربران
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                warnings INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                joined_at TIMESTAMP,
                last_active TIMESTAMP
            )
        ''')
        
        # جدول گروه‌ها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_title TEXT,
                anti_link INTEGER DEFAULT 1,
                anti_forward INTEGER DEFAULT 1,
                anti_spam INTEGER DEFAULT 1,
                warn_limit INTEGER DEFAULT 3,
                welcome_message TEXT DEFAULT 'به گروه خوش آمدید!',
                welcome_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP
            )
        ''')
        
        # جدول مدیران
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                group_id INTEGER,
                user_id INTEGER,
                added_by INTEGER,
                added_at TIMESTAMP,
                PRIMARY KEY (group_id, user_id)
            )
        ''')
        
        # جدول کلمات فیلتر
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS filters (
                group_id INTEGER,
                word TEXT,
                added_by INTEGER,
                added_at TIMESTAMP,
                PRIMARY KEY (group_id, word)
            )
        ''')
        
        # جدول آمار بازی‌ها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER,
                game_name TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, game_name)
            )
        ''')
        
        self.conn.commit()
    
    # ========== کاربران ==========
    def add_user(self, user_id, username, first_name):
        now = datetime.now()
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, now, now))
        self.conn.commit()
    
    def update_user_activity(self, user_id):
        self.cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', 
                          (datetime.now(), user_id))
        self.conn.commit()
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def add_warning(self, user_id):
        self.cursor.execute('UPDATE users SET warnings = warnings + 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def reset_warnings(self, user_id):
        self.cursor.execute('UPDATE users SET warnings = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def ban_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def is_banned(self, user_id):
        self.cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    # ========== گروه‌ها ==========
    def add_group(self, group_id, group_title):
        self.cursor.execute('''
            INSERT OR IGNORE INTO groups (group_id, group_title, created_at)
            VALUES (?, ?, ?)
        ''', (group_id, group_title, datetime.now()))
        self.conn.commit()
    
    def get_group(self, group_id):
        self.cursor.execute('SELECT * FROM groups WHERE group_id = ?', (group_id,))
        return self.cursor.fetchone()
    
    def update_group(self, group_id, setting, value):
        self.cursor.execute(f'UPDATE groups SET {setting} = ? WHERE group_id = ?', (value, group_id))
        self.conn.commit()
    
    # ========== مدیران ==========
    def add_admin(self, group_id, user_id, added_by):
        self.cursor.execute('''
            INSERT OR IGNORE INTO admins (group_id, user_id, added_by, added_at)
            VALUES (?, ?, ?, ?)
        ''', (group_id, user_id, added_by, datetime.now()))
        self.conn.commit()
    
    def remove_admin(self, group_id, user_id):
        self.cursor.execute('DELETE FROM admins WHERE group_id = ? AND user_id = ?', (group_id, user_id))
        self.conn.commit()
    
    def is_admin(self, group_id, user_id):
        self.cursor.execute('SELECT * FROM admins WHERE group_id = ? AND user_id = ?', (group_id, user_id))
        return self.cursor.fetchone() is not None
    
    # ========== فیلتر کلمات ==========
    def add_filter(self, group_id, word, added_by):
        self.cursor.execute('''
            INSERT OR IGNORE INTO filters (group_id, word, added_by, added_at)
            VALUES (?, ?, ?, ?)
        ''', (group_id, word, added_by, datetime.now()))
        self.conn.commit()
    
    def remove_filter(self, group_id, word):
        self.cursor.execute('DELETE FROM filters WHERE group_id = ? AND word = ?', (group_id, word))
        self.conn.commit()
    
    def get_filters(self, group_id):
        self.cursor.execute('SELECT word FROM filters WHERE group_id = ?', (group_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    # ========== آمار بازی ==========
    def update_game_stats(self, user_id, game_name, result, score=0):
        if result == 'win':
            self.cursor.execute('''
                INSERT INTO game_stats (user_id, game_name, wins, losses, draws, score)
                VALUES (?, ?, 1, 0, 0, ?)
                ON CONFLICT(user_id, game_name) DO UPDATE SET 
                    wins = wins + 1,
                    score = score + ?
            ''', (user_id, game_name, score, score))
        elif result == 'loss':
            self.cursor.execute('''
                INSERT INTO game_stats (user_id, game_name, wins, losses, draws, score)
                VALUES (?, ?, 0, 1, 0, 0)
                ON CONFLICT(user_id, game_name) DO UPDATE SET 
                    losses = losses + 1
            ''', (user_id, game_name))
        self.conn.commit()
    
    def get_top_players(self, game_name, limit=10):
        self.cursor.execute('''
            SELECT user_id, wins, score FROM game_stats 
            WHERE game_name = ? ORDER BY score DESC LIMIT ?
        ''', (game_name, limit))
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()
