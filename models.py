# -*- coding: utf-8 -*-

"""models.py - 周易八卦系统数据库模型 (Supabase PostgreSQL)"""

import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text, Column, String, Integer, Boolean, DateTime, JSON, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# Supabase 连接
DB_PASSWORD = os.environ.get('SUPABASE_DB_PASSWORD', 'nDT5oOmUMxulOlX8')
PROJECT_REF = os.environ.get('SUPABASE_PROJECT_REF', 'qkxzmmqhewhpflgyuoud')
DB_HOST = os.environ.get('SUPABASE_DB_HOST', 'aws-0-us-east-1.pooler.supabase.com')
DB_PORT = os.environ.get('SUPABASE_DB_PORT', '5432')
DB_NAME = 'postgres'

DATABASE_URL = f"postgresql://postgres.{PROJECT_REF}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10}
    )
    # 测试连接
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    _db_ready = True
    print(f"✅ Supabase 连接成功")
except Exception as e:
    print(f"❌ Supabase 连接失败: {type(e).__name__}: {str(e)[:300]}")
    _db_ready = False
    engine = None

Base = declarative_base()


# ==================== 数据库模型 ====================

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    avatar = Column(String(500), default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    nickname = Column(String(100), default='')
    birth_year = Column(Integer, nullable=True)
    birth_month = Column(Integer, nullable=True)
    birth_day = Column(Integer, nullable=True)
    birth_hour = Column(Integer, nullable=True)
    gender = Column(String(10), default='')
    phone = Column(String(20), default='')
    created_at = Column(DateTime, default=datetime.utcnow)


class FengshuiProfile(Base):
    __tablename__ = 'fengshui_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    house_type = Column(String(50), default='')
    total_area = Column(Integer, nullable=True)
    room_count = Column(Integer, nullable=True)
    facing_direction = Column(String(20), default='')
    built_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserAction(Base):
    __tablename__ = 'user_actions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    feature = Column(String(100), nullable=False, index=True)
    params = Column(JSON, default={})
    page = Column(String(200), default='')
    duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class HexagramRecord(Base):
    __tablename__ = 'hexagram_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    method = Column(String(20), default='')
    params = Column(JSON, default={})
    yao_values = Column(JSON, default=[])
    moving_lines = Column(JSON, default=[])
    original_hexagram = Column(JSON, default={})
    changed_hexagram = Column(JSON, default={})
    result_text = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class FengshuiRecord(Base):
    __tablename__ = 'fengshui_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(50), default='')
    params = Column(JSON, default={})
    result = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserFavorite(Base):
    __tablename__ = 'user_favorites'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    hexagram_id = Column(String(50), nullable=False)
    note = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('uq_user_hex', 'user_id', 'hexagram_id', unique=True),
    )


def init_db():
    """初始化数据库表"""
    if not _db_ready or engine is None:
        return
    try:
        Base.metadata.create_all(engine)
        print("✅ 数据库表初始化完成")
    except Exception as e:
        print(f"⚠️ 表初始化警告: {e}")


# ==================== 用户认证 ====================

def register_user(username, password, email=None):
    """注册用户"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            # 检查用户名
            result = conn.execute(text("SELECT 1 FROM users WHERE username = :u"), {"u": username})
            if result.fetchone():
                return {"success": False, "error": "用户名已存在"}
            
            if email:
                result = conn.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email})
                if result.fetchone():
                    return {"success": False, "error": "邮箱已被注册"}
            
            now = datetime.utcnow()
            result = conn.execute(
                text("INSERT INTO users (username, email, password_hash, avatar, created_at, updated_at) VALUES (:u, :e, :p, '', :c, :u2)"),
                {"u": username, "e": email, "p": generate_password_hash(password), "c": now, "u2": now}
            )
            user_id = result.inserted_primary_key[0]
            
            # 自动创建用户资料
            conn.execute(
                text("INSERT INTO user_profiles (user_id, nickname, gender) VALUES (:uid, '', '')"),
                {"uid": user_id}
            )
            conn.execute(
                text("INSERT INTO fengshui_profiles (user_id, house_type, facing_direction) VALUES (:uid, '', '')"),
                {"uid": user_id}
            )
        
        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """登录"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, avatar FROM users WHERE username = :u"),
                {"u": username}
            )
            user = result.fetchone()
            if user:
                # 验证密码需要重新查询
                result2 = conn.execute(
                    text("SELECT password_hash FROM users WHERE username = :u"),
                    {"u": username}
                )
                row = result2.fetchone()
                if row and check_password_hash(row[0], password):
                    return {
                        "success": True,
                        "user_id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "avatar": user[3] or "",
                    }
        return {"success": False, "error": "用户名或密码错误"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_profile(user_id):
    """获取用户资料"""
    if not _db_ready:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, avatar, created_at, updated_at FROM users WHERE id = :uid"),
                {"uid": user_id}
            )
            user = result.fetchone()
            if not user:
                return None
            
            profile = conn.execute(
                text("SELECT * FROM user_profiles WHERE user_id = :uid"),
                {"uid": user_id}
            ).fetchone()
            
            fengshui = conn.execute(
                text("SELECT * FROM fengshui_profiles WHERE user_id = :uid"),
                {"uid": user_id}
            ).fetchone()
            
            return {
                "user": dict(user._mapping) if user else None,
                "profile": dict(profile._mapping) if profile else {},
                "fengshui_profile": dict(fengshui._mapping) if fengshui else {},
            }
    except Exception:
        return None


def update_user_profile(user_id, data):
    """更新用户资料"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            profile_fields = ["nickname", "birth_year", "birth_month", "birth_day", "birth_hour", "gender", "phone"]
            profile_updates = {f: data[f] for f in profile_fields if f in data and data[f] is not None}
            if profile_updates:
                set_clauses = ", ".join([f"{k} = :{k}" for k in profile_updates])
                conn.execute(
                    text(f"INSERT INTO user_profiles (user_id, {', '.join(profile_updates.keys())}) VALUES (:uid, {', '.join([':'+k for k in profile_updates.keys()])}) ON CONFLICT (user_id) DO UPDATE SET {set_clauses}"),
                    {**profile_updates, "uid": user_id}
                )
            
            fs_fields = ["house_type", "total_area", "room_count", "facing_direction", "built_year"]
            fs_updates = {f: data[f] for f in fs_fields if f in data and data[f] is not None}
            if fs_updates:
                set_clauses = ", ".join([f"{k} = :{k}" for k in fs_updates])
                conn.execute(
                    text(f"INSERT INTO fengshui_profiles (user_id, {', '.join(fs_updates.keys())}) VALUES (:uid, {', '.join([':'+k for k in fs_updates.keys()])}) ON CONFLICT (user_id) DO UPDATE SET {set_clauses}"),
                    {**fs_updates, "uid": user_id}
                )
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def change_password(user_id, old_password, new_password):
    """修改密码"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT password_hash FROM users WHERE id = :uid"),
                {"uid": user_id}
            )
            user = result.fetchone()
            if not user:
                return {"success": False, "error": "用户不存在"}
            if not check_password_hash(user[0], old_password):
                return {"success": False, "error": "原密码错误"}
            
            conn.execute(
                text("UPDATE users SET password_hash = :ph, updated_at = :now WHERE id = :uid"),
                {"ph": generate_password_hash(new_password), "now": datetime.utcnow(), "uid": user_id}
            )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 用户行为追踪 ====================

def log_user_action(user_id, action_type, feature, params=None, page='', duration=0):
    """记录用户行为"""
    if not _db_ready:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO user_actions (user_id, action_type, feature, params, page, duration, created_at) VALUES (:uid, :at, :f, :p, :pg, :d, :now)"),
                {
                    "uid": user_id, "at": action_type, "f": feature,
                    "p": json.dumps(params, ensure_ascii=False) if params else "{}",
                    "pg": page, "d": duration, "now": datetime.utcnow()
                }
            )
    except Exception:
        pass


def get_user_analytics(user_id, days=30):
    """获取用户行为统计"""
    if not _db_ready:
        return {'total_actions': 0, 'feature_distribution': [], 'daily_activity': [], 'top_pages': []}
    try:
        cutoff = f"(NOW() - INTERVAL '{days} days')"
        with engine.connect() as conn:
            total = conn.execute(
                text("SELECT COUNT(*) FROM user_actions WHERE user_id = :uid AND created_at > :cutoff"),
                {"uid": user_id, "cutoff": cutoff}
            ).scalar() or 0
            
            return {
                'total_actions': total,
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
    if not _db_ready:
        return []
    try:
        cutoff = f"(NOW() - INTERVAL '{days} days')"
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT u.id, u.username, u.email, u.created_at,
                       COUNT(ua.id) as total_actions,
                       MAX(ua.created_at) as last_active
                FROM users u
                LEFT JOIN user_actions ua ON u.id = ua.user_id AND ua.created_at > {cutoff}
                GROUP BY u.id, u.username, u.email, u.created_at
                ORDER BY total_actions DESC
            """)).fetchall()
            
            return [dict(row._mapping) for row in result]
    except Exception:
        return []


# ==================== 起卦记录 ====================

def save_hexagram_record(user_id, method, params, yao_values, moving_lines,
                         original_hexagram, changed_hexagram, result_text):
    """保存起卦记录"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""INSERT INTO hexagram_records 
                        (user_id, method, params, yao_values, moving_lines, 
                         original_hexagram, changed_hexagram, result_text, created_at)
                        VALUES (:uid, :m, :p, :yv, :ml, :oh, :ch, :rt, :now)
                        RETURNING id"""),
                {
                    "uid": user_id, "m": method,
                    "p": json.dumps(params, ensure_ascii=False),
                    "yv": json.dumps(yao_values),
                    "ml": json.dumps(moving_lines),
                    "oh": json.dumps(original_hexagram, ensure_ascii=False),
                    "ch": json.dumps(changed_hexagram, ensure_ascii=False),
                    "rt": result_text,
                    "now": datetime.utcnow()
                }
            )
            return {"success": True, "record_id": result.scalar()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_hexagram_records(user_id, limit=50, offset=0):
    """获取起卦记录"""
    if not _db_ready:
        return []
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM hexagram_records WHERE user_id = :uid ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
                {"uid": user_id, "lim": limit, "off": offset}
            )
            rows = result.fetchall()
            
            results = []
            for row in rows:
                r = dict(row._mapping)
                try:
                    r["params"] = json.loads(r["params"]) if r.get("params") else {}
                except (json.JSONDecodeError, TypeError):
                    r["params"] = {}
                try:
                    r["yao_values"] = json.loads(r["yao_values"]) if r.get("yao_values") else []
                except (json.JSONDecodeError, TypeError):
                    r["yao_values"] = []
                try:
                    r["moving_lines"] = json.loads(r["moving_lines"]) if r.get("moving_lines") else []
                except (json.JSONDecodeError, TypeError):
                    r["moving_lines"] = []
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(r)
            return results
    except Exception:
        return []


# ==================== 风水记录 ====================

def save_fengshui_record(user_id, record_type, params, result):
    """保存风水分析记录"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            result_obj = conn.execute(
                text("""INSERT INTO fengshui_records 
                        (user_id, type, params, result, created_at)
                        VALUES (:uid, :t, :p, :r, :now)
                        RETURNING id"""),
                {
                    "uid": user_id, "t": record_type,
                    "p": json.dumps(params, ensure_ascii=False),
                    "r": json.dumps(result, ensure_ascii=False),
                    "now": datetime.utcnow()
                }
            )
            return {"success": True, "record_id": result_obj.scalar()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_fengshui_records(user_id, limit=50, offset=0):
    """获取风水记录"""
    if not _db_ready:
        return []
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM fengshui_records WHERE user_id = :uid ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
                {"uid": user_id, "lim": limit, "off": offset}
            )
            rows = result.fetchall()
            
            results = []
            for row in rows:
                r = dict(row._mapping)
                try:
                    r["params"] = json.loads(r["params"]) if r.get("params") else {}
                except (json.JSONDecodeError, TypeError):
                    r["params"] = {}
                try:
                    r["result"] = json.loads(r["result"]) if r.get("result") else {}
                except (json.JSONDecodeError, TypeError):
                    r["result"] = {}
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(r)
            return results
    except Exception:
        return []


# ==================== 收藏 ====================

def toggle_favorite(user_id, hexagram_id, note=""):
    """收藏/取消收藏卦"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT 1 FROM user_favorites WHERE user_id = :uid AND hexagram_id = :hid"),
                {"uid": user_id, "hid": hexagram_id}
            ).fetchone()
            
            if existing:
                conn.execute(
                    text("DELETE FROM user_favorites WHERE user_id = :uid AND hexagram_id = :hid"),
                    {"uid": user_id, "hid": hexagram_id}
                )
                return {"success": True, "favorited": False}
            else:
                conn.execute(
                    text("INSERT INTO user_favorites (user_id, hexagram_id, note, created_at) VALUES (:uid, :hid, :n, :now)"),
                    {"uid": user_id, "hid": hexagram_id, "n": note, "now": datetime.utcnow()}
                )
                return {"success": True, "favorited": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_favorites(user_id):
    """获取收藏列表"""
    if not _db_ready:
        return []
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user_favorites WHERE user_id = :uid ORDER BY created_at DESC"),
                {"uid": user_id}
            )
            rows = result.fetchall()
            
            results = []
            for row in rows:
                r = dict(row._mapping)
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(r)
            return results
    except Exception:
        return []


# ==================== 管理员统计 ====================

def get_overview_stats(days=30):
    """获取全站统计"""
    if not _db_ready:
        return {
            'total_users': 0, 'total_actions': 0,
            'active_users_7d': 0, 'today_actions': 0,
            'top_features': [], 'top_users': [],
            'recent_actions': [],
        }
    try:
        cutoff = f"(NOW() - INTERVAL '{days} days')"
        today = "NOW()::date"
        
        with engine.connect() as conn:
            total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            total_actions = conn.execute(text("SELECT COUNT(*) FROM user_actions")).scalar() or 0
            
            active_7d = conn.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM user_actions WHERE created_at > (NOW() - INTERVAL '7 days')")
            ).scalar() or 0
            
            today_actions = conn.execute(
                text("SELECT COUNT(*) FROM user_actions WHERE created_at::date = CURRENT_DATE")
            ).scalar() or 0
            
            top_features = conn.execute(text(f"""
                SELECT feature, COUNT(*) as cnt FROM user_actions
                GROUP BY feature ORDER BY cnt DESC LIMIT 10
            """)).fetchall()
            
            top_users = conn.execute(text(f"""
                SELECT user_id, COUNT(*) as cnt, MAX(created_at) as last_active FROM user_actions
                GROUP BY user_id ORDER BY cnt DESC LIMIT 10
            """)).fetchall()
            
            recent = conn.execute(text("""
                SELECT * FROM user_actions ORDER BY created_at DESC LIMIT 50
            """)).fetchall()
            
            return {
                'total_users': total_users,
                'total_actions': total_actions,
                'active_users_7d': active_7d,
                'today_actions': today_actions,
                'top_features': [{"feature": r[0], "cnt": r[1]} for r in top_features],
                'top_users': [{"user_id": r[0], "cnt": r[1], "last_active": r[2].strftime("%Y-%m-%d %H:%M:%S") if r[2] else ""} for r in top_users],
                'recent_actions': [dict(r._mapping) for r in recent],
            }
    except Exception as e:
        print(f"统计错误: {e}")
        return {
            'total_users': 0, 'total_actions': 0,
            'active_users_7d': 0, 'today_actions': 0,
            'top_features': [], 'top_users': [],
            'recent_actions': [],
        }
