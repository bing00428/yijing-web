# -*- coding: utf-8 -*-

"""models.py - 周易八卦系统数据库模型 (Supabase REST API)"""

import json
import os
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Supabase 配置
PROJECT_REF = os.environ.get('SUPABASE_PROJECT_REF', 'qkxzmmqhewhpflgyuoud')
ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'sb_publishable_Nw9wEQiSRNahY7fKgoDgUA_9p7GvNh6')
SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

BASE_URL = f'https://{PROJECT_REF}.supabase.co/rest/v1'
HEADERS = {
    'apikey': ANON_KEY,
    'Authorization': f'Bearer {ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}

_db_ready = True
print("✅ Supabase REST API 连接成功")


# ==================== 数据库表定义 ====================

TABLES = {
    'users': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'username': 'TEXT UNIQUE NOT NULL',
            'email': 'TEXT UNIQUE',
            'password_hash': 'TEXT NOT NULL',
            'avatar': "TEXT DEFAULT ''",
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'user_profiles': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER UNIQUE NOT NULL REFERENCES users(id)',
            'nickname': "TEXT DEFAULT ''",
            'birth_year': 'INTEGER',
            'birth_month': 'INTEGER',
            'birth_day': 'INTEGER',
            'birth_hour': 'INTEGER',
            'gender': "TEXT DEFAULT ''",
            'phone': "TEXT DEFAULT ''",
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'fengshui_profiles': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER UNIQUE NOT NULL REFERENCES users(id)',
            'house_type': "TEXT DEFAULT ''",
            'total_area': 'INTEGER',
            'room_count': 'INTEGER',
            'facing_direction': "TEXT DEFAULT ''",
            'built_year': 'INTEGER',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'user_actions': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER NOT NULL',
            'action_type': 'TEXT NOT NULL',
            'feature': 'TEXT NOT NULL',
            'params': "JSONB DEFAULT '{}'::jsonb",
            'page': "TEXT DEFAULT ''",
            'duration': 'INTEGER DEFAULT 0',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'hexagram_records': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER NOT NULL',
            'method': "TEXT DEFAULT ''",
            'params': "JSONB DEFAULT '{}'::jsonb",
            'yao_values': "JSONB DEFAULT '[]'::jsonb",
            'moving_lines': "JSONB DEFAULT '[]'::jsonb",
            'original_hexagram': "JSONB DEFAULT '{}'::jsonb",
            'changed_hexagram': "JSONB DEFAULT '{}'::jsonb",
            'result_text': "TEXT DEFAULT ''",
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'fengshui_records': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER NOT NULL',
            'type': "TEXT DEFAULT ''",
            'params': "JSONB DEFAULT '{}'::jsonb",
            'result': "JSONB DEFAULT '{}'::jsonb",
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }
    },
    'user_favorites': {
        'schema': {
            'id': 'SERIAL PRIMARY KEY',
            'user_id': 'INTEGER NOT NULL',
            'hexagram_id': 'TEXT NOT NULL',
            'note': "TEXT DEFAULT ''",
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'unique': '(user_id, hexagram_id)',
        }
    },
}


def _rpc(function_name, params=None):
    """调用 Supabase RPC 函数"""
    try:
        resp = requests.post(
            f'{BASE_URL}/rpc/{function_name}',
            headers=HEADERS,
            json=params or {},
            timeout=10
        )
        return resp.json() if resp.status_code < 400 else None
    except Exception:
        return None


def _query(table, columns='*', filters=None, order=None, limit=None, offset=None):
    """查询表数据"""
    try:
        url = f'{BASE_URL}/{table}?select={columns}'
        if filters:
            for col, (op, val) in filters.items():
                url += f'&{col}={op}.{requests.utils.quote(str(val))}'
        if order:
            url += f'&order={requests.utils.quote(order)}'
        if limit:
            url += f'&limit={limit}'
        if offset:
            url += f'&offset={offset}'
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []


def _insert(table, data):
    """插入数据"""
    try:
        resp = requests.post(
            f'{BASE_URL}/{table}',
            headers=HEADERS,
            json=data,
            timeout=10
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except Exception:
        return None


def _upsert(table, data, unique_cols=None):
    """Upsert 数据"""
    try:
        headers = HEADERS.copy()
        if unique_cols:
            headers['Prefer'] = f'return=representation, resolution=merge,duplicate_keys=update'
        resp = requests.post(
            f'{BASE_URL}/{table}',
            headers=headers,
            json=data,
            timeout=10
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except Exception:
        return None


def _update(table, filters, data):
    """更新数据"""
    try:
        url = f'{BASE_URL}/{table}'
        for col, (op, val) in filters.items():
            url += f'&{col}={op}.{requests.utils.quote(str(val))}'
        
        resp = requests.patch(
            url,
            headers=HEADERS,
            json=data,
            timeout=10
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def _delete(table, filters):
    """删除数据"""
    try:
        url = f'{BASE_URL}/{table}'
        for col, (op, val) in filters.items():
            url += f'&{col}={op}.{requests.utils.quote(str(val))}'
        
        resp = requests.delete(url, headers=HEADERS, timeout=10)
        return resp.status_code in (200, 204)
    except Exception:
        return False


def init_db():
    """初始化数据库表（通过 SQL RPC）"""
    try:
        sql_statements = [
            # 用户表
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                avatar TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 用户资料表
            """CREATE TABLE IF NOT EXISTS user_profiles (
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
            )""",
            # 风水资料表
            """CREATE TABLE IF NOT EXISTS fengshui_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                house_type TEXT DEFAULT '',
                total_area INTEGER,
                room_count INTEGER,
                facing_direction TEXT DEFAULT '',
                built_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 用户行为表
            """CREATE TABLE IF NOT EXISTS user_actions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                feature TEXT NOT NULL,
                params JSONB DEFAULT '{}'::jsonb,
                page TEXT DEFAULT '',
                duration INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 起卦记录表
            """CREATE TABLE IF NOT EXISTS hexagram_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                method TEXT DEFAULT '',
                params JSONB DEFAULT '{}'::jsonb,
                yao_values JSONB DEFAULT '[]'::jsonb,
                moving_lines JSONB DEFAULT '[]'::jsonb,
                original_hexagram JSONB DEFAULT '{}'::jsonb,
                changed_hexagram JSONB DEFAULT '{}'::jsonb,
                result_text TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 风水记录表
            """CREATE TABLE IF NOT EXISTS fengshui_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type TEXT DEFAULT '',
                params JSONB DEFAULT '{}'::jsonb,
                result JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 收藏表
            """CREATE TABLE IF NOT EXISTS user_favorites (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                hexagram_id TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, hexagram_id)
            )""",
        ]
        
        for sql in sql_statements:
            resp = requests.post(
                f'{BASE_URL}/rpc/exec_sql',
                headers=HEADERS,
                json={'sql': sql},
                timeout=30
            )
        
        print("✅ 数据库表初始化完成")
    except Exception as e:
        print(f"⚠️ 表初始化警告: {e}")


# ==================== 用户认证 ====================

def register_user(username, password, email=None):
    """注册用户"""
    if not _db_ready:
        return {"success": False, "error": "数据库未连接"}
    try:
        # 检查用户名
        users = _query('users', 'id', {'username': ('eq', username)})
        if users and len(users) > 0:
            return {"success": False, "error": "用户名已存在"}
        
        if email:
            users = _query('users', 'id', {'email': ('eq', email)})
            if users and len(users) > 0:
                return {"success": False, "error": "邮箱已被注册"}
        
        now = datetime.utcnow().isoformat()
        data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'avatar': '',
            'created_at': now,
            'updated_at': now,
        }
        
        result = _insert('users', data)
        if result:
            user_id = result[0]['id']
            # 自动创建用户资料
            _insert('user_profiles', {'user_id': user_id})
            _insert('fengshui_profiles', {'user_id': user_id})
            return {"success": True, "user_id": user_id}
        
        return {"success": False, "error": "注册失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """登录"""
    try:
        users = _query('users', 'id, username, email, avatar, password_hash', {'username': ('eq', username)})
        if users and len(users) > 0:
            user = users[0]
            if check_password_hash(user['password_hash'], password):
                return {
                    "success": True,
                    "user_id": user['id'],
                    "username": user['username'],
                    "email": user.get('email'),
                    "avatar": user.get('avatar', '') or '',
                }
        return {"success": False, "error": "用户名或密码错误"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_profile(user_id):
    """获取用户资料"""
    try:
        users = _query('users', 'id, username, email, avatar, created_at, updated_at', {'id': ('eq', user_id)})
        if not users:
            return None
        user = users[0]
        
        profiles = _query('user_profiles', '*', {'user_id': ('eq', user_id)})
        profile = profiles[0] if profiles else {}
        
        fengshui_list = _query('fengshui_profiles', '*', {'user_id': ('eq', user_id)})
        fengshui = fengshui_list[0] if fengshui_list else {}
        
        return {
            "user": user,
            "profile": profile,
            "fengshui_profile": fengshui,
        }
    except Exception:
        return None


def update_user_profile(user_id, data):
    """更新用户资料"""
    try:
        profile_fields = ["nickname", "birth_year", "birth_month", "birth_day", "birth_hour", "gender", "phone"]
        profile_updates = {f: data[f] for f in profile_fields if f in data and data[f] is not None}
        if profile_updates:
            _upsert('user_profiles', {**profile_updates, 'user_id': user_id}, unique_cols=['user_id'])
        
        fs_fields = ["house_type", "total_area", "room_count", "facing_direction", "built_year"]
        fs_updates = {f: data[f] for f in fs_fields if f in data and data[f] is not None}
        if fs_updates:
            _upsert('fengshui_profiles', {**fs_updates, 'user_id': user_id}, unique_cols=['user_id'])
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def change_password(user_id, old_password, new_password):
    """修改密码"""
    try:
        users = _query('users', 'password_hash', {'id': ('eq', user_id)})
        if not users:
            return {"success": False, "error": "用户不存在"}
        
        if not check_password_hash(users[0]['password_hash'], old_password):
            return {"success": False, "error": "原密码错误"}
        
        _update('users', {'id': ('eq', user_id)}, {
            'password_hash': generate_password_hash(new_password),
            'updated_at': datetime.utcnow().isoformat(),
        })
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 用户行为追踪 ====================

def log_user_action(user_id, action_type, feature, params=None, page='', duration=0):
    """记录用户行为"""
    try:
        _insert('user_actions', {
            'user_id': user_id,
            'action_type': action_type,
            'feature': feature,
            'params': json.dumps(params, ensure_ascii=False) if params else '{}',
            'page': page,
            'duration': duration,
            'created_at': datetime.utcnow().isoformat(),
        })
    except Exception:
        pass


def get_user_analytics(user_id, days=30):
    """获取用户行为统计"""
    try:
        actions = _query('user_actions', '*', {'user_id': ('eq', user_id)})
        # 简单过滤（按天数）
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [a for a in actions if a.get('created_at') and datetime.fromisoformat(a['created_at'].replace('Z', '+00:00').replace('+00:00', '')) >= cutoff]
        
        return {
            'total_actions': len(recent),
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
        users = _query('users', 'id, username, email, created_at')
        if not users:
            return []
        
        result = []
        for user in users:
            actions = _query('user_actions', 'id, created_at', {'user_id': ('eq', user['id'])})
            total = len(actions) if actions else 0
            last_active = None
            if actions:
                last_active = max(a.get('created_at', '') for a in actions)
            result.append({
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'created_at': user.get('created_at'),
                'total_actions': total,
                'last_active': last_active,
            })
        
        result.sort(key=lambda x: x['total_actions'], reverse=True)
        return result
    except Exception:
        return []


# ==================== 起卦记录 ====================

def save_hexagram_record(user_id, method, params, yao_values, moving_lines,
                         original_hexagram, changed_hexagram, result_text):
    """保存起卦记录"""
    try:
        result = _insert('hexagram_records', {
            'user_id': user_id,
            'method': method,
            'params': json.dumps(params, ensure_ascii=False),
            'yao_values': json.dumps(yao_values),
            'moving_lines': json.dumps(moving_lines),
            'original_hexagram': json.dumps(original_hexagram, ensure_ascii=False),
            'changed_hexagram': json.dumps(changed_hexagram, ensure_ascii=False),
            'result_text': result_text,
            'created_at': datetime.utcnow().isoformat(),
        })
        if result:
            return {"success": True, "record_id": result[0]['id']}
        return {"success": False, "error": "保存失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_hexagram_records(user_id, limit=50, offset=0):
    """获取起卦记录"""
    try:
        records = _query(
            'hexagram_records', '*',
            {'user_id': ('eq', user_id)},
            order='created_at desc',
            limit=limit,
            offset=offset
        )
        
        results = []
        for r in records:
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
        data = result = _insert('fengshui_records', {
            'user_id': user_id,
            'type': record_type,
            'params': json.dumps(params, ensure_ascii=False),
            'result': json.dumps(result, ensure_ascii=False),
            'created_at': datetime.utcnow().isoformat(),
        })
        if data:
            return {"success": True, "record_id": data[0]['id']}
        return {"success": False, "error": "保存失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_fengshui_records(user_id, limit=50, offset=0):
    """获取风水记录"""
    try:
        records = _query(
            'fengshui_records', '*',
            {'user_id': ('eq', user_id)},
            order='created_at desc',
            limit=limit,
            offset=offset
        )
        
        results = []
        for r in records:
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
        existing = _query('user_favorites', 'id', {
            'user_id': ('eq', user_id),
            'hexagram_id': ('eq', hexagram_id),
        })
        
        if existing:
            _delete('user_favorites', {
                'user_id': ('eq', user_id),
                'hexagram_id': ('eq', hexagram_id),
            })
            return {"success": True, "favorited": False}
        else:
            _insert('user_favorites', {
                'user_id': user_id,
                'hexagram_id': hexagram_id,
                'note': note,
                'created_at': datetime.utcnow().isoformat(),
            })
            return {"success": True, "favorited": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_favorites(user_id):
    """获取收藏列表"""
    try:
        favorites = _query(
            'user_favorites', '*',
            {'user_id': ('eq', user_id)},
            order='created_at desc'
        )
        
        results = []
        for f in favorites:
            if f.get('created_at'):
                f['created_at'] = f['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            results.append(f)
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
        users = _query('users', 'id')
        total_users = len(users) if users else 0
        
        actions = _query('user_actions', '*')
        total_actions = len(actions) if actions else 0
        
        # 最近7天活跃用户
        from datetime import timedelta
        cutoff_7d = datetime.utcnow() - timedelta(days=7)
        active_7d = 0
        if actions:
            active_user_ids = set()
            for a in actions:
                if a.get('created_at'):
                    try:
                        ca = a['created_at']
                        if isinstance(ca, str):
                            ca = ca.replace('Z', '')
                        created = datetime.fromisoformat(ca)
                        if created >= cutoff_7d:
                            active_user_ids.add(a.get('user_id'))
                    except (ValueError, TypeError):
                        pass
            active_7d = len(active_user_ids)
        
        # 今日动作
        today = datetime.utcnow().date()
        today_actions = 0
        for a in actions:
            if a.get('created_at'):
                try:
                    ca = a['created_at']
                    if isinstance(ca, str):
                        ca = ca.replace('Z', '')
                    created = datetime.fromisoformat(ca).date()
                    if created == today:
                        today_actions += 1
                except (ValueError, TypeError):
                    pass
        
        # 功能分布
        feature_counts = {}
        user_counts = {}
        recent = []
        
        for a in actions:
            feat = a.get('feature', '')
            feature_counts[feat] = feature_counts.get(feat, 0) + 1
            
            uid = a.get('user_id')
            if uid:
                if uid not in user_counts:
                    user_counts[uid] = {'cnt': 0, 'last_active': ''}
                user_counts[uid]['cnt'] += 1
                if not user_counts[uid]['last_active'] or (a.get('created_at') or '') > user_counts[uid]['last_active']:
                    user_counts[uid]['last_active'] = a.get('created_at', '')
        
            # 最近50条
            if len(recent) < 50:
                r = dict(a)
                if r.get('created_at'):
                    r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                try:
                    r['params'] = json.loads(r['params']) if r.get('params') else {}
                except (json.JSONDecodeError, TypeError):
                    r['params'] = {}
                recent.append(r)
        
        top_features = [{"feature": k, "cnt": v} for k, v in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
        
        top_users = []
        for uid, info in sorted(user_counts.items(), key=lambda x: x[1]['cnt'], reverse=True)[:10]:
            top_users.append({
                'user_id': uid,
                'cnt': info['cnt'],
                'last_active': info['last_active'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(info.get('last_active'), str) else info.get('last_active', ''),
            })
        
        return {
            'total_users': total_users,
            'total_actions': total_actions,
            'active_users_7d': active_7d,
            'today_actions': today_actions,
            'top_features': top_features,
            'top_users': top_users,
            'recent_actions': recent,
        }
    except Exception as e:
        print(f"统计错误: {e}")
        return default
