# -*- coding: utf-8 -*-

"""models.py - 周易八卦系统数据库模型 (Supabase PostgreSQL)"""

import json
import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

# Supabase 连接
DB_PASSWORD = os.environ.get('SUPABASE_DB_PASSWORD', 'nDT5oOmUMxulOlX8')
PROJECT_REF = os.environ.get('SUPABASE_PROJECT_REF', 'qkxzmmqhewhpflgyuoud')
# 直连模式（绕过 pooler）
DB_HOST = os.environ.get('SUPABASE_DB_HOST', f'{PROJECT_REF}.supabase.co')
DB_PORT = int(os.environ.get('SUPABASE_DB_PORT', '5432'))
DB_NAME = 'postgres'

_conn_str = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user=postgres.{PROJECT_REF} password={DB_PASSWORD} connect_timeout=10"

_db_ready = False
_conn = None
_cursor = None


def _get_conn():
    """获取数据库连接"""
    global _conn, _db_ready
    if _conn is None:
        try:
            _conn = psycopg2.connect(_conn_str)
            _conn.autocommit = True
            _db_ready = True
            print("✅ Supabase 连接成功")
        except Exception as e:
            print(f"❌ Supabase 连接失败: {type(e).__name__}: {str(e)[:300]}")
            _db_ready = False
    return _conn


def init_db():
    """初始化数据库表"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return
        c = conn.cursor()
        
        # 用户表
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # 用户资料表
        c.execute("""CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            nickname TEXT DEFAULT '',
            birth_year INTEGER,
            birth_month INTEGER,
            birth_day INTEGER,
            birth_hour INTEGER,
            gender TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # 风水资料表
        c.execute("""CREATE TABLE IF NOT EXISTS fengshui_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            house_type TEXT DEFAULT '',
            total_area INTEGER,
            room_count INTEGER,
            facing_direction TEXT DEFAULT '',
            built_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # 用户行为表
        c.execute("""CREATE TABLE IF NOT EXISTS user_actions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            feature TEXT NOT NULL,
            params JSONB DEFAULT '{}',
            page TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_user ON user_actions(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_type ON user_actions(action_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_feature ON user_actions(feature)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_created ON user_actions(created_at)")
        
        # 起卦记录表
        c.execute("""CREATE TABLE IF NOT EXISTS hexagram_records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            method TEXT DEFAULT '',
            params JSONB DEFAULT '{}',
            yao_values JSONB DEFAULT '[]',
            moving_lines JSONB DEFAULT '[]',
            original_hexagram JSONB DEFAULT '{}',
            changed_hexagram JSONB DEFAULT '{}',
            result_text TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_hex_records_user ON hexagram_records(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_hex_records_created ON hexagram_records(created_at)")
        
        # 风水记录表
        c.execute("""CREATE TABLE IF NOT EXISTS fengshui_records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type TEXT DEFAULT '',
            params JSONB DEFAULT '{}',
            result JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_fs_records_user ON fengshui_records(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_fs_records_created ON fengshui_records(created_at)")
        
        # 收藏表
        c.execute("""CREATE TABLE IF NOT EXISTS user_favorites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            hexagram_id TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, hexagram_id)
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_fav_user ON user_favorites(user_id)")
        
        conn.commit()
        print("✅ 数据库表初始化完成")
    except Exception as e:
        print(f"⚠️ 表初始化警告: {e}")


# ==================== 用户认证 ====================

def register_user(username, password, email=None):
    """注册用户"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        
        c.execute("SELECT id FROM users WHERE username = %s", (username,))
        if c.fetchone():
            return {"success": False, "error": "用户名已存在"}
        
        if email:
            c.execute("SELECT id FROM users WHERE email = %s", (email,))
            if c.fetchone():
                return {"success": False, "error": "邮箱已被注册"}
        
        now = datetime.utcnow()
        c.execute(
            "INSERT INTO users (username, email, password_hash, avatar, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (username, email, generate_password_hash(password), '', now, now)
        )
        user_id = c.fetchone()[0]
        
        c.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (user_id,))
        c.execute("INSERT INTO fengshui_profiles (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        
        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """登录"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        
        c.execute("SELECT id, username, email, avatar, password_hash FROM users WHERE username = %s", (username,))
        row = c.fetchone()
        if row and check_password_hash(row[4], password):
            return {
                "success": True,
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "avatar": row[3] or "",
            }
        return {"success": False, "error": "用户名或密码错误"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_profile(user_id):
    """获取用户资料"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return None
        c = conn.cursor()
        
        c.execute("SELECT id, username, email, avatar, created_at, updated_at FROM users WHERE id = %s", (user_id,))
        user = c.fetchone()
        if not user:
            return None
        
        c.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = c.fetchone()
        
        c.execute("SELECT * FROM fengshui_profiles WHERE user_id = %s", (user_id,))
        fengshui = c.fetchone()
        
        return {
            "user": dict(zip(["id", "username", "email", "avatar", "created_at", "updated_at"], user)) if user else None,
            "profile": dict(zip([desc[0] for desc in c.description], profile)) if profile else {},
            "fengshui_profile": dict(zip([desc[0] for desc in c.description], fengshui)) if fengshui else {},
        }
    except Exception:
        return None


def update_user_profile(user_id, data):
    """更新用户资料"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        
        profile_fields = ["nickname", "birth_year", "birth_month", "birth_day", "birth_hour", "gender", "phone"]
        profile_vals = []
        profile_set = []
        for f in profile_fields:
            if f in data and data[f] is not None:
                profile_set.append(f"{f} = %s")
                profile_vals.append(data[f])
        if profile_set:
            profile_vals.append(user_id)
            c.execute(f"INSERT INTO user_profiles (user_id, {', '.join(profile_set)}) VALUES (%s, {', '.join(['%s' for _ in profile_set])}) ON CONFLICT (user_id) DO UPDATE SET {', '.join(profile_set)}", profile_vals)
        
        fs_fields = ["house_type", "total_area", "room_count", "facing_direction", "built_year"]
        fs_vals = []
        fs_set = []
        for f in fs_fields:
            if f in data and data[f] is not None:
                fs_set.append(f"{f} = %s")
                fs_vals.append(data[f])
        if fs_set:
            fs_vals.append(user_id)
            c.execute(f"INSERT INTO fengshui_profiles (user_id, {', '.join(fs_set)}) VALUES (%s, {', '.join(['%s' for _ in fs_set])}) ON CONFLICT (user_id) DO UPDATE SET {', '.join(fs_set)}", fs_vals)
        
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def change_password(user_id, old_password, new_password):
    """修改密码"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        
        c.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        row = c.fetchone()
        if not row:
            return {"success": False, "error": "用户不存在"}
        if not check_password_hash(row[0], old_password):
            return {"success": False, "error": "原密码错误"}
        
        c.execute("UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                  (generate_password_hash(new_password), user_id))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 用户行为追踪 ====================

def log_user_action(user_id, action_type, feature, params=None, page='', duration=0):
    """记录用户行为"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return
        c = conn.cursor()
        c.execute(
            "INSERT INTO user_actions (user_id, action_type, feature, params, page, duration, created_at) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
            (user_id, action_type, feature, json.dumps(params, ensure_ascii=False) if params else '{}', page, duration)
        )
        conn.commit()
    except Exception:
        pass


def get_user_analytics(user_id, days=30):
    """获取用户行为统计"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {'total_actions': 0, 'feature_distribution': [], 'daily_activity': [], 'top_pages': []}
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM user_actions WHERE user_id = %s AND created_at > NOW() - INTERVAL '%s days'", (user_id, days))
        total = c.fetchone()[0]
        
        return {
            'total_actions': total or 0,
            'feature_distribution': [],
            'daily_activity': [],
            'top_pages': [],
            'first_seen': days,
            'last_seen': days,
        }
    except Exception:
        return {'total_actions': 0, 'feature_distribution': [], 'daily_activity': [], 'top_pages': []}


def get_all_users_summary(days=30):
    """获取所有用户的简要统计"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return []
        c = conn.cursor()
        
        c.execute("""SELECT u.id, u.username, u.email, u.created_at,
                         COUNT(ua.id) as total_actions, MAX(ua.created_at) as last_active
                  FROM users u LEFT JOIN user_actions ua ON u.id = ua.user_id AND ua.created_at > NOW() - INTERVAL '%s days'
                  GROUP BY u.id, u.username, u.email, u.created_at ORDER BY total_actions DESC""" % days)
        
        cols = [desc[0] for desc in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]
    except Exception:
        return []


# ==================== 起卦记录 ====================

def save_hexagram_record(user_id, method, params, yao_values, moving_lines,
                         original_hexagram, changed_hexagram, result_text):
    """保存起卦记录"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        c.execute(
            """INSERT INTO hexagram_records (user_id, method, params, yao_values, moving_lines,
                 original_hexagram, changed_hexagram, result_text, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING id""",
            (user_id, method, json.dumps(params, ensure_ascii=False),
             json.dumps(yao_values), json.dumps(moving_lines),
             json.dumps(original_hexagram, ensure_ascii=False),
             json.dumps(changed_hexagram, ensure_ascii=False), result_text)
        )
        record_id = c.fetchone()[0]
        conn.commit()
        return {"success": True, "record_id": record_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_hexagram_records(user_id, limit=50, offset=0):
    """获取起卦记录"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return []
        c = conn.cursor()
        c.execute("SELECT * FROM hexagram_records WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                  (user_id, limit, offset))
        
        cols = [desc[0] for desc in c.description]
        rows = c.fetchall()
        
        results = []
        for row in rows:
            r = dict(zip(cols, row))
            for field in ['params', 'yao_values', 'moving_lines', 'original_hexagram', 'changed_hexagram']:
                if r.get(field):
                    try:
                        r[field] = json.loads(r[field])
                    except (json.JSONDecodeError, TypeError):
                        r[field] = {} if field in ['params', 'original_hexagram', 'changed_hexagram'] else []
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            results.append(r)
        return results
    except Exception:
        return []


# ==================== 风水记录 ====================

def save_fengshui_record(user_id, record_type, params, result):
    """保存风水分析记录"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        c.execute(
            """INSERT INTO fengshui_records (user_id, type, params, result, created_at)
               VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING id""",
            (user_id, record_type, json.dumps(params, ensure_ascii=False),
             json.dumps(result, ensure_ascii=False))
        )
        record_id = c.fetchone()[0]
        conn.commit()
        return {"success": True, "record_id": record_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_fengshui_records(user_id, limit=50, offset=0):
    """获取风水记录"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return []
        c = conn.cursor()
        c.execute("SELECT * FROM fengshui_records WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                  (user_id, limit, offset))
        
        cols = [desc[0] for desc in c.description]
        rows = c.fetchall()
        
        results = []
        for row in rows:
            r = dict(zip(cols, row))
            for field in ['params', 'result']:
                if r.get(field):
                    try:
                        r[field] = json.loads(r[field])
                    except (json.JSONDecodeError, TypeError):
                        r[field] = {}
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            results.append(r)
        return results
    except Exception:
        return []


# ==================== 收藏 ====================

def toggle_favorite(user_id, hexagram_id, note=""):
    """收藏/取消收藏卦"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return {"success": False, "error": "数据库未连接"}
        c = conn.cursor()
        
        c.execute("SELECT id FROM user_favorites WHERE user_id = %s AND hexagram_id = %s", (user_id, hexagram_id))
        if c.fetchone():
            c.execute("DELETE FROM user_favorites WHERE user_id = %s AND hexagram_id = %s", (user_id, hexagram_id))
            conn.commit()
            return {"success": True, "favorited": False}
        else:
            c.execute("INSERT INTO user_favorites (user_id, hexagram_id, note, created_at) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                      (user_id, hexagram_id, note))
            conn.commit()
            return {"success": True, "favorited": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_favorites(user_id):
    """获取收藏列表"""
    try:
        conn = _get_conn()
        if not _db_ready:
            return []
        c = conn.cursor()
        c.execute("SELECT * FROM user_favorites WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        
        cols = [desc[0] for desc in c.description]
        rows = c.fetchall()
        
        results = []
        for row in rows:
            r = dict(zip(cols, row))
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            results.append(r)
        return results
    except Exception:
        return []


# ==================== 管理员统计 ====================

def get_overview_stats(days=30):
    """获取全站统计"""
    default = {
        'total_users': 0, 'total_actions': 0,
        'active_users_7d': 0, 'today_actions': 0,
        'top_features': [], 'top_users': [],
        'recent_actions': [],
    }
    try:
        conn = _get_conn()
        if not _db_ready:
            return default
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM user_actions")
        total_actions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions WHERE created_at > NOW() - INTERVAL '7 days'")
        active_7d = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM user_actions WHERE created_at::date = CURRENT_DATE")
        today_actions = c.fetchone()[0] or 0
        
        c.execute("SELECT feature, COUNT(*) as cnt FROM user_actions GROUP BY feature ORDER BY cnt DESC LIMIT 10")
        top_features = [{"feature": r[0], "cnt": r[1]} for r in c.fetchall()]
        
        c.execute("SELECT user_id, COUNT(*) as cnt, MAX(created_at) as last_active FROM user_actions GROUP BY user_id ORDER BY cnt DESC LIMIT 10")
        top_users = [{"user_id": r[0], "cnt": r[1], "last_active": r[2].strftime('%Y-%m-%d %H:%M:%S') if r[2] else ""} for r in c.fetchall()]
        
        c.execute("SELECT * FROM user_actions ORDER BY created_at DESC LIMIT 50")
        cols = [desc[0] for desc in c.description]
        recent_actions = []
        for row in c.fetchall():
            r = dict(zip(cols, row))
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            try:
                r['params'] = json.loads(r['params']) if r.get('params') else {}
            except (json.JSONDecodeError, TypeError):
                r['params'] = {}
            recent_actions.append(r)
        
        return {
            'total_users': total_users,
            'total_actions': total_actions,
            'active_users_7d': active_7d,
            'today_actions': today_actions,
            'top_features': top_features,
            'top_users': top_users,
            'recent_actions': recent_actions,
        }
    except Exception as e:
        print(f"统计错误: {e}")
        return default
