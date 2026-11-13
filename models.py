# -*- coding: utf-8 -*-

"""models.py - 周易八卦系统数据库模型 (MongoDB)"""

import json
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB 连接
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://test:test@cluster0.mongodb.net/test?retryWrites=true&w=majority')
DB_NAME = os.environ.get('MONGODB_DB', 'yijing_web')

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    mongo_client.admin.command('ping')
    db = mongo_client[DB_NAME]
    _mongo_ready = True
    print(f"✅ MongoDB 连接成功: {DB_NAME}")
except Exception as e:
    print(f"❌ MongoDB 连接失败: {type(e).__name__}: {e}")
    print(f"   MONGODB_URI: {MONGO_URI.split('@')[0]}@...")
    print(f"   MONGODB_DB: {DB_NAME}")
    print(f"   URI length: {len(MONGO_URI)}")
    import os
    print(f"   Render instance: {os.environ.get('RENDER', 'false')}")
    db = None
    _mongo_ready = False


def _ensure_collections():
    """确保索引存在"""
    if not _mongo_ready or db is None:
        return
    try:
        # 用户索引
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True, sparse=True)
        
        # 行为索引
        db.user_actions.create_index([("user_id", 1), ("created_at", -1)])
        db.user_actions.create_index([("action_type", 1), ("created_at", -1)])
        db.user_actions.create_index([("feature", 1), ("created_at", -1)])
        db.user_actions.create_index([("created_at", -1)])
        
        # 记录索引
        db.hexagram_records.create_index([("user_id", 1), ("created_at", -1)])
        db.fengshui_records.create_index([("user_id", 1), ("created_at", -1)])
        
        # 收藏唯一索引
        db.user_favorites.create_index([("user_id", 1), ("hexagram_id", 1)], unique=True)
    except Exception as e:
        print(f"索引创建警告: {e}")


# 初始化
_ensure_collections()


# ==================== 用户认证 ====================

def register_user(username, password, email=None):
    """注册用户"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    
    try:
        # 检查用户名是否已存在
        if db.users.find_one({"username": username}):
            return {"success": False, "error": "用户名已存在"}
        
        if email and db.users.find_one({"email": email}):
            return {"success": False, "error": "邮箱已被注册"}
        
        now = datetime.utcnow()
        user_id = db.users.insert_one({
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "avatar": "",
            "created_at": now,
            "updated_at": now,
        }).inserted_id
        
        # 自动创建用户资料
        db.user_profiles.insert_one({"user_id": user_id, "nickname": "", "gender": ""})
        db.fengshui_profiles.insert_one({"user_id": user_id, "house_type": "", "facing_direction": ""})
        
        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """登录"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    
    user = db.users.find_one({"username": username})
    if user and check_password_hash(user["password_hash"], password):
        return {
            "success": True,
            "user_id": user["_id"],
            "username": user["username"],
            "email": user.get("email"),
            "avatar": user.get("avatar", ""),
        }
    return {"success": False, "error": "用户名或密码错误"}


def get_user_profile(user_id):
    """获取用户资料"""
    if not _mongo_ready:
        return None
    
    user = db.users.find_one({"_id": user_id}, {"password_hash": 0})
    if not user:
        return None
    
    profile = db.user_profiles.find_one({"user_id": user_id}) or {}
    fengshui = db.fengshui_profiles.find_one({"user_id": user_id}) or {}
    
    return {
        "user": user,
        "profile": profile,
        "fengshui_profile": fengshui,
    }


def update_user_profile(user_id, data):
    """更新用户资料"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    
    try:
        # 更新 user_profiles
        update_fields = {}
        for field in ["nickname", "birth_year", "birth_month", "birth_day", "birth_hour", "gender", "phone"]:
            if field in data and data[field] is not None:
                update_fields[field] = data[field]
        if update_fields:
            db.user_profiles.update_one(
                {"user_id": user_id},
                {"$set": update_fields},
                upsert=True
            )
        
        # 更新 fengshui_profiles
        fs_fields = {}
        for field in ["house_type", "total_area", "room_count", "facing_direction", "built_year"]:
            if field in data and data[field] is not None:
                fs_fields[field] = data[field]
        if fs_fields:
            db.fengshui_profiles.update_one(
                {"user_id": user_id},
                {"$set": fs_fields},
                upsert=True
            )
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def change_password(user_id, old_password, new_password):
    """修改密码"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    
    user = db.users.find_one({"_id": user_id})
    if not user:
        return {"success": False, "error": "用户不存在"}
    
    if not check_password_hash(user["password_hash"], old_password):
        return {"success": False, "error": "原密码错误"}
    
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"password_hash": generate_password_hash(new_password), "updated_at": datetime.utcnow()}}
    )
    return {"success": True}


# ==================== 用户行为追踪 ====================

def log_user_action(user_id, action_type, feature, params=None, page='', duration=0):
    """记录用户行为"""
    if not _mongo_ready:
        return
    try:
        db.user_actions.insert_one({
            "user_id": user_id,
            "action_type": action_type,
            "feature": feature,
            "params": json.dumps(params, ensure_ascii=False) if params else '{}',
            "page": page,
            "duration": duration,
            "created_at": datetime.utcnow(),
        })
    except Exception:
        pass


def get_user_analytics(user_id, days=30):
    """获取用户行为统计（最近 N 天）"""
    if not _mongo_ready:
        return {'total_actions': 0, 'feature_distribution': [], 'daily_activity': [], 'top_pages': []}
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 总行为数
        total = db.user_actions.count_documents({
            "user_id": user_id, "created_at": {"$gte": cutoff}
        })
        
        # 按功能分布
        features = list(db.user_actions.aggregate([
            {"$match": {"user_id": user_id, "created_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$feature", "cnt": {"$sum": 1}}},
            {"$sort": {"cnt": -1}},
        ]))
        
        # 按天统计
        daily = list(db.user_actions.aggregate([
            {"$match": {"user_id": user_id, "created_at": {"$gte": cutoff}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "cnt": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
        ]))
        
        # 停留时长 TOP 页面
        top_pages = list(db.user_actions.aggregate([
            {"$match": {"user_id": user_id, "page": {"$ne": ""}, "duration": {"$gt": 0}, "created_at": {"$gte": cutoff}}},
            {"$group": {
                "_id": "$page",
                "avg_dur": {"$avg": "$duration"},
                "total_dur": {"$sum": "$duration"},
                "cnt": {"$sum": 1}
            }},
            {"$sort": {"total_dur": -1}},
            {"$limit": 10},
        ]))
        
        return {
            'total_actions': total,
            'feature_distribution': [{"feature": r["_id"], "cnt": r["cnt"]} for r in features],
            'daily_activity': [{"day": r["_id"], "cnt": r["cnt"]} for r in daily],
            'top_pages': [{"page": r["_id"], "avg_dur": r["avg_dur"], "total_dur": r["total_dur"], "cnt": r["cnt"]} for r in top_pages],
            'first_seen': days,
            'last_seen': days,
        }
    except Exception:
        return {'total_actions': 0, 'feature_distribution': [], 'daily_activity': [], 'top_pages': []}


def get_all_users_summary(days=30):
    """获取所有用户的简要统计（管理员用）"""
    if not _mongo_ready:
        return []
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        rows = list(db.users.aggregate([
            {"$lookup": {
                "from": "user_actions",
                "let": {"uid": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$and": [
                        {"$eq": ["$user_id", "$$uid"]},
                        {"$gte": ["$created_at", cutoff]}
                    ]}}},
                    {"$group": {"_id": None, "total_actions": {"$sum": 1}, "last_active": {"$max": "$created_at"}}}
                ],
                "as": "actions"
            }},
            {"$project": {
                "id": "$_id",
                "username": 1,
                "email": 1,
                "created_at": 1,
                "total_actions": {"$ifNull": [{"$arrayElemAt": ["$actions.total_actions", 0]}, 0]},
                "last_active": {"$ifNull": [{"$arrayElemAt": ["$actions.last_active", None]}, None]}
            }},
            {"$sort": {"total_actions": -1}},
        ]))
        
        return rows
    except Exception:
        return []


# ==================== 起卦记录 ====================

def save_hexagram_record(user_id, method, params, yao_values, moving_lines,
                         original_hexagram, changed_hexagram, result_text):
    """保存起卦记录"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        record_id = db.hexagram_records.insert_one({
            "user_id": user_id,
            "method": method,
            "params": json.dumps(params, ensure_ascii=False),
            "yao_values": json.dumps(yao_values),
            "moving_lines": json.dumps(moving_lines),
            "original_hexagram": original_hexagram,
            "changed_hexagram": changed_hexagram,
            "result_text": result_text,
            "created_at": datetime.utcnow(),
        }).inserted_id
        return {"success": True, "record_id": record_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_hexagram_records(user_id, limit=50, offset=0):
    """获取起卦记录"""
    if not _mongo_ready:
        return []
    
    rows = list(db.hexagram_records.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(offset).limit(limit))
    
    results = []
    for row in rows:
        r = dict(row)
        r.pop("_id", None)
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


# ==================== 风水记录 ====================

def save_fengshui_record(user_id, record_type, params, result):
    """保存风水分析记录"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        record_id = db.fengshui_records.insert_one({
            "user_id": user_id,
            "type": record_type,
            "params": json.dumps(params, ensure_ascii=False),
            "result": json.dumps(result, ensure_ascii=False),
            "created_at": datetime.utcnow(),
        }).inserted_id
        return {"success": True, "record_id": record_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_fengshui_records(user_id, limit=50, offset=0):
    """获取风水记录"""
    if not _mongo_ready:
        return []
    
    rows = list(db.fengshui_records.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(offset).limit(limit))
    
    results = []
    for row in rows:
        r = dict(row)
        r.pop("_id", None)
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


# ==================== 收藏 ====================

def toggle_favorite(user_id, hexagram_id, note=""):
    """收藏/取消收藏卦"""
    if not _mongo_ready:
        return {"success": False, "error": "数据库未连接"}
    
    try:
        existing = db.user_favorites.find_one({"user_id": user_id, "hexagram_id": hexagram_id})
        
        if existing:
            db.user_favorites.delete_one({"user_id": user_id, "hexagram_id": hexagram_id})
            return {"success": True, "favorited": False}
        else:
            db.user_favorites.insert_one({
                "user_id": user_id,
                "hexagram_id": hexagram_id,
                "note": note,
                "created_at": datetime.utcnow(),
            })
            return {"success": True, "favorited": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_favorites(user_id):
    """获取收藏列表"""
    if not _mongo_ready:
        return []
    
    rows = list(db.user_favorites.find(
        {"user_id": user_id}
    ).sort("created_at", -1))
    
    results = []
    for row in rows:
        r = dict(row)
        r.pop("_id", None)
        if r.get("created_at"):
            r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        results.append(r)
    return results


# ==================== 管理员统计 ====================

def get_overview_stats(days=30):
    """获取全站统计（管理员用）"""
    if not _mongo_ready:
        return {
            'total_users': 0, 'total_actions': 0,
            'active_users_7d': 0, 'today_actions': 0,
            'top_features': [], 'top_users': [],
            'recent_actions': [],
        }
    
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        
        # 总用户数
        total_users = db.users.count_documents({})
        
        # 总行为数
        total_actions = db.user_actions.count_documents({})
        
        # 近 7 日活跃用户
        active_users_7d = db.user_actions.distinct("user_id", {"created_at": {"$gte": week_ago}})
        
        # 今日行为数
        today_actions = db.user_actions.count_documents({"created_at": {"$gte": today}})
        
        # 热门功能 TOP 10
        top_features = list(db.user_actions.aggregate([
            {"$group": {"_id": "$feature", "cnt": {"$sum": 1}}},
            {"$sort": {"cnt": -1}},
            {"$limit": 10},
        ]))
        
        # 活跃用户 TOP 10
        top_users = list(db.user_actions.aggregate([
            {"$group": {"_id": "$user_id", "cnt": {"$sum": 1}, "last_active": {"$max": "$created_at"}}},
            {"$sort": {"cnt": -1}},
            {"$limit": 10},
        ]))
        
        # 最近 50 条行为
        recent_actions = list(db.user_actions.find().sort("created_at", -1).limit(50))
        for a in recent_actions:
            a.pop("_id", None)
            if a.get("created_at"):
                a["created_at"] = a["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            # 解析 params
            try:
                a["params"] = json.loads(a["params"]) if a.get("params") else {}
            except (json.JSONDecodeError, TypeError):
                a["params"] = {}
        
        return {
            'total_users': total_users,
            'total_actions': total_actions,
            'active_users_7d': len(active_users_7d),
            'today_actions': today_actions,
            'top_features': [{"feature": r["_id"], "cnt": r["cnt"]} for r in top_features],
            'top_users': [{"user_id": r["_id"], "cnt": r["cnt"], "last_active": r["last_active"].strftime("%Y-%m-%d %H:%M:%S") if r.get("last_active") else ""} for r in top_users],
            'recent_actions': recent_actions,
        }
    except Exception as e:
        print(f"统计错误: {e}")
        return {
            'total_users': 0, 'total_actions': 0,
            'active_users_7d': 0, 'today_actions': 0,
            'top_features': [], 'top_users': [],
            'recent_actions': [],
        }
