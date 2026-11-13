# -*- coding: utf-8 -*-
"""Flask web server for 周易八卦系统"""

import sys
import json
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session

sys.path.insert(0, str(Path(__file__).parent))

from core import (
    TRIGRAMS, HEXAGRAMS, NAJIA, HEXAGRAM_LINES,
    toss_coins, toss_single_coin, yarrow_stalk, yarrow_single, time_divination,
    find_hexagram, search_hexagrams, get_changed_hexagram, binary_to_trigrams,
    xing_relationship, xing_strength, get_xing_relationship_detail,
    ba_zhai_directions, lookup_trigram_by_dir,
    get_mingben_wuxing, calc_benming_wuxing_strength,
    SHENG_XIAO_NAMES, SHENG_XIAO_WU_XING,
    TIAN_GAN, DI_ZHI, TIAN_GAN_WU_XING,
    DI_ZHI_WU_XING, calc_lua_qin, _lua_qin_from, SHI_SHEN_DESC,
    BA_ZHAI_XING_INFO, JIU_XING_MAPPING, JIU_XING_WU_XING,
    JIU_XING_XING_FEI_NIAN, JIU_XING_HUO_FU_JUE, JIU_XING_FENFANG,
    calc_xing_gong_sheng_ke, calc_men_zhu_zao, calc_men_zhu_zao_liu_yao,
    calc_comprehensive_analysis, calc_bazhai_comprehensive, calc_room_fengshui,
    KE_TING_FENGSHUI, SHU_FANG_FENGSHUI, ZUO_SHAN_GUA_SHUO_MING, JIU_XING_SU_CHA,
    BA_GUA_XIANG, LIU_HE_DETAIL, SAN_HE_DETAIL, LIU_CHONG, SAN_XING, LIU_HAI,
    ER_SHIBA_XIU, JIAN_CHU_SHEN, JIAN_CHU_ZHI, calc_jian_chu,
    NAYIN_NAMES, NAYIN_LIST,
    calc_que_jiang, check_house_shape,
    QUE_JIANG_INFO, QUE_JIANG_HUA_JIE,
    TU_JIANG_INFO, TU_JIANG_HUA_JIE,
    CHUYIN_FENGSHUI, CESSHI_FENGSHUI, HUO_SHAO_TIAN_MEN,
    YANG_ZHAI_SHI_SHU_DUAN_YU, BA_GUA_LEI_XIANG,
    WU_XING_XI_JIE, BU_JIANG_BAI_JIAN,
    SHI_CHEN_NAMES,
)

# 导入完整卦象数据（含大象传、学术注释）
from hexagram_data import HEXAGRAM_DATA

# 导入命卦数据（倪海厦解读）
from mingua_data import MINGUA_DATA

# 导入数据库模块
import models as db

# Flask session 密钥（生产环境建议用环境变量）
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'yijing-web-dev-key-change-in-prod')

# 管理后台密码（可通过环境变量 ADMIN_PASSWORD 设置）
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def get_current_user():
    """从 session 获取当前用户"""
    if 'user_id' not in session:
        return None
    return db.get_user_profile(session['user_id'])


def require_auth(f):
    """登录验证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        return f(*args, **kwargs)
    return decorated


# ========== 首页数据 ==========
@app.route('/')
def index():
    return render_template('index.html')


# ========== 管理后台 ==========
def admin_required(f):
    """管理后台登录验证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return jsonify({"success": False, "error": "未登录"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/api/debug/db', methods=['GET'])
def api_debug_db():
    """调试：检查数据库连接状态"""
    return {
        'db_ready': db._db_ready,
        'project_ref': db.PROJECT_REF,
        'api_url': db.BASE_URL,
    }


@app.route('/admin')
def admin_page():
    """管理后台页面"""
    return render_template('admin.html')


@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """管理后台登录"""
    data = request.json or {}
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '密码错误'}), 401


@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    """管理后台登出"""
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})


@app.route('/api/admin/session', methods=['GET', 'POST'])
def api_admin_session():
    """管理后台登录状态"""
    return jsonify({'success': True, 'logged_in': 'admin_logged_in' in session})


@app.route('/api/admin/overview', methods=['GET'])
@admin_required
def api_admin_overview():
    """管理后台总览数据"""
    from datetime import datetime, timedelta
    
    # 总用户数
    users = db._query('users')
    total_users = len(users) if users else 0
    
    # 总行为数
    actions = db._query('user_actions')
    total_actions = len(actions) if actions else 0
    
    # 近 7 天数据
    cutoff_7d = datetime.utcnow() - timedelta(days=7)
    today = datetime.utcnow().date()
    
    daily_activity = {}
    top_features = {}
    active_user_map = {}
    
    for a in (actions or []):
        feat = a.get('feature', '')
        top_features[feat] = top_features.get(feat, 0) + 1
        
        uid = a.get('user_id')
        if uid:
            if uid not in active_user_map:
                active_user_map[uid] = {'cnt': 0, 'last_active': ''}
            active_user_map[uid]['cnt'] += 1
            ca = a.get('created_at', '') or ''
            if isinstance(ca, str):
                ca = ca.replace('Z', '')
            if active_user_map[uid]['last_active'] < ca:
                active_user_map[uid]['last_active'] = ca
        
        if a.get('created_at'):
            try:
                ca = a['created_at']
                if isinstance(ca, str):
                    ca = ca.replace('Z', '')
                created = datetime.fromisoformat(ca)
                if created >= cutoff_7d:
                    day_key = created.strftime('%Y-%m-%d')
                    daily_activity[day_key] = daily_activity.get(day_key, 0) + 1
            except (ValueError, TypeError):
                pass
    
    today_actions = 0
    for a in (actions or []):
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
    
    active_users = []
    for uid, info in sorted(active_user_map.items(), key=lambda x: x[1]['cnt'], reverse=True)[:10]:
        if info['cnt'] > 0:
            user_data = db._query('users', 'id,username', {'id': ('eq', uid)})
            username = user_data[0]['username'] if user_data else 'unknown'
            try:
                la = datetime.fromisoformat(info['last_active'].replace('Z', ''))
                la_str = la.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                la_str = ''
            active_users.append({'id': uid, 'username': username, 'actions': info['cnt'], 'last_active': la_str})
    
    top_features_list = [{'feature': k, 'cnt': v} for k, v in sorted(top_features.items(), key=lambda x: x[1], reverse=True)[:10]]
    daily_list = [{'day': k, 'cnt': v} for k, v in sorted(daily_activity.items())]
    
    return jsonify({
        'success': True,
        'data': {
            'total_users': total_users,
            'total_actions': total_actions,
            'daily_activity': daily_list,
            'top_features': top_features_list,
            'active_users': active_users,
            'today_actions': today_actions,
        }
    })


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_admin_users():
    """管理后台用户列表"""
    days = request.args.get('days', 30, type=int)
    users = db.get_all_users_summary(days)
    return jsonify({'success': True, 'data': users})


@app.route('/api/admin/recent_actions', methods=['GET'])
@admin_required
def api_admin_recent_actions():
    """管理后台全站最近行为记录"""
    from datetime import datetime
    limit = request.args.get('limit', 50, type=int)
    try:
        actions = db._query('user_actions', '*', order='created_at.desc', limit=limit)
        
        results = []
        for a in actions:
            uid = a.get('user_id')
            username = 'unknown'
            if uid:
                user_data = db._query('users', 'username', {'id': ('eq', uid)})
                if user_data:
                    username = user_data[0].get('username', 'unknown')
            
            r = dict(a)
            r['username'] = username
            if r.get('created_at'):
                try:
                    ca = r['created_at']
                    if isinstance(ca, str):
                        ca = ca.replace('Z', '')
                    created = datetime.fromisoformat(ca)
                    r['created_at'] = created.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
            results.append(r)
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/admin/user/<int:user_id>', methods=['GET'])
@admin_required
def api_admin_user_detail(user_id):
    """管理后台用户详情"""
    user_data = db._query('users', 'id,username,email,avatar,created_at,updated_at', {'id': ('eq', user_id)})
    if not user_data:
        return jsonify({'success': False, 'error': '用户不存在'})
    user = user_data[0]
    
    # 用户行为记录（最近 100 条）
    actions = db._query('user_actions', '*', {'user_id': ('eq', user_id)}, order='created_at.desc', limit=100)
    user['actions'] = []
    for a in actions:
        r = dict(a)
        if r.get('created_at'):
            r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        user['actions'].append(r)
    
    # 用户统计
    stats = db.get_user_analytics(user_id, 30)
    user['stats'] = stats
    return jsonify({'success': True, 'data': user})


# ========== 铜钱起卦 ==========
@app.route('/api/coin/toss', methods=['POST'])
@require_auth
def api_coin_toss():
    """抛单次铜钱，返回单爻结果"""
    result = toss_single_coin()
    return jsonify({'success': True, 'data': result})


# ========== 蓍草起卦 ==========
@app.route('/api/yarrow/calculate', methods=['POST'])
@require_auth
def api_yarrow():
    """单次蓍草演算"""
    result = yarrow_single()
    return jsonify({'success': True, 'data': result})


# ========== 时间起卦 ==========
@app.route('/api/time/divination', methods=['POST'])
@require_auth
def api_time_divination():
    """时间起卦，返回完整卦象数据（含爻辞、大象传、变卦）"""
    data = request.json or {}
    year = data.get('year', 2025)
    month = data.get('month', 1)
    day = data.get('day', 1)
    clock_hour = data.get('hour', 0)  # 选择框实际时间值：0,1,3,5,7,9,11,13,15,17,19,21
    # 转为地支序数：子时=1, 丑时=2, ..., 亥时=12
    hour_dizhi_num = (clock_hour + 1) // 2 + 1
    upper_name, lower_name = time_divination(year, month, day, hour_dizhi_num)
    total = year + month + day + hour_dizhi_num
    moving_yao = (total % 6) if total % 6 > 0 else 6

    # 查找完整卦象数据
    hex_result = find_hexagram(upper_name, lower_name)
    hex_name = hex_result['name'] if hex_result else f'{upper_name}{lower_name}'

    # 从 HEXAGRAM_DATA 获取大象传等完整信息
    hx_data = HEXAGRAM_DATA.get(hex_name, {})
    xiang_comment = hx_data.get('xiang_comment', '')
    line_types = hx_data.get('line_type', [])
    line_notes = hx_data.get('line_note', [])

    # 获取动爻的爻辞
    yao_names = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
    yao_text = ''
    yao_name = ''
    yao_note = ''
    lines_data = HEXAGRAM_LINES.get(hex_name, [])
    if moving_yao <= len(lines_data):
        yao_text = lines_data[moving_yao - 1]
    if moving_yao <= len(yao_names):
        yao_name = yao_names[moving_yao - 1]
    if moving_yao <= len(line_types):
        yao_name = line_types[moving_yao - 1]
    if moving_yao <= len(line_notes):
        yao_note = line_notes[moving_yao - 1]

    # 计算变卦
    changed_name = ''
    changed_upper = ''
    changed_lower = ''
    changed_hex = None
    if moving_yao:
        # 根据动爻计算变卦：阳变阴，阴变阳
        changed_binary = 0
        for i in range(6):
            if i == moving_yao - 1:
                # 动爻：阴阳互换
                changed_binary |= (1 - (1 << i) & 1) << i
            else:
                # 非动爻保持不变
                if i < len(lines_data) and lines_data[i]:
                    changed_binary |= (1 << i)
        # 更简单的计算：获取当前爻值
        yao_values = [0] * 6
        for i in range(6):
            if i < len(lines_data) and lines_data[i]:
                yao_values[i] = 1  # 阳
            else:
                yao_values[i] = 0  # 阴
        # 动爻翻转
        yao_values[moving_yao - 1] = 1 - yao_values[moving_yao - 1]
        changed_binary = sum(v << i for i, v in enumerate(yao_values))
        cu, cl = binary_to_trigrams(changed_binary)
        changed_hex = find_hexagram(cu, cl)
        if changed_hex:
            changed_name = changed_hex['name']
            changed_upper = changed_hex['upper']
            changed_lower = changed_hex['lower']

    result = {
        'upper': upper_name,
        'lower': lower_name,
        'moving_yao': moving_yao,
        'name': hex_name,
        'judgment': hex_result.get('judgment', '') if hex_result else '',
        'upper_trigram': hex_result.get('upper', '') if hex_result else upper_name,
        'lower_trigram': hex_result.get('lower', '') if hex_result else lower_name,
        'xiang_comment': xiang_comment,
        'yao_name': yao_name,
        'yao_text': yao_text,
        'yao_note': yao_note,
        'changed_name': changed_name,
        'changed_upper': changed_upper,
        'changed_lower': changed_lower,
    }
    return jsonify({'success': True, 'data': result})


# ========== 命卦查询 ==========
@app.route('/api/mingua/lookup', methods=['POST'])
@require_auth
def api_mingua_lookup():
    """查询六十四卦命卦数据（倪海厦解读）"""
    data = request.json or {}
    hex_name = data.get('hexagram', '')
    
    # 如果直接匹配成功，返回结果
    result = MINGUA_DATA.get(hex_name, {})
    if result:
        return jsonify({
            'success': True,
            'data': {
                'hexagram': hex_name,
                'xiantian': result.get('xiantian', ''),
                'houtian': result.get('houtian', ''),
                'liunian': result.get('liunian', ''),
            }
        })
    
    # 尝试将"上卦 + 下卦"格式映射到完整卦名
    # 例如：乾兑 -> 天泽履
    matched_name = None
    for hx in HEXAGRAMS:
        if len(hx) >= 4 and hx[1] + hx[2] == hex_name:
            matched_name = hx[0]
            break
    
    if matched_name:
        result = MINGUA_DATA.get(matched_name, {})
        return jsonify({
            'success': True,
            'data': {
                'hexagram': hex_name,
                'matched_name': matched_name,
                'xiantian': result.get('xiantian', ''),
                'houtian': result.get('houtian', ''),
                'liunian': result.get('liunian', ''),
            }
        })
    
    return jsonify({
        'success': True,
        'data': {
            'hexagram': hex_name,
            'xiantian': '',
            'houtian': '',
            'liunian': '',
        }
    })


# ========== 六十四卦查询 ==========
@app.route('/api/hexagram/search', methods=['POST'])
@require_auth
def api_hexagram_search():
    """搜索六十四卦，返回完整数据（卦辞、爻辞、十翼）"""
    data = request.json or {}
    keyword = data.get('keyword', '').strip()
    result = search_hexagrams(keyword)
    # HEXAGRAM_LINES[name] 是爻辞列表（每爻一条字符串）
    if isinstance(result, dict) and result.get('name'):
        name = result.get('name')
        lines_data = HEXAGRAM_LINES.get(name, [])
        # 给每条爻辞添加爻位名称
        yao_names = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
        result['lines'] = []
        if isinstance(lines_data, list):
            for i, line_text in enumerate(lines_data):
                result['lines'].append({
                    'yao_name': yao_names[i] if i < len(yao_names) else '',
                    'text': line_text,
                })
        result['shi_yi'] = {}
    elif isinstance(result, list):
        for hex_item in result:
            name = hex_item.get('name', '')
            lines_data = HEXAGRAM_LINES.get(name, [])
            yao_names = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
            hex_item['lines'] = []
            if isinstance(lines_data, list):
                for i, line_text in enumerate(lines_data):
                    hex_item['lines'].append({
                        'yao_name': yao_names[i] if i < len(yao_names) else '',
                        'text': line_text,
                    })
            hex_item['shi_yi'] = {}
    return jsonify({'success': True, 'data': result})


# ========== 变卦 ==========
@app.route('/api/hexagram/changed', methods=['POST'])
@require_auth
def api_hexagram_changed():
    """获取变卦"""
    data = request.json or {}
    hex_name = data.get('hexagram', '')
    moving_lines = data.get('moving_lines', [])
    result = get_changed_hexagram(hex_name, moving_lines)
    return jsonify({'success': True, 'data': result})


# ========== 五行生克 ==========
@app.route('/api/wuxing/relationship', methods=['POST'])
@require_auth
def api_wuxing_relationship():
    """五行生克关系，包含十神详解"""
    data = request.json or {}
    w1 = data.get('wuxing1', '')
    w2 = data.get('wuxing2', '')
    result = xing_relationship(w1, w2)
    detail = get_xing_relationship_detail(w1, w2)
    strength = xing_strength(w1, 'spring')

    # 计算六亲关系
    e1_wx = w1
    e2_wx = w2
    lq = _lua_qin_from(wuxing_me=e1_wx, wuxing_ta=e2_wx)

    return jsonify({
        'success': True,
        'data': {
            'relationship': result,
            'detail': detail,
            'strength': strength,
            'liu_qin': lq,
            'wuxing1': e1_wx,
            'wuxing2': e2_wx,
            'shi_shen': SHI_SHEN_DESC.get(lq, {}),
        }
    })


# ========== 本命五行 ==========
@app.route('/api/benming/calculate', methods=['POST'])
@require_auth
def api_benming():
    """本命五行测算，返回完整四柱八字和详细分析"""
    data = request.json or {}
    year = data.get('year', 1990)
    month = data.get('month', 0)
    day = data.get('day', 0)
    hour_index = data.get('hour_index', 0)

    # 时辰对应的小时（子时=0或24，丑时=1，等等）
    shi_chen_hours = [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
    hour = shi_chen_hours[hour_index] if 0 <= hour_index < 12 else 12

    strength_result = calc_benming_wuxing_strength(year, month, day, hour)
    mingben = get_mingben_wuxing(year, month, day, hour)

    return jsonify({
        'success': True,
        'data': {
            'strength': strength_result,
            'mingben': mingben,
            'year_pillar': f"{year}年",
        }
    })


# ========== 八宅风水方位 ==========
@app.route('/api/fengshui/directions', methods=['POST'])
@require_auth
def api_fengshui_directions():
    """八宅风水方位，包含九星祸福诀、星宫生克、化解建议"""
    data = request.json or {}
    gua = data.get('gua', '乾')
    directions = ba_zhai_directions(gua)
    trigram_info = lookup_trigram_by_dir(gua)

    # 构建详细的方位数据
    detailed_directions = {}
    ji_xiong_map = {
        "生气": ("吉", "#81c784"), "天医": ("吉", "#81c784"),
        "延年": ("吉", "#81c784"), "伏位": ("平", "#d4a843"),
        "六煞": ("凶", "#e57373"), "五鬼": ("凶", "#e57373"),
        "绝命": ("凶", "#e57373"), "祸害": ("凶", "#e57373"),
    }

    for direction in ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]:
        star = directions.get(direction, "未知")
        jx, color = ji_xiong_map.get(star, ("未知", "#6b7b8d"))
        info = BA_ZHAI_XING_INFO.get(star, {})
        nine_star = info.get("九星名", "")
        star_wx = info.get("五行", "")
        palace_gua = lookup_trigram_by_dir(direction)
        xg = calc_xing_gong_sheng_ke(star, palace_gua)

        detailed_directions[direction] = {
            'star': star,
            'ji_xiong': jx,
            'color': color,
            'nine_star': nine_star,
            'star_wuxing': star_wx,
            'palace_gua': palace_gua,
            'xing_gong_sheng_ke': xg,
            'info': info,
        }

    # 九星祸福诀
    jiu_xing_huo_fu_jue = {}
    for star_name in ["生气", "天医", "延年", "伏位", "六煞", "五鬼", "绝命", "祸害"]:
        hfj = JIU_XING_HUO_FU_JUE.get(star_name, {})
        if hfj:
            jiu_xing_huo_fu_jue[star_name] = hfj

    # 吉凶分组化解建议
    ji_stars, xiong_stars, ping_stars = [], [], []
    for direction in ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]:
        star = directions.get(direction, "未知")
        info = BA_ZHAI_XING_INFO.get(star, {})
        jx = info.get("吉凶", "平")
        entry = {
            'direction': direction,
            'star': star,
            'nine_star': info.get("九星名", ""),
            'info': info,
        }
        if jx == "吉":
            ji_stars.append(entry)
        elif jx in ("凶", "大凶"):
            xiong_stars.append(entry)
        else:
            ping_stars.append(entry)

    return jsonify({
        'success': True,
        'data': {
            'directions': directions,
            'directions_detail': detailed_directions,
            'trigram_info': trigram_info,
            'jiu_xing_huo_fu_jue': jiu_xing_huo_fu_jue,
            'ji_stars': ji_stars,
            'xiong_stars': xiong_stars,
            'ping_stars': ping_stars,
            'ming_type': "东四命" if gua in ("坎", "离", "震", "巽") else "西四命",
        }
    })


# ========== 阳宅六要·门主灶分析 ==========
@app.route('/api/fengshui/mz_analysis', methods=['POST'])
@require_auth
def api_fengshui_mz_analysis():
    """阳宅六要综合风水测算"""
    data = request.json or {}
    door_dir = data.get('door_dir', '')
    main_dir = data.get('main_dir', '')
    kitchen_dir = data.get('kitchen_dir', '')
    living_dir = data.get('living_dir', '')
    study_dir = data.get('study_dir', '')
    toilet_dir = data.get('toilet_dir', '')
    gua = data.get('gua', '')

    result = calc_comprehensive_analysis(
        door_dir, main_dir, kitchen_dir,
        living_dir, study_dir, toilet_dir, gua
    )

    # 门主灶六爻
    mz_liuyao = calc_men_zhu_zao_liu_yao(
        door_dir, main_dir, kitchen_dir,
        living_dir, study_dir, toilet_dir, gua
    )

    mzz = calc_men_zhu_zao(door_dir, main_dir, kitchen_dir)

    return jsonify({
        'success': True,
        'data': {
            'comprehensive': result,
            'men_zhu_zao_liuyao': mz_liuyao,
            'men_zhu_zao': mzz,
        }
    })


# ========== 缺角凸角分析 ==========
@app.route('/api/fengshui/que_jiang', methods=['POST'])
@require_auth
def api_que_jiang():
    """缺角/凸角分析"""
    data = request.json or {}
    area = data.get('area', '西北')
    is_que = data.get('is_que_jiang', True)
    result = calc_que_jiang(area, is_que)
    return jsonify({'success': True, 'data': result})


# ========== 综合风水分析（八宅+九宫+缺角+命理） ==========
@app.route('/api/fengshui/comprehensive_bazhai', methods=['POST'])
@require_auth
def api_fengshui_comprehensive_bazhai():
    """综合风水分析（八宅+九宫+缺角+命理）"""
    data = request.json or {}
    result = calc_bazhai_comprehensive(
        house_gua=data.get('house_gua', ''),
        door_dir=data.get('door_dir', ''),
        main_dir=data.get('main_dir', ''),
        kitchen_dir=data.get('kitchen_dir', ''),
        living_dir=data.get('living_dir', ''),
        study_dir=data.get('study_dir', ''),
        toilet_dir=data.get('toilet_dir', ''),
        resident_shengxiao=data.get('resident_shengxiao', ''),
        resident_year=data.get('resident_year', 0),
        house_shape=data.get('house_shape', ''),
    )
    return jsonify({'success': True, 'data': result})


# ========== 房间风水 ==========
@app.route('/api/fengshui/room', methods=['POST'])
@require_auth
def api_fengshui_room():
    """房间风水测算"""
    data = request.json or {}
    room_type = data.get('room_type', '客厅')
    room_dir = data.get('room_dir', '')
    gua = data.get('gua', '')
    result = calc_room_fengshui(room_type, room_dir, gua)
    return jsonify({'success': True, 'data': result})


# ========== 八卦详解 ==========
@app.route('/api/bagua/detail', methods=['POST'])
@require_auth
def api_bagua_detail():
    """八卦详解"""
    data = request.json or {}
    gua = data.get('gua', '乾')
    info = BA_GUA_XIANG.get(gua, {})
    lei_xiang = BA_GUA_LEI_XIANG.get(gua, {})
    return jsonify({
        'success': True,
        'data': {
            'xiang': info,
            'lei_xiang': lei_xiang,
        }
    })


# ========== 二十八星宿 ==========
# 二十八宿五行到四象的映射
WU_XING_TO_SI_XIANG = {
    '金': '青龙',
    '木': '青龙',
    '水': '玄武',
    '火': '朱雀',
    '土': '白虎',
}

# 九星名称 → 二十八宿名映射（来自传统二十八宿九曜体系）
JIUX_TO_XINGZUO = {
    '贪狼': ['角', '奎', '柳'],
    '巨门': ['亢', '娄', '星'],
    '武曲': ['氐', '胃', '张'],
    '文曲': ['房', '昴', '翼'],
    '廉贞': ['心', '毕', '轸'],
    '禄存': ['尾', '觜'],
    '破军': ['箕', '斗'],
    '左辅': ['井'],
    '右弼': ['女', '鬼'],
}


@app.route('/api/28xiu/calculate', methods=['POST'])
@require_auth
def api_28_xiu():
    """二十八星宿查询"""
    data = request.json or {}
    xiang_filter = data.get('xiang_filter', '')
    jiux_filter = data.get('jiux_filter', '')
    jiachushen_filter = data.get('jiachushen_filter', '')
    jiachuzhi_filter = data.get('jiachuzhi_filter', '')
    results = []

    # 五行筛选映射：金/木→青龙, 水→玄武, 火→朱雀, 土→白虎
    si_xiang_target = None
    if xiang_filter and xiang_filter in WU_XING_TO_SI_XIANG:
        si_xiang_target = WU_XING_TO_SI_XIANG[xiang_filter]

    # 九星筛选：通过九星→星宿映射
    xingzuo_list = None
    if jiux_filter and jiux_filter in JIUX_TO_XINGZUO:
        xingzuo_list = JIUX_TO_XINGZUO[jiux_filter]

    for xing_name, xi in ER_SHIBA_XIU.items():
        # 四象筛选
        if si_xiang_target and xi.get('象', '') != si_xiang_target:
            continue
        # 九星筛选
        if xingzuo_list and xing_name not in xingzuo_list:
            continue
        # 建除十二神筛选（占断中包含）
        if jiachushen_filter and jiachushen_filter not in xi.get('占断', ''):
            continue
        # 建除十二支筛选
        if jiachuzhi_filter:
            found = False
            for zhi in ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']:
                if zhi in xi.get('占断', '') and jiachuzhi_filter in xi.get('占断', ''):
                    found = True
                    break
            if not found and jiachuzhi_filter:
                continue
        results.append({
            'name': xing_name,
            'xiang': xi.get('象', ''),
            'jiux': xi.get('星神', ''),
            'jixiong': xi.get('吉凶', ''),
            'desc': xi.get('含义', ''),
            'good': xi.get('占断', ''),
            '宿属': xi.get('宿属', ''),
        })

    return jsonify({'success': True, 'data': results})


# ========== 纳甲 ==========
@app.route('/api/najia/list', methods=['POST'])
@require_auth
def api_najia():
    """纳甲数据，包含六亲计算"""
    # 构建完整的纳甲数据，包含六亲
    najia_with_liu_qin = {}
    for gua_name, gua_data in NAJIA.items():
        na_jia = gua_data.get("纳甲", "")
        na_zhi = gua_data.get("纳支", [])
        yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]

        yao_details = []
        for yao, zhi in zip(yao_names, na_zhi):
            zhi_wx = DI_ZHI_WU_XING.get(zhi, "")
            lq = calc_lua_qin(gua_name, zhi)
            yao_details.append({
                'yao': yao,
                'zhi': zhi,
                'zhi_wuxing': zhi_wx,
                'liu_qin': lq,
            })

        najia_with_liu_qin[gua_name] = {
            'na_jia': na_jia,
            'yao_details': yao_details,
            'trigram_info': TRIGRAMS.get(gua_name, {}),
        }

    return jsonify({
        'success': True,
        'data': {
            'najia': najia_with_liu_qin,
            'nayin_list': NAYIN_LIST,
        }
    })


# ========== 纳音查询 ==========
@app.route('/api/nayin/search', methods=['POST'])
@require_auth
def api_nayin_search():
    """纳音五行查询"""
    data = request.json or {}
    ganzhi = data.get('ganzhi', '')
    for item in NAYIN_LIST:
        if item[0] == ganzhi or item[1] == ganzhi:
            return jsonify({'success': True, 'data': {
                'ganzhi': ganzhi,
                'nayin': item[2],
                'wuxing': item[3],
            }})
    return jsonify({'success': False, 'data': {'message': '未找到纳音五行'}})


# ========== 五行分布 ==========
@app.route('/api/wuxing/distribution', methods=['POST'])
@require_auth
def api_wuxing_distribution():
    """五行分布"""
    return jsonify({
        'success': True,
        'data': {
            'wuxing_xiang': WU_XING_XI_JIE,
        }
    })


# ========== 八卦方位 ==========
@app.route('/api/trigram/direction', methods=['POST'])
@require_auth
def api_trigram_direction():
    """八卦方位查询"""
    data = request.json or {}
    direction = data.get('direction', '')
    info = lookup_trigram_by_dir(direction)
    return jsonify({'success': True, 'data': info})


# ========== 生肖五行 ==========
@app.route('/api/shengxiao/wuxing', methods=['POST'])
@require_auth
def api_shengxiao_wuxing():
    """生肖五行"""
    data = request.json or {}
    shengxiao = data.get('shengxiao', '')
    wx = SHENG_XIAO_WU_XING.get(shengxiao, '')
    name = SHENG_XIAO_NAMES.get(shengxiao, '')
    return jsonify({
        'success': True,
        'data': {
            'shengxiao': shengxiao,
            'name': name,
            'wuxing': wx,
        }
    })


# ========== 六冲/三合/六合等 ==========
@app.route('/api/wuxing/details', methods=['POST'])
@require_auth
def api_wuxing_details():
    """六合/三合/六冲/三刑/六害"""
    data = request.json or {}
    detail_type = data.get('type', 'liu_chong')
    details = {
        'liu_he': LIU_HE_DETAIL,
        'san_he': SAN_HE_DETAIL,
        'liu_chong': LIU_CHONG,
        'san_xing': SAN_XING,
        'liu_hai': LIU_HAI,
    }
    raw = details.get(detail_type, {})
    # 将字典转为数组格式，供前端表格渲染
    result = []
    for key, val in raw.items():
        if isinstance(val, dict):
            row = {'关系': key}
            row.update(val)
            result.append(row)
        else:
            result.append({'项': key, '值': str(val)})
    return jsonify({
        'success': True,
        'data': result
    })


# ========== 建除神 ==========
@app.route('/api/jian_chu/calculate', methods=['POST'])
@require_auth
def api_jian_chu():
    """建除十二神"""
    data = request.json or {}
    ganshi = data.get('ganshi', '')
    result = calc_jian_chu(ganshi)
    return jsonify({'success': True, 'data': result})


# ========== 厨房/厕所方位 ==========
@app.route('/api/fengshui/chu_ce', methods=['POST'])
@require_auth
def api_fengshui_chu_ce():
    """厨房/厕所方位吉凶"""
    data = request.json or {}
    room_type = data.get('type', 'chu')  # chu or ce
    direction = data.get('direction', '')
    if room_type == 'chu':
        result = CHUYIN_FENGSHUI.get(direction, {})
    else:
        result = CESSHI_FENGSHUI.get(direction, {})
    return jsonify({'success': True, 'data': result})


# ========== 火烧天门 ==========
@app.route('/api/fengshui/huo_shao_tian_men', methods=['POST'])
@require_auth
def api_huo_shao_tian_men():
    """火烧天门"""
    return jsonify({'success': True, 'data': HUO_SHAO_TIAN_MEN})


# ========== 坐山卦说明 ==========
@app.route('/api/fengshui/sitting_trigram', methods=['POST'])
@require_auth
def api_sitting_trigram():
    """坐山卦通俗说明"""
    return jsonify({
        'success': True,
        'data': ZUO_SHAN_GUA_SHUO_MING,
    })


# ========== 九星速查 ==========
@app.route('/api/jiuxing/search', methods=['POST'])
@require_auth
def api_jiuxing_search():
    """九星速查"""
    data = request.json or {}
    jiuxing = data.get('jiuxing', '')
    result = {}
    if jiuxing:
        result = JIU_XING_SU_CHA.get(jiuxing, {})
    else:
        result = JIU_XING_SU_CHA
    return jsonify({'success': True, 'data': result})


# ========== 用户认证 ==========

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    """注册"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip() or None

    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'})

    result = db.register_user(username, password, email)
    if result['success']:
        # 自动登录
        session['user_id'] = result['user_id']
    return jsonify(result)


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    """登录"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    result = db.login_user(username, password)
    if result['success']:
        session['user_id'] = result['user_id']
    return jsonify(result)


@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    """登出"""
    session.pop('user_id', None)
    return jsonify({'success': True})


@app.route('/api/auth/session', methods=['GET', 'POST'])
def api_auth_session():
    """获取当前登录状态"""
    if 'user_id' not in session:
        return jsonify({'success': True, 'logged_in': False})

    profile = db.get_user_profile(session['user_id'])
    if not profile:
        session.pop('user_id', None)
        return jsonify({'success': True, 'logged_in': False})

    return jsonify({
        'success': True,
        'logged_in': True,
        'user': profile,
    })


# ========== 用户资料 ==========

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def api_get_profile():
    """获取用户资料"""
    profile = get_current_user()
    return jsonify({'success': True, 'data': profile})


@app.route('/api/user/profile', methods=['POST'])
@require_auth
def api_update_profile():
    """更新用户资料"""
    data = request.json or {}
    result = db.update_user_profile(session['user_id'], data)
    return jsonify(result)


@app.route('/api/user/change_password', methods=['POST'])
@require_auth
def api_change_password():
    """修改密码"""
    data = request.json or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not old_pw or not new_pw:
        return jsonify({'success': False, 'error': '请填写原密码和新密码'})
    if len(new_pw) < 4:
        return jsonify({'success': False, 'error': '新密码至少4个字符'})
    result = db.change_password(session['user_id'], old_pw, new_pw)
    return jsonify(result)


@app.route('/api/user/action', methods=['POST'])
@require_auth
def api_log_action():
    """记录用户行为（可批量）"""
    data = request.json or {}
    actions = data.get('actions', [data])  # 支持单条或批量
    for action in actions:
        db.log_user_action(
            session['user_id'],
            action.get('action_type', 'other'),
            action.get('feature', ''),
            action.get('params'),
            action.get('page', ''),
            action.get('duration', 0),
        )
    return jsonify({'success': True})


@app.route('/api/user/analytics', methods=['GET'])
@require_auth
def api_get_analytics():
    """获取用户行为统计"""
    days = request.args.get('days', 30, type=int)
    result = db.get_user_analytics(session['user_id'], days)
    return jsonify({'success': True, 'data': result})


# ========== 起卦记录 ==========

@app.route('/api/hexagram/record', methods=['POST'])
@require_auth
def api_save_hexagram_record():
    """保存起卦记录"""
    data = request.json or {}
    result = db.save_hexagram_record(
        session['user_id'],
        method=data.get('method', 'coin'),
        params=data.get('params', {}),
        yao_values=data.get('yao_values', []),
        moving_lines=data.get('moving_lines', []),
        original_hexagram=data.get('original_hexagram', ''),
        changed_hexagram=data.get('changed_hexagram', ''),
        result_text=data.get('result_text', ''),
    )
    return jsonify(result)


@app.route('/api/hexagram/records')
@require_auth
def api_get_hexagram_records():
    """获取起卦记录"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    records = db.get_hexagram_records(session['user_id'], limit, offset)
    return jsonify({'success': True, 'data': records, 'total': len(records)})


# ========== 风水记录 ==========

@app.route('/api/fengshui/record', methods=['POST'])
@require_auth
def api_save_fengshui_record():
    """保存风水记录"""
    data = request.json or {}
    result = db.save_fengshui_record(
        session['user_id'],
        record_type=data.get('type', ''),
        params=data.get('params', {}),
        result=data.get('result', {}),
    )
    return jsonify(result)


@app.route('/api/fengshui/records')
@require_auth
def api_get_fengshui_records():
    """获取风水记录"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    records = db.get_fengshui_records(session['user_id'], limit, offset)
    return jsonify({'success': True, 'data': records, 'total': len(records)})


# ========== 收藏 ==========

@app.route('/api/favorites', methods=['GET'])
@require_auth
def api_get_favorites():
    """获取收藏"""
    favorites = db.get_favorites(session['user_id'])
    return jsonify({'success': True, 'data': favorites})


@app.route('/api/favorites', methods=['POST'])
@require_auth
def api_toggle_favorite():
    """收藏/取消收藏"""
    data = request.json or {}
    result = db.toggle_favorite(
        session['user_id'],
        hexagram_id=data.get('hexagram_id', ''),
        note=data.get('note', ''),
    )
    return jsonify(result)


if __name__ == '__main__':
    print("启动周易八卦 Web 服务...")
    print("访问地址: http://localhost:5500")
    app.run(host='0.0.0.0', port=5500, debug=True)
