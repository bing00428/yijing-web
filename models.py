# -*- coding: utf-8 -*-

"""models.py - 周易八卦系统数据库模型"""

import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# 数据库路径
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "yijing.db"


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 并发安全
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    c = conn.cursor()

    # 用户表
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 用户资料表
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT DEFAULT '',
            birth_year INTEGER,
            birth_month INTEGER,
            birth_day INTEGER,
            birth_hour INTEGER,
            gender TEXT CHECK(gender IN ('male', 'female', '')),
            phone TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 房屋信息表
    c.execute("""
        CREATE TABLE IF NOT EXISTS fengshui_profiles (
            user_id INTEGER PRIMARY KEY,
            house_type TEXT DEFAULT '',
            total_area REAL,
            room_count INTEGER,
            facing_direction TEXT DEFAULT '',
            built_year INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 起卦记录表
    c.execute("""
        CREATE TABLE IF NOT EXISTS hexagram_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT NOT NULL CHECK(method IN ('coin', 'yarrow', 'time')),
            params TEXT DEFAULT '{}',
            yao_values TEXT NOT NULL,
            moving_lines TEXT DEFAULT '[]',
            original_hexagram TEXT,
            changed_hexagram TEXT,
            result_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 风水分析记录表
    c.execute("""
        CREATE TABLE IF NOT EXISTS fengshui_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            params TEXT DEFAULT '{}',
            result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 收藏表
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hexagram_id TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, hexagram_id)
        )
    """)

    # 索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_hexagram_records_user ON hexagram_records(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fengshui_records_user ON fengshui_records(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id)")

    # 用户行为追踪表
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL CHECK(action_type IN ('page_view', 'feature_use', 'divination', 'search', 'other')),
            feature TEXT NOT NULL,
            params TEXT DEFAULT '{}',
            page TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_user ON user_actions(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_type ON user_actions(action_type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_feature ON user_actions(feature)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_time ON user_actions(created_at)")

    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


# ==================== 用户认证 ====================

def register_user(username, password, email=None):
    """注册用户"""
    conn = get_db()
    try:
        # 检查用户名是否已存在
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return {"success": False, "error": "用户名已存在"}

        existing_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone() if email else None
        if existing_email:
            return {"success": False, "error": "邮箱已被注册"}

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()

        # 自动创建用户资料
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
        conn.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))
        conn.execute("INSERT INTO fengshui_profiles (user_id) VALUES (?)", (user_id,))

        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def login_user(username, password):
    """登录"""
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, email, password_hash, avatar FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return {
            "success": True,
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "avatar": user["avatar"],
        }
    return {"success": False, "error": "用户名或密码错误"}


def get_user_profile(user_id):
    """获取用户资料"""
    conn = get_db()
    user = conn.execute("SELECT id, username, email, avatar, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    profile = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    fengshui = conn.execute("SELECT * FROM fengshui_profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    if not user:
        return None

    return {
        "user": dict(user),
        "profile": dict(profile) if profile else {},
        "fengshui_profile": dict(fengshui) if fengshui else {},
    }


def update_user_profile(user_id, data):
    """更新用户资料"""
    conn = get_db()
    try:
        # 更新 user_profiles
        profile = conn.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if profile:
            conn.execute("""
                UPDATE user_profiles SET
                    nickname = COALESCE(?, nickname),
                    birth_year = COALESCE(?, birth_year),
                    birth_month = COALESCE(?, birth_month),
                    birth_day = COALESCE(?, birth_day),
                    birth_hour = COALESCE(?, birth_hour),
                    gender = COALESCE(?, gender),
                    phone = COALESCE(?, phone)
                WHERE user_id = ?
            """, (
                data.get("nickname"), data.get("birth_year"), data.get("birth_month"),
                data.get("birth_day"), data.get("birth_hour"), data.get("gender"),
                data.get("phone"), user_id
            ))
        else:
            conn.execute("""
                INSERT INTO user_profiles (user_id, nickname, birth_year, birth_month,
                    birth_day, birth_hour, gender, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, data.get("nickname", ""), data.get("birth_year"),
                data.get("birth_month"), data.get("birth_day"), data.get("birth_hour"),
                data.get("gender", ""), data.get("phone", "")
            ))

        # 更新 fengshui_profiles
        fs = conn.execute("SELECT user_id FROM fengshui_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if fs:
            conn.execute("""
                UPDATE fengshui_profiles SET
                    house_type = COALESCE(?, house_type),
                    total_area = COALESCE(?, total_area),
                    room_count = COALESCE(?, room_count),
                    facing_direction = COALESCE(?, facing_direction),
                    built_year = COALESCE(?, built_year)
                WHERE user_id = ?
            """, (
                data.get("house_type"), data.get("total_area"), data.get("room_count"),
                data.get("facing_direction"), data.get("built_year"), user_id
            ))
        else:
            conn.execute("""
                INSERT INTO fengshui_profiles (user_id, house_type, total_area, room_count,
                    facing_direction, built_year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, data.get("house_type", ""), data.get("total_area"),
                data.get("room_count"), data.get("facing_direction", ""),
                data.get("built_year")
            ))

        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def change_password(user_id, old_password, new_password):
    """修改密码"""
    conn = get_db()
    user = conn.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()

    if not user:
        return {"success": False, "error": "用户不存在"}

    if not check_password_hash(user["password_hash"], old_password):
        return {"success": False, "error": "原密码错误"}

    new_hash = generate_password_hash(new_password)
    conn = get_db()
    conn.execute(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_hash, user_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


# ==================== 用户行为追踪 ====================

def log_user_action(user_id, action_type, feature, params=None, page='', duration=0):
    """记录用户行为"""
    conn = get_db()
    conn.execute("""
        INSERT INTO user_actions (user_id, action_type, feature, params, page, duration)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, action_type, feature, json.dumps(params, ensure_ascii=False) if params else '{}', page, duration))
    conn.commit()
    conn.close()


def get_user_analytics(user_id, days=30):
    """获取用户行为统计（最近 N 天）"""
    from datetime import datetime, timedelta
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # 总行为数
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM user_actions WHERE user_id = ? AND created_at >= ?",
        (user_id, cutoff)
    ).fetchone()['cnt']

    # 按功能分布
    features = conn.execute("""
        SELECT feature, COUNT(*) as cnt
        FROM user_actions
        WHERE user_id = ? AND created_at >= ?
        GROUP BY feature ORDER BY cnt DESC
    """, (user_id, cutoff)).fetchall()

    # 按天统计
    daily = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt
        FROM user_actions
        WHERE user_id = ? AND created_at >= ?
        GROUP BY day ORDER BY day
    """, (user_id, cutoff)).fetchall()

    # 停留时长 TOP 页面
    top_pages = conn.execute("""
        SELECT page, AVG(duration) as avg_dur, SUM(duration) as total_dur, COUNT(*) as cnt
        FROM user_actions
        WHERE user_id = ? AND page != '' AND duration > 0 AND created_at >= ?
        GROUP BY page ORDER BY total_dur DESC LIMIT 10
    """, (user_id, cutoff)).fetchall()

    conn.close()

    return {
        'total_actions': total,
        'feature_distribution': [dict(r) for r in features],
        'daily_activity': [dict(r) for r in daily],
        'top_pages': [dict(r) for r in top_pages],
        'first_seen': days,
        'last_seen': days,
    }


def get_all_users_summary(days=30):
    """获取所有用户的简要统计（管理员用）"""
    from datetime import datetime, timedelta
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    rows = conn.execute("""
        SELECT u.id, u.username, u.email, u.created_at,
               COUNT(ua.id) as total_actions,
               MAX(ua.created_at) as last_active
        FROM users u
        LEFT JOIN user_actions ua ON u.id = ua.user_id AND ua.created_at >= ?
        GROUP BY u.id
        ORDER BY total_actions DESC
    """, (cutoff,)).fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ==================== 起卦记录 ====================

def save_hexagram_record(user_id, method, params, yao_values, moving_lines,
                         original_hexagram, changed_hexagram, result_text):
    """保存起卦记录"""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO hexagram_records
                (user_id, method, params, yao_values, moving_lines,
                 original_hexagram, changed_hexagram, result_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, method, json.dumps(params, ensure_ascii=False),
            json.dumps(yao_values), json.dumps(moving_lines),
            original_hexagram, changed_hexagram, result_text
        ))
        conn.commit()
        return {"success": True, "record_id": cursor.lastrowid}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_hexagram_records(user_id, limit=50, offset=0):
    """获取起卦记录"""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, method, params, yao_values, moving_lines,
               original_hexagram, changed_hexagram, result_text, created_at
        FROM hexagram_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset)).fetchall()
    conn.close()

    results = []
    for row in rows:
        r = dict(row)
        r["params"] = json.loads(r["params"]) if r["params"] else {}
        r["yao_values"] = json.loads(r["yao_values"]) if r["yao_values"] else []
        r["moving_lines"] = json.loads(r["moving_lines"]) if r["moving_lines"] else []
        results.append(r)
    return results


# ==================== 风水记录 ====================

def save_fengshui_record(user_id, record_type, params, result):
    """保存风水分析记录"""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO fengshui_records (user_id, type, params, result)
            VALUES (?, ?, ?, ?)
        """, (
            user_id, record_type,
            json.dumps(params, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False)
        ))
        conn.commit()
        return {"success": True, "record_id": cursor.lastrowid}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_fengshui_records(user_id, limit=50, offset=0):
    """获取风水记录"""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, type, params, result, created_at
        FROM fengshui_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset)).fetchall()
    conn.close()

    results = []
    for row in rows:
        r = dict(row)
        r["params"] = json.loads(r["params"]) if r["params"] else {}
        r["result"] = json.loads(r["result"]) if r["result"] else {}
        results.append(r)
    return results


# ==================== 收藏 ====================

def toggle_favorite(user_id, hexagram_id, note=""):
    """收藏/取消收藏卦"""
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM user_favorites WHERE user_id = ? AND hexagram_id = ?",
            (user_id, hexagram_id)
        ).fetchone()

        if existing:
            conn.execute(
                "DELETE FROM user_favorites WHERE user_id = ? AND hexagram_id = ?",
                (user_id, hexagram_id)
            )
            return {"success": True, "favorited": False}
        else:
            conn.execute("""
                INSERT INTO user_favorites (user_id, hexagram_id, note)
                VALUES (?, ?, ?)
            """, (user_id, hexagram_id, note))
            conn.commit()
            return {"success": True, "favorited": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_favorites(user_id):
    """获取收藏列表"""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, hexagram_id, note, created_at
        FROM user_favorites
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
