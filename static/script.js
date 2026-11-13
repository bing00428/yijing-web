/**
 * script.js - 周易八卦系统前端交互
 * 匹配 server.py API 端点
 */

// ========== 工具函数 ==========

function yaoSymbol(value) {
    var map = {
        6: { symbol: "\u2636", name: "老阴", type: "yin", moving: true },
        7: { symbol: "\u2630", name: "少阳", type: "yang", moving: false },
        8: { symbol: "\u2637", name: "少阴", type: "yin", moving: false },
        9: { symbol: "\u2631", name: "老阳", type: "yang", moving: true },
    };
    return map[value] || { symbol: "?", name: "未知", type: "yang", moving: false };
}

function trigramSymbol(name) {
    var map = {
        "乾": "\u2630", "坤": "\u2637", "震": "\u2633", "巽": "\u2634",
        "坎": "\u2635", "离": "\u2632", "艮": "\u2636", "兑": "\u2631",
    };
    return map[name] || "?";
}

function binaryToTrigram(binary) {
    var map = {
        7: "乾", 6: "兑", 5: "离", 4: "震",
        3: "巽", 2: "坎", 1: "艮", 0: "坤",
    };
    return map[binary] || "乾";
}

function renderYaoLines(yaoValues, movingLines) {
    if (!movingLines) movingLines = [];
    var html = '<div class="hex-lines">';
    for (var i = 5; i >= 0; i--) {
        var yao = yaoValues[i];
        var info = yaoSymbol(yao);
        var isMoving = movingLines.indexOf(i + 1) >= 0;
        var cls = info.type === "yang" ? "yang" : "yin";
        html += '<div class="' + cls + '">';
        if (info.type === "yang") {
            html += "\u2500\u2500\u2500";
        } else {
            html += "\u2500 \u2500";
        }
        if (isMoving) html += " \u26a1";
        html += '</div>';
    }
    html += '</div>';
    return html;
}

function showResult(containerId, html) {
    var container = document.getElementById(containerId);
    if (container) container.innerHTML = html;
}

function showLoading(containerId) {
    showResult(containerId, '<div class="loading"></div>');
}

// ========== 生肖数据（供本命五行测算使用）==========
var SHENG_XIAO_NAMES = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
    "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
    "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
};
var SHENG_XIAO_WU_XING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
};
var TIAN_GAN_WU_XING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
};
var DI_ZHI_WU_XING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
};

function ajax(url, data, callback) {
    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data || {}),
        credentials: "same-origin",
    }).then(function(resp) { return resp.json(); })
      .then(function(json) { callback(json); })
      .catch(function(err) { callback({ success: false, error: err.message }); });
}

function hexagramSymbol(upperName, lowerName) {
    var upperBits = 0, lowerBits = 0;
    if (upperName === "乾") upperBits = 0b111;
    else if (upperName === "兑") upperBits = 0b110;
    else if (upperName === "离") upperBits = 0b101;
    else if (upperName === "震") upperBits = 0b100;
    else if (upperName === "巽") upperBits = 0b011;
    else if (upperName === "坎") upperBits = 0b010;
    else if (upperName === "艮") upperBits = 0b001;
    else if (upperName === "坤") upperBits = 0b000;
    if (lowerName === "乾") lowerBits = 0b111;
    else if (lowerName === "兑") lowerBits = 0b110;
    else if (lowerName === "离") lowerBits = 0b101;
    else if (lowerName === "震") lowerBits = 0b100;
    else if (lowerName === "巽") lowerBits = 0b011;
    else if (lowerName === "坎") lowerBits = 0b010;
    else if (lowerName === "艮") lowerBits = 0b001;
    else if (lowerName === "坤") lowerBits = 0b000;
    var binary = (upperBits << 3) | lowerBits;
    return "\u2630\u2630\u2630\u2630\u2630\u2630"[binary % 16] || "?";
}

function colorWuxing(wx) {
    var colors = { "金": "#FFD700", "木": "#228B22", "水": "#1E90FF", "火": "#FF4500", "土": "#8B4513" };
    return colors[wx] || "#888";
}

// ========== 页面导航 ==========
var _pendingPage = null; // 未登录时暂存目标页面

/** 检查登录状态，未登录则弹出登录框 */
function checkAuthAndSwitch(pageId) {
    if (_isAuthenticated()) {
        switchPage(pageId);
    } else {
        _pendingPage = pageId;
        showLoginModal();
    }
}

/** 登录/注册后自动跳转到暂存的页面 */
function _navigatePendingPage() {
    var page = _pendingPage;
    _pendingPage = null;
    if (page) switchPage(page);
}

/** 检查是否已登录（快速检查，不调用 API）*/
function _isAuthenticated() {
    var userDiv = document.getElementById('user-dropdown');
    var authDiv = document.getElementById('navbar-auth');
    return userDiv && userDiv.style.display !== 'none' && (!authDiv || authDiv.style.display === 'none');
}

// ============================================
// 用户行为追踪
// ============================================

var _trackingPageStart = null;  // 当前页面进入时间
var _trackingQueue = [];        // 待发送的行为队列
var _trackingTimer = null;      // 批量发送定时器

/** 记录用户行为（本地排队 + 批量发送）*/
function trackAction(actionType, feature, params, page) {
    var action = {
        action_type: actionType,
        feature: feature,
        params: params || null,
        page: page || getCurrentPageName(),
    };
    _trackingQueue.push(action);
    // 延迟批量发送
    if (_trackingTimer) clearTimeout(_trackingTimer);
    _trackingTimer = setTimeout(_flushTrackingQueue, 2000);
}

/** 获取当前页面名称 */
function getCurrentPageName() {
    var active = document.querySelector('.page.active');
    if (!active) return '';
    var id = active.id || '';
    // 去掉 page- 前缀
    return id.replace(/^page-/, '');
}

/** 页面进入计时 */
function trackPageEnter() {
    _trackingPageStart = Date.now();
}

/** 页面离开计时 */
function trackPageLeave() {
    if (!_trackingPageStart) return;
    var duration = Math.round((Date.now() - _trackingPageStart) / 1000);  // 秒
    _trackingQueue.push({
        action_type: 'page_view',
        feature: 'page_view',
        page: getCurrentPageName(),
        duration: duration,
    });
    _trackingPageStart = null;
}

/** 发送队列中的行为数据 */
function _flushTrackingQueue() {
    if (_trackingQueue.length === 0) return;
    var actions = _trackingQueue.splice(0);
    _trackingTimer = null;
    ajax('/api/user/action', { actions: actions }, function() {
        // 静默发送，不阻塞
    });
}

/** 手动发送剩余队列 */
function flushTracking() {
    if (_trackingTimer) {
        clearTimeout(_trackingTimer);
        _trackingTimer = null;
    }
    _flushTrackingQueue();
}

/** 启动页面追踪 */
function initTracking() {
    trackPageEnter();
    // 页面关闭时发送最后的行为
    window.addEventListener('beforeunload', function() {
        trackPageLeave();
        flushTracking();
    });
    // 页面切换时追踪
    var origSwitchPage = window.switchPage;
    if (origSwitchPage) {
        window.switchPage = function(pageId) {
            trackPageLeave();
            origSwitchPage(pageId);
            // 延迟记录新页面进入
            setTimeout(trackPageEnter, 100);
        };
    }
}

document.querySelectorAll('.nav a, .feature-card').forEach(function(link) {
    link.addEventListener('click', function(e) {
        var page = this.getAttribute('data-page') || this.getAttribute('data-goto');
        if (page) { e.preventDefault(); checkAuthAndSwitch(page); }
    });
});

function switchPage(pageId) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
    // 移除导航 active 状态
    document.querySelectorAll('.navbar-nav a').forEach(function(a) { a.classList.remove('active'); });
    // 显示目标页面
    var page = document.getElementById('page-' + pageId);
    if (page) page.classList.add('active');
    // 设置导航 active
    var navLink = document.querySelector('.navbar-nav a[data-page="' + pageId + '"]');
    if (navLink) navLink.classList.add('active');

    // 清除八卦按钮 active
    var fengshuiBtns = document.querySelectorAll('#fengshui-gua-select .gua-btn');
    fengshuiBtns.forEach(function(btn) { btn.classList.remove('active'); });
    var baguaBtns = document.querySelectorAll('#bagua-select .gua-btn');
    baguaBtns.forEach(function(btn) { btn.classList.remove('active'); });

    // 切换侧栏模式（非首页启用左侧边栏导航）
    var wrapper = document.getElementById('page-wrapper');
    var navbar = document.getElementById('navbar');
    if (pageId === 'home') {
        wrapper.classList.remove('sidebar-mode');
        navbar.classList.remove('sidebar');
    } else {
        wrapper.classList.add('sidebar-mode');
        navbar.classList.add('sidebar');
    }

    // 页面切换时自动加载
    if (pageId === 'home') { /* 首页无需加载 */ }
    if (pageId === 'hexagrams') loadHexagramList();
    if (pageId === 'najia') loadNajiaData();
    if (pageId === '28_xiu') query28Xiu();
    if (pageId === 'wuxing_detail') switchWuxingDetail('liu_he');
    if (pageId === 'coin') { coinYaoValues = []; coinMovingLines = []; updateCoinUI(); }
    if (pageId === 'yarrow') { yarrowYaoValues = []; yarrowMovingLines = []; updateYarrowUI(); }
    if (pageId === 'bagua_detail') { /* 需要选择八卦 */ }
    if (pageId === 'profile') loadProfile();
}

// 八卦按钮点击事件
document.querySelectorAll('.gua-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        // 移除同组其他按钮的 active 状态
        var parent = this.parentElement;
        parent.querySelectorAll('.gua-btn').forEach(function(b) { b.classList.remove('active'); });
        this.classList.add('active');
    });
});

// ========== 铜钱起卦 ==========
var coinYaoValues = [];
var coinMovingLines = [];

function doCoinToss() {
    if (coinYaoValues.length >= 6) return;
    ajax('/api/coin/toss', {}, function(json) {
        if (!json.success) { showResult('coin-result', '<div class="error">起卦失败</div>'); return; }
        var d = json.data;
        coinYaoValues.push(d.yao_value);
        if (d.is_moving) coinMovingLines.push(coinYaoValues.length);
        updateCoinUI();
        if (coinYaoValues.length === 6) {
            renderCoinFinalResult();
            trackAction('divination', 'coin_toss', { yao_count: 6 });
        }
    });
}

function updateCoinUI() {
    var count = coinYaoValues.length;
    showResult('yao-count', '需点击 6 次，当前进度：' + count + '/6');
    if (count > 0) {
        var last = coinYaoValues[count - 1];
        var emojis = { 9: '\ud83e\ude99\ud83e\ude99\ud83e\ude99', 6: '字字字', 7: '字字\ud83e\ude99', 8: '字\ud83e\ude99\ud83e\ude99' };
        showResult('coin-display', '<div class="coin-animations">' + (emojis[last] || '???') + '</div>');
    }
    var html = '';
    for (var i = 0; i < coinYaoValues.length; i++) {
        var info2 = yaoSymbol(coinYaoValues[i]);
        var isMv = coinMovingLines.indexOf(i + 1) >= 0;
        html += '<div class="yao-history-item"><span>第' + (i+1) + '爻</span><span class="badge ' + (info2.moving ? 'badge-danger' : 'badge-info') + '">' + info2.name + (isMv ? ' ⚡动' : '') + '</span></div>';
    }
    var revHtml = '';
    for (var j = coinYaoValues.length - 1; j >= 0; j--) {
        var info3 = yaoSymbol(coinYaoValues[j]);
        var isMv2 = coinMovingLines.indexOf(j + 1) >= 0;
        revHtml += '<div class="yao-history-item"><span>第' + (j+1) + '爻</span><span>' + info3.symbol + ' ' + info3.name + (isMv2 ? ' ⚡动' : '') + '</span></div>';
    }
    if (revHtml) html += '<hr style="border-color:var(--border);margin:0.5rem 0;"><span style="color:var(--text-muted);font-size:0.8rem;">当前卦象</span>' + revHtml;
    showResult('coin-history', html);
    if (count >= 6) showResult('coin-result', '<p style="color:var(--success);">六爻已满，卦象已生成</p>');
}

function renderCoinFinalResult() {
    var binary = 0;
    for (var i = 0; i < 6; i++) { if (coinYaoValues[i] >= 7) binary |= (1 << i); }
    var upperName = binaryToTrigram((binary >> 3) & 0b111), lowerName = binaryToTrigram(binary & 0b111);
    ajax('/api/hexagram/search', { keyword: upperName + lowerName }, function(json) {
        var html = '';
        if (json.data && json.data.name) {
            var hx = json.data;
            html += '<div class="hex-display"><div class="hex-name-display" style="font-size:2rem;color:var(--gold);">' + hx.name + '</div>';
            html += '<div class="hex-detail-display">上' + trigramSymbol(hx.upper) + hx.upper + ' 下' + trigramSymbol(hx.lower) + hx.lower + '</div>';
            if (hx.judgment) html += '<div class="hex-judgment-display" style="background:rgba(212,168,67,0.1);border:1px solid var(--gold);border-radius:8px;padding:1rem;margin:1rem 0;">卦辞："' + hx.judgment + '"</div>';
            html += '</div>';
        } else {
            html += '<div class="hex-display"><div class="hex-name-display" style="font-size:2rem;color:var(--gold);">' + upperName + '上' + lowerName + '下</div></div>';
        }
        if (coinMovingLines.length > 0) {
            html += '<div class="moving-info" style="color:var(--accent);text-align:center;margin:0.5rem 0;">动爻：第' + coinMovingLines.join('、') + '爻</div>';
            html += renderYaoLines(coinYaoValues, coinMovingLines);
            var changed = coinYaoValues.map(function(v) { if (v === 9) return 8; if (v === 6) return 7; return v; });
            var cb = 0; for (var i = 0; i < 6; i++) { if (changed[i] >= 7) cb |= (1 << i); }
            var cu = binaryToTrigram((cb >> 3) & 0b111), cl = binaryToTrigram(cb & 0b111);
            ajax('/api/hexagram/search', { keyword: cu + cl }, function(cj) {
                if (cj.data && cj.data.name) {
                    html += '<div class="changed-hex" style="background:rgba(78,204,163,0.1);border:1px solid var(--success);border-radius:8px;padding:1rem;margin-top:1rem;"><h3 style="color:var(--success);">变卦：' + cj.data.name + '</h3></div>';
                }
                showResult('coin-final-result', html);
                showResult('coin-hex-display', html);
            });
        } else {
            html += '<div class="moving-info" style="color:var(--text-muted);text-align:center;">静卦，无动爻</div>';
            html += renderYaoLines(coinYaoValues, []);
            showResult('coin-final-result', html);
            showResult('coin-hex-display', html);
        }
    });
}

// ========== 蓍草起卦 ==========
var yarrowYaoValues = [];
var yarrowMovingLines = [];

function doYarrowToss() {
    if (yarrowYaoValues.length >= 6) return;
    ajax('/api/yarrow/calculate', {}, function(json) {
        if (!json.success) { showResult('yarrow-result', '<div class="error">起卦失败</div>'); return; }
        var d = json.data;
        yarrowYaoValues.push(d.yao_value);
        if (d.is_moving) yarrowMovingLines.push(yarrowYaoValues.length);
        updateYarrowUI();
        if (yarrowYaoValues.length === 6) {
            renderYarrowFinalResult();
            trackAction('divination', 'yarrow', { yao_count: 6 });
        }
    });
}

function updateYarrowUI() {
    var count = yarrowYaoValues.length;
    var html = '<p style="text-align:center;color:var(--warning);font-weight:bold;">演算进度：' + count + '/6 爻</p>';
    html += '<div class="hex-lines">';
    for (var i = count - 1; i >= 0; i--) {
        var info = yaoSymbol(yarrowYaoValues[i]);
        var isMv = yarrowMovingLines.indexOf(i + 1) >= 0;
        html += '<div class="' + info.type + '">' + info.symbol + info.symbol + info.symbol + (isMv ? ' ⚡' : '');
        html += '</div><div style="text-align:center;font-size:0.8rem;color:var(--text-muted);">第' + (i+1) + '爻 ' + info.name + '</div>';
    }
    html += '</div>';
    if (count >= 6) {
        html += '<p style="text-align:center;color:var(--success);">六爻已满</p>';
        showResult('yarrow-result', html);
    } else {
        html += '<div style="text-align:center;margin-top:1rem;"><button class="btn-primary" onclick="doYarrowToss()">🌿 演算下一爻</button></div>';
        showResult('yarrow-result', html);
    }
}

function renderYarrowFinalResult() {
    var binary = 0;
    for (var i = 0; i < 6; i++) { if (yarrowYaoValues[i] >= 7) binary |= (1 << i); }
    var upperName = binaryToTrigram((binary >> 3) & 0b111), lowerName = binaryToTrigram(binary & 0b111);
    var html = renderYaoLines(yarrowYaoValues, yarrowMovingLines);
    html += '<div class="hex-display"><div class="hex-name-display" style="font-size:2rem;color:var(--gold);">' + upperName + '上' + lowerName + '下</div></div>';
    ajax('/api/hexagram/search', { keyword: upperName + lowerName }, function(json) {
        if (json.data && json.data.name) {
            html = '<div class="hex-display"><div class="hex-name-display" style="font-size:2rem;color:var(--gold);">' + json.data.name + '</div>';
            html += '<div class="hex-detail-display">上' + trigramSymbol(json.data.upper) + json.data.upper + ' 下' + trigramSymbol(json.data.lower) + json.data.lower + '</div>';
            if (json.data.judgment) html += '<div class="hex-judgment-display" style="background:rgba(212,168,67,0.1);border:1px solid var(--gold);border-radius:8px;padding:1rem;margin:1rem 0;">卦辞："' + json.data.judgment + '"</div>';
            html += '</div>';
        }
        if (yarrowMovingLines.length > 0) {
            html += '<div class="moving-info" style="color:var(--accent);text-align:center;">动爻：第' + yarrowMovingLines.join('、') + '爻</div>';
            var changed = yarrowYaoValues.map(function(v) { if (v === 9) return 8; if (v === 6) return 7; return v; });
            var cb = 0; for (var i = 0; i < 6; i++) { if (changed[i] >= 7) cb |= (1 << i); }
            var cu = binaryToTrigram((cb >> 3) & 0b111), cl = binaryToTrigram(cb & 0b111);
            ajax('/api/hexagram/search', { keyword: cu + cl }, function(cj) {
                if (cj.data && cj.data.name) html += '<div class="changed-hex" style="background:rgba(78,204,163,0.1);border:1px solid var(--success);border-radius:8px;padding:1rem;margin-top:1rem;"><h3 style="color:var(--success);">变卦：' + cj.data.name + '</h3></div>';
                showResult('yarrow-final-result', html);
                showResult('yarrow-hex-display', html);
            });
        } else {
            showResult('yarrow-final-result', html + '<div class="moving-info" style="color:var(--text-muted);text-align:center;">静卦</div>');
            showResult('yarrow-hex-display', html + '<div class="moving-info" style="color:var(--text-muted);text-align:center;">静卦</div>');
        }
    });
}

// ========== 时间起卦 ==========
function doTimeDivination() {
    var year = parseInt(document.getElementById('time-year').value) || 2025;
    var month = parseInt(document.getElementById('time-month').value) || 1;
    var day = parseInt(document.getElementById('time-day').value) || 1;
    var hour = parseInt(document.getElementById('time-hour').value) || 6;
    showLoading('time-result');
    showLoading('time-hex-display');
    ajax('/api/time/divination', { year: year, month: month, day: day, hour: hour, minute: 0 }, function(json) {
        if (!json.success) { showResult('time-result', '<div class="error">起卦失败</div>'); showResult('time-hex-display', '<div class="error">起卦失败</div>'); return; }
        var d = json.data;
        var html = '<div class="hex-display">';

        // 卦名
        html += '<div class="hex-name-display" style="font-size:2rem;color:var(--gold);">' + (d.name || '起卦中') + '</div>';
        if (d.upper && d.lower) html += '<div class="hex-detail-display">上' + trigramSymbol(d.upper) + d.upper + ' 下' + trigramSymbol(d.lower) + d.lower + '</div>';

        // 卦辞
        if (d.judgment) {
            html += '<div class="hex-judgment-display" style="background:rgba(212,168,67,0.1);border:1px solid var(--gold);border-radius:8px;padding:1rem;margin:1rem 0;">';
            html += '<h4 style="color:var(--gold);font-size:0.95rem;margin-bottom:0.5rem;">卦辞</h4>';
            html += '<p style="color:var(--text);font-size:0.9rem;line-height:1.6;">"' + d.judgment + '"</p>';
            html += '</div>';
        }

        // 大象传
        if (d.xiang_comment) {
            html += '<div class="hex-judgment-display" style="background:rgba(168,130,255,0.08);border:1px solid rgba(168,130,255,0.3);border-radius:8px;padding:1rem;margin:1rem 0;">';
            html += '<h4 style="color:#a882ff;font-size:0.95rem;margin-bottom:0.5rem;">象曰</h4>';
            html += '<p style="color:var(--text);font-size:0.9rem;line-height:1.6;">' + d.xiang_comment + '</p>';
            html += '</div>';
        }

        // 动爻 + 爻辞
        if (d.moving_yao) {
            html += '<div class="moving-info" style="color:var(--accent);text-align:center;margin-bottom:0.5rem;">动爻：第' + d.moving_yao + '爻（' + (d.yao_name || '') + '）</div>';
            if (d.yao_text) {
                html += '<div class="hex-judgment-display" style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);border-radius:8px;padding:1rem;margin:1rem 0;">';
                html += '<h4 style="color:#fbbf24;font-size:0.95rem;margin-bottom:0.5rem;">' + (d.yao_name || '动爻') + ' 爻辞</h4>';
                html += '<p style="color:var(--text);font-size:0.9rem;line-height:1.6;margin-bottom:0.5rem;">"' + d.yao_text + '"</p>';
                if (d.yao_note) {
                    html += '<p style="color:var(--text-muted);font-size:0.85rem;line-height:1.5;font-style:italic;">' + d.yao_note + '</p>';
                }
                html += '</div>';
            }
        }

        // 变卦
        if (d.changed_name && d.changed_name !== d.name) {
            html += '<div class="changed-hex" style="background:rgba(78,204,163,0.1);border:1px solid var(--success);border-radius:8px;padding:1rem;margin-top:1rem;">';
            html += '<h3 style="color:var(--success);">变卦：' + d.changed_name + '</h3>';
            if (d.changed_upper && d.changed_lower) {
                html += '<div style="color:var(--text);font-size:0.9rem;margin-top:0.5rem;">上' + trigramSymbol(d.changed_upper) + d.changed_upper + ' 下' + trigramSymbol(d.changed_lower) + d.changed_lower + '</div>';
            }
            html += '</div>';
        }

        // 白话解析（动态生成）
        html += '<div style="background:rgba(78,204,163,0.06);border:1px solid rgba(78,204,163,0.2);border-radius:8px;padding:1rem;margin-top:1rem;">';
        html += '<h4 style="color:var(--success);font-size:0.95rem;margin-bottom:0.5rem;">💡 白话解析</h4>';
        html += generateTimeDivinationInterpretation(d);
        html += '</div>';

        // 命卦解读（倪海厦解读）
        html += '<div class="mingua-section" style="background:rgba(255,183,77,0.06);border:1px solid rgba(255,183,77,0.2);border-radius:8px;padding:1rem;margin-top:1rem;">';
        html += '<h4 style="color:#ffb74d;font-size:0.95rem;margin-bottom:0.5rem;">🔮 命卦解读（倪海厦）</h4>';
        html += '<div id="mingua-content" style="display:flex;align-items:center;justify-content:center;min-height:3rem;color:var(--text-muted);">加载中...</div>';
        html += '</div>';

        html += '</div>';
        showResult('time-result', html);
        showResult('time-hex-display', html);
        trackAction('divination', 'time_divination', { year: year, month: month, day: day, hour: hour });

        // 加载命卦数据
        loadMinghuaData(d.name);
    });
}

/** 加载命卦数据 */
function loadMinghuaData(hexName) {
    ajax('/api/mingua/lookup', { hexagram: hexName }, function(json) {
        var container = document.getElementById('mingua-content');
        if (!json.success || !json.data) {
            container.innerHTML = '<p style="color:var(--text-muted);">暂无命卦数据</p>';
            return;
        }
        var m = json.data;
        if (!m.xiantian && !m.houtian && !m.liunian) {
            container.innerHTML = '<p style="color:var(--text-muted);">暂无命卦数据</p>';
            return;
        }
        var html = '';
        if (m.xiantian) {
            html += '<div style="margin-bottom:0.75rem;"><b style="color:#ffb74d;font-size:0.9rem;">先天卦：</b><p style="color:var(--text);font-size:0.85rem;line-height:1.6;margin:0.25rem 0 0 0;">' + m.xiantian + '</p></div>';
        }
        if (m.houtian) {
            html += '<div style="margin-bottom:0.75rem;"><b style="color:#ffb74d;font-size:0.9rem;">后天卦：</b><p style="color:var(--text);font-size:0.85rem;line-height:1.6;margin:0.25rem 0 0 0;">' + m.houtian + '</p></div>';
        }
        if (m.liunian) {
            html += '<div><b style="color:#ffb74d;font-size:0.9rem;">流年卦：</b><p style="color:var(--text);font-size:0.85rem;line-height:1.6;margin:0.25rem 0 0 0;">' + m.liunian + '</p></div>';
        }
        container.innerHTML = html;
    });
}

/** 生成时间起卦白话解析 */
function generateTimeDivinationInterpretation(d) {
    var lines = [];

    // 总体判断
    var judgment_meaning = getJudgmentMeaning(d.name, d.judgment);
    lines.push('<p style="color:var(--text);font-size:0.9rem;line-height:1.7;margin-bottom:0.5rem;"><b>【总体】</b>' + judgment_meaning + '</p>');

    // 动爻解读
    if (d.yao_text && d.yao_name) {
        var yao_meaning = getYaoInterpretation(d.moving_yao, d.yao_text, d.name);
        lines.push('<p style="color:var(--text);font-size:0.9rem;line-height:1.7;margin-bottom:0.5rem;"><b>【动爻提示】</b>第' + d.moving_yao + '爻（' + d.yao_name + '）："' + d.yao_text + '" —— ' + yao_meaning + '</p>');
    }

    // 变卦提示
    if (d.changed_name && d.changed_name !== d.name) {
        lines.push('<p style="color:var(--text);font-size:0.9rem;line-height:1.7;margin-bottom:0.5rem;"><b>【发展趋势】</b>事情将向<b>' + d.changed_name + '</b>的方向发展，建议顺势而为。</p>');
    }

    return lines.join('');
}

/** 卦辞白话解释 */
function getJudgmentMeaning(name, judgment) {
    var meanings = {
        '乾为天': '元亨利贞表示大吉大利。天道刚健，适合积极行动，但需坚守正道。',
        '坤为地': '柔顺包容，适合以静制动。做事要脚踏实地，顺应自然。',
        '水雷屯': '起始艰难，但充满生机。好比草木破土而出，需要耐心培育。',
        '山水蒙': '启蒙之象，宜虚心求学。此时不明，需要请教有识之士。',
        '水天需': '耐心等待时机。前方有困难，但只要守正不躁，终能成功。',
        '天水讼': '容易发生争执，宜退让化解。做事要谨慎，避免冲突升级。',
        '地水师': '需要组织和纪律。凡事要有人领导，众人同心才能成事。',
        '水地比': '亲密辅佐之象，利于合作交友。与人和睦相处，可得助力。',
        '风天小畜': '力量尚小，宜蓄积准备。暂时不宜大举行动，先做好基础。',
        '天泽履':  '如履薄冰，小心行事。虽然处境有风险，但守正可安。',
        '地天泰': '通达安泰之象，吉祥。上下和谐，事事顺利，把握好运。',
        '天地否': '闭塞不通，宜守不宜进。此时运势不佳，耐心等待转机。',
        '天火同人': '志同道合，团结协作。与人合作可成大事，光明正大。',
        '火天大有': '丰收大有，运势极佳。顺天依时，大有所获。',
        '地山谦': '谦虚受益，满招损。保持谦逊态度，必有福报。',
        '雷地豫': '安逸喜悦，顺势而为。把握良机，可以有所作为。',
        '泽雷随': '随机应变，顺势而行。不要固执己见，灵活应对。',
        '山风蛊': '整治积弊之时。事情有败坏，需要大刀阔斧改革。',
        '地泽临': '居高临下，指导他人。运势上升，可大展宏图。',
        '风泽中孚': '诚信为本，以诚待人。内心真诚，可以感化他人。',
        '雷风恒': '持之以恒，持之以恒。做事要有恒心，不可三心二意。',
        '天山遁': '退避隐居，明哲保身。小人当道，暂时退让为佳。',
        '雷天大壮': '气势壮盛，不可妄动。虽然力量强大，但要守法度。',
        '泽天夬': '果断决断，清除小人。当机立断，不可犹豫。',
        '坤为地': '柔顺包容，宜静守。以退为进，等待时机。',
        '兑为泽': '喜悦和悦，利于交往。心情愉悦，人际关系和谐。',
        '离为火': '光明附丽，依附正道。如日中天，但要懂得收敛。',
        '震为雷': '震动惊恐，但可无咎。遇事不惊，处变不惊。',
        '巽为风': '柔顺渗透，循序渐进。如风无孔不入，以柔克刚。',
        '坎为水': '重重险阻，但可通行。身处险境，要坚守本心。',
        '艮为山': '止步静止，安于本位。该停则停，不可强求。',
        '水火既济': '事情已成，但要防衰。成功之后要居安思危。',
        '火水未济': '事犹未成，但可努力。尚未成功，但前景可期。'
    };
    if (meanings[name]) return meanings[name];
    // 通用解释
    if (judgment && judgment.length > 10) {
        return '此卦卦辞为"' + judgment.slice(0, 20) + '..."，需要结合具体问题来理解。建议静心思考卦辞含义。';
    }
    return '此卦需要结合您所问之事来解读。建议诚心静思，体会卦象深意。';
}

/** 动爻白话解读 */
function getYaoInterpretation(yaoNum, yaoText, hexName) {
    // 常见爻辞的快速解释
    var yaoInterp = {
        '潜龙，勿用': '时机未到，宜韬光养晦，不要急于行动。',
        '见龙在田': '才华初显，利于结交贵人，展现自己。',
        '利见大人': '有贵人相助，可寻求帮助或展示才华。',
        '君子终日乾乾': '要勤奋不懈，早晚警惕，虽然有风险但最终无害。',
        '或跃在渊': '处于进退之间，可以大胆尝试，没有风险。',
        '飞龙在天': '时机成熟，大展宏图，利见贵人。',
        '亢龙有悔': '高处不胜寒，过刚易折，要懂得适可而止。',
        '履霜，坚冰至': '事物发展有征兆，要见微知著，提前防范。',
        '黄裳，元吉': '谦逊低调可得大吉，位置合适自然顺利。',
        '突如其来如': '事情突然变化，要从容应对，不要惊慌。'
    };
    if (yaoInterp[yaoText]) return yaoInterp[yaoText];

    // 根据爻位给出通用建议
    var positions = ['初爻','二爻','三爻','四爻','五爻','上爻'];
    var suggestions = [
        '事情刚开始，要打好基础，不可操之过急。',
        '处于发展阶段，要稳扎稳打，把握方向。',
        '处于关键转折期，要谨慎行事，警惕风险。',
        '已进入上层阶段，要审时度势，灵活应对。',
        '处于最佳位置，可大展手脚，但勿骄傲。',
        '事物发展到尽头，要考虑退路或转变方向。'
    ];
    if (yaoNum >= 1 && yaoNum <= 6) {
        return positions[yaoNum-1] + '提示：' + suggestions[yaoNum-1];
    }
    return '此爻提示您需要关注当前所处阶段的特殊含义。';
}

// ========== 六十四卦查询 ==========
var hexagramCache = [];
function loadHexagramList() {
    if (hexagramCache.length > 0) { renderHexagramList(hexagramCache); return; }
    showLoading('hex-list');
    ajax('/api/hexagram/search', { keyword: '' }, function(json) {
        if (!json.success || !json.data) { showResult('hex-list', '<div class="error">加载失败</div>'); return; }
        hexagramCache = json.data;
        renderHexagramList(json.data);
    });
}
function renderHexagramList(list) {
    var html = '';
    for (var i = 0; i < list.length; i++) {
        var hx = list[i];
        html += '<div class="hexagram-item" data-name="' + (hx.name||'') + '" data-upper="' + (hx.upper||'') + '" data-lower="' + (hx.lower||'') + '" style="cursor:pointer;">';
        html += '<span class="hex-name">' + (hx.name || hx.number || '') + '</span>';
        html += '<span class="hex-detail">上' + (hx.upper||'?') + ' 下' + (hx.lower||'?') + '</span>';
        html += '</div>';
    }
    showResult('hex-list', html);
}
function filterHexagrams() {
    var query = (document.getElementById('hex-search').value || '').toLowerCase();
    document.querySelectorAll('.hexagram-item').forEach(function(item) {
        var name = (item.dataset.name||'').toLowerCase();
        var upper = (item.dataset.upper||'').toLowerCase();
        var lower = (item.dataset.lower||'').toLowerCase();
        item.style.display = (name.indexOf(query)>=0 || upper.indexOf(query)>=0 || lower.indexOf(query)>=0) ? '' : 'none';
    });
    if (query.length > 0) {
        trackAction('feature_use', 'hexagram_search', { query: query });
    }
}

// 卦名点击事件
document.addEventListener('click', function(e) {
    var item = e.target.closest('.hexagram-item');
    if (item) {
        var name = item.dataset.name;
        var upper = item.dataset.upper;
        var lower = item.dataset.lower;
        if (name) showHexagramDetail(name, upper, lower);
    }
});

function showHexagramDetail(name, upper, lower) {
    // 从缓存中查找
    var cached = null;
    if (hexagramCache.length > 0) {
        for (var i = 0; i < hexagramCache.length; i++) {
            if (hexagramCache[i].name === name) {
                cached = hexagramCache[i];
                break;
            }
        }
    }

    var html = '<div class="hex-display">';
    html += '<div class="hex-name-display" style="font-size:2rem;color:var(--gold);margin-bottom:0.5rem;">' + name + '</div>';
    html += '<div class="hex-detail-display">上' + trigramSymbol(upper) + upper + ' 下' + trigramSymbol(lower) + lower + '</div>';

    if (cached) {
        if (cached.judgment) {
            html += '<div class="hex-judgment-display" style="background:rgba(212,168,67,0.1);border:1px solid var(--gold);border-radius:8px;padding:1rem;margin:1rem 0;">';
            html += '<h4 style="color:var(--gold);font-size:0.95rem;margin-bottom:0.5rem;">卦辞</h4>';
            html += '<p style="color:var(--text);font-size:0.9rem;line-height:1.6;">"' + cached.judgment + '"</p>';
            html += '</div>';
        }

        // 爻辞
        if (cached.lines && cached.lines.length > 0) {
            html += '<h4 style="color:var(--gold);font-size:0.95rem;margin:1rem 0 0.5rem;">爻辞</h4>';
            cached.lines.forEach(function(line) {
                html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;padding:0.25rem 0.5rem;background:rgba(255,255,255,0.02);border-radius:4px;">';
                html += '<b style="color:var(--gold);">' + (line.yao_name || '') + '</b> ' + (line.text || '') + '</p>';
            });
        }

        // 十翼
        if (cached.shi_yi && Object.keys(cached.shi_yi).length > 0) {
            html += '<h4 style="color:var(--gold);font-size:0.95rem;margin:1rem 0 0.5rem;">十翼</h4>';
            var shiYi = cached.shi_yi;
            var shiYiTitles = {
                'comprehensive': '彖传',
                'image': '象传',
                'explanation': '文言传',
                'structure': '系辞传',
                'bare_bones': '说卦传',
                'order': '序卦传',
                'transformation': '杂卦传',
            };
            for (var key in shiYi) {
                var title = shiYiTitles[key] || key;
                var content = shiYi[key];
                if (content) {
                    html += '<div style="margin:0.5rem 0;padding:0.5rem;background:rgba(212,168,67,0.05);border-radius:6px;border-left:3px solid var(--gold);">';
                    html += '<h5 style="color:var(--gold);font-size:0.85rem;margin-bottom:0.25rem;">' + title + '</h5>';
                    html += '<p style="color:var(--text);font-size:0.8rem;line-height:1.6;">' + content + '</p>';
                    html += '</div>';
                }
            }
        }
    }

    html += '</div>';
    var detailDiv = document.getElementById('hex-detail');
    detailDiv.style.display = 'block';
    detailDiv.innerHTML = html;
    detailDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    trackAction('feature_use', 'hexagram_detail', { hexagram: name, upper: upper, lower: lower });
}

// ========== 五行生克 ==========
function queryWuxing() {
    var w1 = document.getElementById('wuxing1').value;
    var w2 = document.getElementById('wuxing2').value;
    showLoading('wuxing-result');
    ajax('/api/wuxing/relationship', { wuxing1: w1, wuxing2: w2 }, function(json) {
        if (!json.success) { showResult('wuxing-result', '<div class="error">查询失败</div>'); return; }
        var d = json.data;
        var colors = {'金': '#FFD700', '木': '#228B22', '水': '#1E90FF', '火': '#FF4500', '土': '#8B4513'};
        var c1 = colors[w1] || '#888';
        var c2 = colors[w2] || '#888';
        var lqColors = {'父母': '#4fc3f7', '兄弟': '#fff176', '子孙': '#81c784', '妻财': '#ffb74d', '官鬼': '#e57373'};

        var html = '<div style="text-align:center;margin-bottom:1rem;">';
        html += '<h3 style="color:var(--gold);font-size:1.3rem;margin-bottom:0.75rem;">五行关系分析</h3>';
        html += '<div style="margin:1rem 0;">';
        html += '<span style="font-size:2.5rem;font-weight:bold;color:' + c1 + '">' + w1 + '</span>';
        html += '<span style="font-size:2rem;color:var(--text-muted);margin:0 1rem;">→</span>';
        html += '<span style="font-size:2.5rem;font-weight:bold;color:' + c2 + '">' + w2 + '</span>';
        html += '</div>';
        html += '<div style="font-size:1.8rem;color:var(--gold);font-weight:bold;margin:0.75rem 0;">' + (d.relationship || '') + '</div>';
        if (d.liu_qin) {
            var lqColor = lqColors[d.liu_qin] || 'var(--text)';
            html += '<div style="font-size:1rem;color:' + lqColor + ';font-weight:bold;margin:0.5rem 0;">';
            html += '六亲：' + d.liu_qin + '（' + d.wuxing1 + '为' + (d.wuxing1||'') + ' → ' + d.wuxing2 + '为' + (d.wuxing2||'') + '）';
            html += '</div>';
        }
        html += '</div>';

        if (d.detail) {
            html += '<hr style="border:none;border-top:1px solid var(--border);margin:1rem 0;"/>';
            html += '<p>关系：<b>' + (d.detail['关系'] || d.detail.direction || '') + '</b></p>';
            html += '<p>元素一视角：<b>' + (d.detail['元素一视角'] || d.detail.from_obj1 || '') + '</b></p>';
            html += '<p>元素二视角：<b>' + (d.detail['元素二视角'] || d.detail.from_obj2 || '') + '</b></p>';
            html += '<p>综合：<b>' + (d.detail['综合'] || d.detail.compatibility || '') + '</b></p>';
        }

        // 旺相休囚死
        if (d.strength) {
            html += '<hr style="border:none;border-top:1px solid var(--border);margin:1rem 0;"/>';
            html += '<h4 style="color:var(--gold);font-size:1rem;margin:1rem 0 0.5rem;">旺相休囚死（春季参考）</h4>';
            html += '<p>' + w1 + ' 在春季的状态：<b>' + (d.strength || '') + '</b></p>';
            html += '<p>' + w2 + ' 在春季的状态：<b>' + (d.strength || '') + '</b></p>';
        }

        // 十神详解
        if (d.shi_shen && Object.keys(d.shi_shen).length > 0) {
            var ss = d.shi_shen;
            html += '<hr style="border:none;border-top:1px solid var(--border);margin:1rem 0;"/>';
            var lqName = d.liu_qin || '';
            var lqColor = lqColors[lqName] || 'var(--gold)';
            html += '<h4 style="color:' + lqColor + ';font-size:1rem;margin:1rem 0 0.5rem;">📖 ' + lqName + '（十神详解）</h4>';
            html += '<p style="color:var(--text);font-size:0.85rem;"><b>含义：</b>' + (ss.含义 || '') + '</p>';
            html += '<p style="color:#81c784;font-size:0.85rem;"><b>正面：</b>' + (ss.正面 || '') + '</p>';
            html += '<p style="color:#e57373;font-size:0.85rem;"><b>负面：</b>' + (ss.负面 || '') + '</p>';

            if (ss.占断 && Object.keys(ss.占断).length > 0) {
                html += '<h5 style="color:var(--gold);font-size:0.9rem;margin:0.75rem 0 0.5rem;">占断参考：</h5>';
                html += '<ul style="color:var(--text);font-size:0.85rem;line-height:1.8;padding-left:1.5rem;">';
                for (var area in ss.占断) {
                    html += '<li><b>' + area + '：</b>' + ss.占断[area] + '</li>';
                }
                html += '</ul>';
            }
        }

        showResult('wuxing-result', html);
        trackAction('feature_use', 'wuxing_relationship', { wuxing1: w1, wuxing2: w2 });
    });
}
function switchWuxingDetail(type, btnEl) {
    document.querySelectorAll('.detail-tab-btn').forEach(function(btn) { btn.classList.remove('active'); });
    var target = btnEl || (typeof event !== 'undefined' && event && event.target);
    if (target) target.classList.add('active');
    ajax('/api/wuxing/details', { type: type }, function(json) {
        if (!json.success) { showResult('wuxing-detail-content', '<div class="error">加载失败</div>'); return; }
        var d = json.data;
        var titles = { liu_he: '六合', san_he: '三合', liu_chong: '六冲', san_xing: '三刑', liu_hai: '六害' };
        var html = '<h3>' + (titles[type] || type) + '</h3>';
        if (Array.isArray(d)) {
            if (d.length > 0 && typeof d[0] === 'object') {
                var cols = Object.keys(d[0]);
                html += '<table class="data-table"><thead><tr>';
                cols.forEach(function(c) { html += '<th>' + c + '</th>'; });
                html += '</tr></thead><tbody>';
                d.forEach(function(row) {
                    html += '<tr>';
                    cols.forEach(function(c) { html += '<td>' + (row[c] || '') + '</td>'; });
                    html += '</tr>';
                });
                html += '</tbody></table>';
            }
        }
        showResult('wuxing-detail-content', html);
        trackAction('feature_use', 'wuxing_detail', { type: type });
    });
}
function doBenming() {
    var year = parseInt(document.getElementById('benming-year').value) || 1990;
    var month = parseInt(document.getElementById('benming-month').value) || 0;
    var day = parseInt(document.getElementById('benming-day').value) || 0;
    var hour = parseInt(document.getElementById('benming-hour').value) || 0;
    showLoading('benming-result');
    ajax('/api/benming/calculate', { year: year, month: month, day: day, hour_index: hour }, function(json) {
        if (!json.success) { showResult('benming-result', '<div class="error">测算失败</div>'); return; }
        var d = json.data;
        var colors = {'金': '#FFD700', '木': '#228B22', '水': '#1E90FF', '火': '#FF4500', '土': '#8B4513', '未知': '#888'};

        var html = '';

        // ====== 头部：本命五行 ======
        var mb = d.mingben || {};
        var benming = mb.benming_wuxing || '未知';
        var bcolor = colors[benming] || 'var(--text)';
        html += '<div style="text-align:center;margin-bottom:1.5rem;padding:1.5rem;background:rgba(212,168,67,0.05);border-radius:12px;border:1px solid var(--border);">';
        html += '<h3 style="color:var(--gold);font-size:1.1rem;margin-bottom:0.5rem;font-weight:normal;">本命五行（纳音）</h3>';
        html += '<div style="font-size:4.5rem;font-weight:bold;color:' + bcolor + ';margin:0.5rem 0;text-shadow:0 0 20px ' + bcolor + '40;">' + benming + '</div>';
        html += '<p style="color:var(--text-muted);margin:0.25rem 0 0;">';
        if (mb.nayin_name) html += '纳音：' + mb.nayin_name;
        if (mb.nayin_wuxing) html += '（' + mb.nayin_wuxing + '）';
        html += '</p>';
        if (mb.description) {
            html += '<p style="color:var(--text-muted);font-style:italic;margin:0.5rem 0 0;font-size:0.85rem;">"' + mb.description + '"</p>';
        }
        html += '</div>';

        // ====== 生肖 ======
        html += '<div class="card" style="margin-bottom:1rem;">';
        html += '<div class="card-header"><span class="icon">🐴</span><h3>生肖信息</h3></div>';
        html += '<div style="padding:0.5rem 1rem;">';
        if (mb.shengxiao) {
            var sxDz = mb.di_zhi || '';
            var sxName = SHENG_XIAO_NAMES && SHENG_XIAO_NAMES[sxDz] || mb.shengxiao;
            var sxWx = SHENG_XIAO_WU_XING && SHENG_XIAO_WU_XING[sxDz] || (mb.shengxiao_wuxing || '');
            html += '<p style="margin:0.25rem 0;">生肖：<b style="color:var(--gold);">' + (sxName || mb.shengxiao) + '</b></p>';
            if (sxDz) html += '<p style="margin:0.25rem 0;">年支：<b style="color:var(--gold);">' + sxDz + '</b></p>';
            if (sxWx) html += '<p style="margin:0.25rem 0;">生肖五行：<b style="color:' + (colors[sxWx] || 'var(--text)') + ';">' + sxWx + '</b></p>';
        }
        html += '</div></div>';

        // ====== 四柱八字 ======
        html += '<div class="card" style="margin-bottom:1rem;">';
        html += '<div class="card-header"><span class="icon">📜</span><h3>四柱八字</h3></div>';
        html += '<div style="padding:0.5rem 1rem;">';

        // 年柱
        var yearGz = mb.gan_zhi || '';
        if (yearGz) html += '<p style="margin:0.25rem 0;">年柱：<b style="color:var(--gold);">' + yearGz + '</b></p>';

        // 月柱
        if (mb.month_gan_zhi) {
            html += '<p style="margin:0.25rem 0;">月柱：<b style="color:var(--gold);">' + mb.month_gan_zhi + '</b> <span style="color:var(--text-muted);font-size:0.8rem;">（' + (mb.month_wuxing || '') + '）</span></p>';
        }

        // 日柱（日主/日元）
        if (mb.day_gan_zhi) {
            html += '<p style="margin:0.25rem 0;">日柱：<b style="color:var(--gold);">' + mb.day_gan_zhi + '</b>';
            if (mb.day_wuxing) html += ' <span style="color:' + (colors[mb.day_wuxing] || 'var(--text)') + ';">日主（' + mb.day_wuxing + '）</span>';
            html += '</p>';
        }

        // 时柱
        if (mb.hour_gan_zhi) {
            html += '<p style="margin:0.25rem 0;">时柱：<b style="color:var(--gold);">' + mb.hour_gan_zhi + '</b>';
            if (mb.hour_wuxing) html += ' <span style="color:' + (colors[mb.hour_wuxing] || 'var(--text)') + ';">（' + mb.hour_wuxing + '）</span>';
            if (mb.shichen) html += ' <span style="color:var(--text-muted);font-size:0.8rem;">' + mb.shichen + '</span>';
            html += '</p>';
        }

        // 四柱表格
        var fp = mb.four_pillars || {};
        if (fp.year || fp.month || fp.day || fp.hour) {
            html += '<table style="width:100%;margin-top:0.75rem;border-collapse:collapse;font-size:0.85rem;">';
            html += '<tr style="border-bottom:1px solid var(--border);"><th style="padding:0.4rem;text-align:center;color:var(--gold);">柱</th><th style="padding:0.4rem;text-align:center;color:var(--gold);">天干</th><th style="padding:0.4rem;text-align:center;color:var(--gold);">地支</th><th style="padding:0.4rem;text-align:center;color:var(--gold);">五行</th></tr>';
            var pillarOrder = ['year', 'month', 'day', 'hour'];
            var pillarLabels = ['年柱', '月柱', '日柱', '时柱'];
            for (var pi = 0; pi < 4; pi++) {
                var pk = pillarOrder[pi];
                var gz = fp[pk];
                if (gz && gz.length >= 2) {
                    var tg = gz.charAt(0), dz = gz.charAt(1);
                    var tgWx = TIAN_GAN_WU_XING && TIAN_GAN_WU_XING[tg] || '';
                    html += '<tr style="border-bottom:1px solid var(--border);"><td style="padding:0.4rem;text-align:center;color:var(--text-muted);">' + pillarLabels[pi] + '</td><td style="padding:0.4rem;text-align:center;color:' + (colors[tgWx] || 'var(--text)') + ';">' + tg + '</td><td style="padding:0.4rem;text-align:center;color:' + (colors[DI_ZHI_WU_XING && DI_ZHI_WU_XING[dz] || ''] || 'var(--text)') + ';">' + dz + '</td><td style="padding:0.4rem;text-align:center;color:' + (colors[tgWx] || 'var(--text)') + ';">' + (tgWx || '-') + '</td></tr>';
                }
            }
            html += '</table>';
        }

        html += '</div></div>';

        // ====== 五行强弱分析 ======
        var s = d.strength || {};
        if (s.scores) {
            html += '<div class="card" style="margin-bottom:1rem;">';
            html += '<div class="card-header"><span class="icon">⚖️</span><h3>五行强弱分析</h3></div>';
            html += '<div style="padding:0.5rem 1rem;">';

            // 平衡度
            if (s.balance) {
                var balColor = s.balance === '均衡' ? 'var(--success)' : 'var(--warning)';
                html += '<p style="margin:0 0 0.75rem;"><b style="color:' + balColor + ';">五行平衡度：</b>' + s.balance + '</p>';
            }

            // 五行得分（进度条）
            html += '<p style="color:var(--text);font-size:0.85rem;margin-bottom:0.5rem;"><b>五行得分：</b></p>';
            var maxScore = 0;
            for (var wx in s.scores) { if (s.scores[wx] > maxScore) maxScore = s.scores[wx]; }
            html += '<div style="margin-bottom:0.75rem;">';
            var wxOrder = ['金', '木', '水', '火', '土'];
            for (var wi = 0; wi < wxOrder.length; wi++) {
                var wx = wxOrder[wi];
                var score = s.scores[wx] || 0;
                var pct = maxScore > 0 ? Math.round(score / maxScore * 100) : 0;
                var wxColor = colors[wx] || 'var(--text)';
                html += '<div style="display:flex;align-items:center;margin:0.35rem 0;gap:0.5rem;">';
                html += '<span style="color:' + wxColor + ';font-weight:bold;width:1.5rem;text-align:center;">' + wx + '</span>';
                html += '<div style="flex:1;background:var(--border);border-radius:4px;height:18px;overflow:hidden;">';
                html += '<div style="width:' + pct + '%;background:' + wxColor + ';height:100%;border-radius:4px;transition:width 0.3s;"></div>';
                html += '</div>';
                html += '<span style="color:var(--text-muted);font-size:0.8rem;width:2rem;text-align:right;">' + score + '</span>';
                html += '</div>';
            }
            html += '</div>';

            // 排名
            if (s.ranking && s.ranking.length > 0) {
                html += '<p style="color:var(--text);font-size:0.85rem;margin-bottom:0.5rem;"><b>五行排名：</b></p>';
                html += '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.75rem;">';
                for (var ri = 0; ri < s.ranking.length; ri++) {
                    var r = s.ranking[ri];
                    html += '<span style="padding:0.3rem 0.75rem;background:' + (colors[r[0]] || 'var(--text)') + '20;border:1px solid ' + (colors[r[0]] || 'var(--text)') + '40;border-radius:20px;font-size:0.8rem;color:' + (colors[r[0]] || 'var(--text)') + ';">';
                    html += (ri + 1) + '. ' + r[0] + '（' + r[1] + '分）</span>';
                }
                html += '</div>';
            }

            // 最强最弱
            if (s.strongest) {
                html += '<p style="margin:0.5rem 0;"><b style="color:#81c784;">最强：</b><span style="color:' + (colors[s.strongest[0]] || 'var(--text)') + ';">' + s.strongest[0] + '（' + s.strongest[1] + '分）</span></p>';
            }
            if (s.weakest) {
                html += '<p style="margin:0.5rem 0;"><b style="color:#e57373;">最弱：</b><span style="color:' + (colors[s.weakest[0]] || 'var(--text)') + ';">' + s.weakest[0] + '（' + s.weakest[1] + '分）</span></p>';
            }

            // 五行明细
            if (s.detail) {
                html += '<p style="color:var(--text);font-size:0.85rem;margin:0.75rem 0 0.5rem;"><b>五行明细：</b></p>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">';
                for (var dxi = 0; dxi < wxOrder.length; dxi++) {
                    var wxx = wxOrder[dxi];
                    var items = s.detail[wxx] || [];
                    html += '<div style="padding:0.5rem;background:' + (colors[wxx] || 'var(--text)') + '10;border-radius:6px;border:1px solid ' + (colors[wxx] || 'var(--text)') + '20;">';
                    html += '<div style="color:' + (colors[wxx] || 'var(--text)') + ';font-weight:bold;font-size:0.85rem;margin-bottom:0.25rem;">' + wxx + '</div>';
                    html += '<div style="font-size:0.75rem;color:var(--text-muted);">' + (items.length > 0 ? items.join('、') : '缺') + '</div>';
                    html += '</div>';
                }
                html += '</div>';
            }

            // 五行性格描述
            if (s.desc) {
                html += '<p style="color:var(--text);font-size:0.85rem;margin:1rem 0 0.5rem;"><b>五行性格特质：</b></p>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">';
                for (var dxi2 = 0; dxi2 < wxOrder.length; dxi2++) {
                    var wxx2 = wxOrder[dxi2];
                    if (s.desc[wxx2] && s.scores[wxx2] > 0) {
                        html += '<div style="padding:0.5rem;background:' + (colors[wxx2] || 'var(--text)') + '08;border-radius:6px;border-left:3px solid ' + (colors[wxx2] || 'var(--text)') + '40;">';
                        html += '<div style="color:' + (colors[wxx2] || 'var(--text)') + ';font-weight:bold;font-size:0.8rem;">' + wxx2 + '</div>';
                        html += '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem;">' + s.desc[wxx2] + '</div>';
                        html += '</div>';
                    }
                }
                html += '</div>';
            }

            html += '</div></div>';
        }

        showResult('benming-result', html);
        trackAction('feature_use', 'benming_wuxing', { year: year, month: month, day: day, hour: hour });
    });
}

// ========== 八宅风水 ==========
function queryBaZhai(gua) {
    showLoading('fengshui-result');
    ajax('/api/fengshui/directions', { gua: gua }, function(json) {
        if (!json.success) { showResult('fengshui-result', '<div class="error">查询失败</div>'); return; }
        var d = json.data;
        var mingType = d.ming_type || '';
        var ji_xiong_map = {
            '吉': { color: '#81c784', cls: 'ji' },
            '凶': { color: '#e57373', cls: 'xiong' },
            '平': { color: '#d4a843', cls: 'ping' },
        };

        var html = '<div style="text-align:center;margin-bottom:1rem;">';
        html += '<h3 style="color:var(--gold);font-size:1.3rem;margin-bottom:0.5rem;">八宅风水分析</h3>';
        html += '<p style="color:var(--text-muted);font-size:0.9rem;">坐山：' + gua + ' · ' + mingType + '</p>';
        html += '</div>';

        // 八方位吉凶表
        html += '<h4 style="color:var(--gold);font-size:1rem;margin:1rem 0 0.5rem;">八方位吉凶</h4>';
        html += '<table class="data-table"><thead><tr>';
        html += '<th>方位</th><th>卦位</th><th>星曜</th><th>吉凶</th><th>九星</th><th>星宫生克</th>';
        html += '</tr></thead><tbody>';

        var dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北'];
        var dirGuas = { '北': '坎', '东北': '艮', '东': '震', '东南': '巽', '南': '离', '西南': '坤', '西': '兑', '西北': '乾' };

        dirs.forEach(function(dir) {
            var detail = d.directions_detail && d.directions_detail[dir];
            if (!detail) return;
            var star = detail.star;
            var jx = detail.ji_xiong;
            var color = ji_xiong_map[jx] ? ji_xiong_map[jx].color : '#6b7b8d';
            var jxCls = ji_xiong_map[jx] ? ji_xiong_map[jx].cls : '';
            var nineStar = detail.nine_star || '';
            var xg = detail.xing_gong_sheng_ke || {};
            var xgRel = xg.relation || xg.relationship || '';
            var xgJx = xg.ji_xiong || '平';
            var xgColor = xgJx === '吉' ? '#81c784' : (xgJx === '凶' ? '#e57373' : '#d4a843');

            html += '<tr>';
            html += '<td>' + trigramSymbol(dirGuas[dir]) + ' ' + dir + '</td>';
            html += '<td>' + (detail.palace_gua || '') + '</td>';
            html += '<td><span style="color:' + color + ';font-weight:bold;">' + star + '</span></td>';
            html += '<td><span class="badge badge-' + jxCls + '">' + jx + '</span></td>';
            html += '<td>' + nineStar + '</td>';
            html += '<td style="color:' + xgColor + ';font-size:0.8rem;">' + xgRel + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';

        // 九星祸福诀
        html += '<h4 style="color:var(--gold);font-size:1rem;margin:1.5rem 0 0.5rem;">九星祸福诀</h4>';
        var jiuXingHuoFuJue = d.jiu_xing_huo_fu_jue || {};
        var starOrder = ['生气', '天医', '延年', '伏位', '六煞', '五鬼', '绝命', '祸害'];
        starOrder.forEach(function(starName) {
            var hfj = jiuXingHuoFuJue[starName];
            if (!hfj) return;
            var info = BA_ZHAI_XING_INFO && BA_ZHAI_XING_INFO[starName];
            var nineStar = info ? (info['九星名'] || '') : '';
            var starWx = info ? (info['五行'] || '') : '';
            var jx = info ? (info['吉凶'] || '') : '';
            var jxColor = ji_xiong_map[jx] ? ji_xiong_map[jx].color : '#6b7b8d';

            html += '<div style="padding:0.5rem 0.75rem;margin:0.25rem 0;border-left:3px solid ' + jxColor + ';background:rgba(255,255,255,0.02);border-radius:4px;">';
            html += '<b style="color:' + jxColor + ';">' + starName + '</b>';
            if (nineStar) html += '（' + nineStar + '·' + starWx + '·' + jx + '）';
            html += '<br><span style="color:var(--text-muted);font-size:0.8rem;">' + (hfj.诀文 || '') + '</span><br>';
            html += '<span style="color:var(--text);font-size:0.8rem;">' + (hfj.白话 || '') + '</span>';
            html += '</div>';
        });

        // 方位化解建议
        html += '<h4 style="color:var(--gold);font-size:1rem;margin:1.5rem 0 0.5rem;">方位化解建议</h4>';

        if (d.ji_stars && d.ji_stars.length > 0) {
            html += '<h5 style="color:#81c784;font-size:0.95rem;margin:0.75rem 0 0.25rem;">✅ 吉星方位（宜布置）</h5>';
            d.ji_stars.forEach(function(s) {
                html += '<div style="padding:0.5rem 0.75rem;margin:0.25rem 0;background:rgba(129,199,132,0.05);border-radius:6px;">';
                html += '<b style="color:#81c784;">' + s.direction + '·' + s.star + '(' + s.nine_star + ')</b><br>';
                html += '<span style="color:var(--text-muted);font-size:0.8rem;">宜：' + (s.info['宜'] || '') + '</span><br>';
                html += '<span style="color:var(--text);font-size:0.8rem;">' + (s.info['化解建议'] || '') + '</span>';
                html += '</div>';
            });
        }

        if (d.xiong_stars && d.xiong_stars.length > 0) {
            html += '<h5 style="color:#e57373;font-size:0.95rem;margin:0.75rem 0 0.25rem;">⚠️ 凶星方位（宜化解）</h5>';
            d.xiong_stars.forEach(function(s) {
                html += '<div style="padding:0.5rem 0.75rem;margin:0.25rem 0;background:rgba(229,115,115,0.05);border-radius:6px;">';
                html += '<b style="color:#e57373;">' + s.direction + '·' + s.star + '(' + s.nine_star + ')</b><br>';
                html += '<span style="color:var(--text-muted);font-size:0.8rem;">宜：' + (s.info['宜'] || '') + '</span><br>';
                html += '<span style="color:var(--text);font-size:0.8rem;">' + (s.info['化解建议'] || '') + '</span>';
                html += '</div>';
            });
        }

        if (d.ping_stars && d.ping_stars.length > 0) {
            html += '<h5 style="color:#d4a843;font-size:0.95rem;margin:0.75rem 0 0.25rem;">➖ 平星方位（宜守成）</h5>';
            d.ping_stars.forEach(function(s) {
                html += '<div style="padding:0.5rem 0.75rem;margin:0.25rem 0;background:rgba(212,168,67,0.05);border-radius:6px;">';
                html += '<b style="color:#d4a843;">' + s.direction + '·' + s.star + '(' + s.nine_star + ')</b><br>';
                html += '<span style="color:var(--text);font-size:0.8rem;">' + (s.info['化解建议'] || '') + '</span>';
                html += '</div>';
            });
        }

        html += '<p style="color:var(--text-muted);font-size:0.8rem;margin-top:1rem;">⬇️ 下方：阳宅六要·门主灶分析、缺角凸角分析、综合分析</p>';

        showResult('fengshui-result', html);
        trackAction('feature_use', 'fengshui_bazhai', { gua: gua });
    });
}
var BA_ZHAI_XING_INFO = null;

// ========== 八卦详解 ==========
function queryBagua(gua) {
    showLoading('bagua-detail-result');
    ajax('/api/bagua/detail', { gua: gua }, function(json) {
        if (!json.success) { showResult('bagua-detail-result', '<div class="error">查询失败</div>'); return; }
        var d = json.data;
        var html = '<h3>' + gua + '卦详解</h3>';
        if (d.xiang) {
            html += '<div class="info-card-item"><h4>卦象</h4>';
            html += '<p><strong>卦名：</strong>' + (d.xiang.name || gua) + '</p>';
            html += '<p><strong>属性：</strong>' + (d.xiang.nature || '') + '</p>';
            html += '<p><strong>象征：</strong>' + (d.xiang.symbol || '') + '</p>';
            if (d.xiang.body) html += '<p><strong>身体：</strong>' + d.xiang.body + '</p>';
            if (d.xiang.family) html += '<p><strong>家庭：</strong>' + d.xiang.family + '</p>';
            if (d.xiang.direction) html += '<p><strong>方位：</strong>' + d.xiang.direction + '</p>';
            if (d.xiang.element) html += '<p><strong>五行：</strong>' + d.xiang.element + '</p>';
            html += '</div>';
        }
        if (d.lei_xiang) {
            html += '<div class="info-card-item"><h4>类象</h4>';
            for (var key in d.lei_xiang) {
                html += '<p><strong>' + key + '</strong>：' + d.lei_xiang[key] + '</p>';
            }
            html += '</div>';
        }
        showResult('bagua-detail-result', html);
        trackAction('feature_use', 'bagua_detail', { gua: gua });
    });
}
function query28Xiu() {
    var xiang = document.getElementById('xiu-xiang-filter').value;
    var jiux = document.getElementById('xiu-jiux-filter').value;
    showLoading('28xiu-result');
    ajax('/api/28xiu/calculate', { xiang_filter: xiang, jiux_filter: jiux }, function(json) {
        if (!json.success) { showResult('28xiu-result', '<div class="error">查询失败</div>'); return; }
        var list = json.data || [];
        var html = '';
        list.forEach(function(xi) {
            var jxClass = '';
            var jx = xi.ji_xiong || xi.jixiong || '';
            if (jx.indexOf('吉') >= 0 || jx.indexOf('祥') >= 0) jxClass = 'ji-xiong-ji';
            else if (jx.indexOf('凶') >= 0) jxClass = 'ji-xiong-xiong';
            else jxClass = 'ji-xiong-ping';
            html += '<div class="xiu-card">';
            html += '<h4>' + (xi.name || xi.xing_name || '') + '</h4>';
            html += '<p><strong>四相：</strong>' + (xi.xiang || xi.si_xiang || '') + ' | <strong>九星：</strong>' + (xi.jiux || xi.jiu_xing || '') + '</p>';
            html += '<p><strong>吉凶：</strong><span class="' + jxClass + '">' + (xi.ji_xiong || xi.jixiong || xi.jixiong2 || '') + '</span></p>';
            if (xi.desc) html += '<p>' + xi.desc + '</p>';
            if (xi.good) html += '<p><strong>宜：</strong>' + xi.good + '</p>';
            if (xi.bad) html += '<p><strong>忌：</strong>' + xi.bad + '</p>';
            html += '</div>';
        });
        showResult('28xiu-result', html || '<p>无匹配数据</p>');
        trackAction('feature_use', '28_xiu', { xiang: xiang, jiux: jiux });
    });
}
// ========== 纳甲 ==========
var najiaData = null;
function loadNajiaData() {
    if (najiaData) { renderNajia(najiaData); return; }
    showLoading('najia-content');
    ajax('/api/najia/list', {}, function(json) {
        if (!json.success) { showResult('najia-content', '<div class="error">加载失败</div>'); return; }
        najiaData = json.data;
        renderNajia(json.data);
        trackAction('feature_use', 'najia');
    });
}

function renderNajia(data) {
    var html = '';
    if (data.najia) {
        // 添加卦名选择器
        html += '<div style="margin-bottom:1rem;">';
        html += '<label style="color:var(--text-muted);font-size:0.85rem;margin-right:0.5rem;">选择卦名：</label>';
        html += '<select id="najia-gua-select" onchange="renderNajiaGua(this.value)" style="padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);">';
        var guaNames = Object.keys(data.najia);
        for (var g = 0; g < guaNames.length; g++) {
            html += '<option value="' + guaNames[g] + '">' + guaNames[g] + '</option>';
        }
        html += '</select></div>';

        // 初始显示乾卦
        renderNajiaGua(guaNames[0] || '');
    }
    if (data.nayin_list && data.nayin_list.length > 0) {
        html += '<h4 style="margin-top:2rem;">纳音列表（前20条）</h4><table class="data-table"><thead><tr>';
        html += '<th>干支1</th><th>干支2</th><th>纳音</th><th>五行</th></tr></thead><tbody>';
        for (var i = 0; i < Math.min(data.nayin_list.length, 60); i++) {
            var item = data.nayin_list[i];
            html += '<tr><td>' + (item[0]||'') + '</td><td>' + (item[1]||'') + '</td><td>' + (item[2]||'') + '</td><td>' + (item[3]||'') + '</td></tr>';
        }
        html += '</tbody></table>';
    }
    showResult('najia-content', html);
}

function renderNajiaGua(gua) {
    if (!gua || !najiaData || !najiaData.najia[gua]) return;
    var g = najiaData.najia[gua];
    var triSym = trigramSymbol(gua);
    var triInfo = g.trigram_info || {};

    var html = '<div style="text-align:center;margin-bottom:1rem;">';
    html += '<h3 style="color:var(--gold);font-size:1.3rem;">' + triSym + ' ' + gua + ' 纳甲</h3>';
    html += '<p style="color:var(--text-muted);font-size:0.85rem;">';
    html += '五行：' + (triInfo.element || '') + ' · ';
    html += '自然：' + (triInfo.nature || '') + ' · ';
    html += '家族：' + (triInfo.family || '') + '</p>';
    html += '</div>';

    var naJia = g.na_jia || '';
    html += '<p><b style="color:var(--gold);">纳甲：</b>' + naJia + '</p>';

    // 六亲颜色
    var lqColors = {
        '父母': '#4fc3f7', '兄弟': '#fff176', '子孙': '#81c784',
        '妻财': '#ffb74d', '官鬼': '#e57373',
    };

    // 六爻纳支表
    html += '<table class="data-table"><thead><tr>';
    html += '<th>爻位</th><th>纳支</th><th>五行</th><th>六亲</th>';
    html += '</tr></thead><tbody>';

    var yaoDetails = g.yao_details || [];
    yaoDetails.forEach(function(yd) {
        var wxColor = colorWuxing(yd.zhi_wuxing);
        var lqColor = lqColors[yd.liu_qin] || 'var(--text)';
        html += '<tr>';
        html += '<td style="color:var(--gold);">' + yd.yao + '</td>';
        html += '<td style="color:' + wxColor + ';">' + yd.zhi + '</td>';
        html += '<td style="color:' + wxColor + ';">' + yd.zhi_wuxing + '</td>';
        html += '<td style="color:' + lqColor + ';font-weight:bold;">' + yd.liu_qin + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';

    // 六亲说明
    html += '<h4 style="color:var(--gold);font-size:0.95rem;margin:1rem 0 0.5rem;">📖 六亲含义</h4>';
    html += '<p style="color:var(--text);font-size:0.85rem;line-height:1.8;">';
    html += '<span style="color:#4fc3f7;">父母</span>（生我者） · ';
    html += '<span style="color:#fff176;">兄弟</span>（同我者） · ';
    html += '<span style="color:#81c784;">子孙</span>（我生者） · ';
    html += '<span style="color:#ffb74d;">妻财</span>（我克者） · ';
    html += '<span style="color:#e57373;">官鬼</span>（克我者）</p>';
}


// ========== 阳宅六要·门主灶分析 ==========
function doMzAnalysis() {
    var gua = document.querySelector('.gua-btn.active') || document.querySelector('.gua-btn');
    var guaName = '';
    // 从当前激活的卦按钮获取卦名
    var activeBtn = document.querySelector('#fengshui-gua-select .gua-btn.active');
    if (!activeBtn) {
        // 如果没有激活的，使用第一个
        var allBtns = document.querySelectorAll('#fengshui-gua-select .gua-btn');
        if (allBtns.length > 0) {
            // 从按钮文本提取卦名
            var text = allBtns[0].textContent.trim();
            var match = text.match(/([乾坤震巽坎离艮兑])宅/);
            guaName = match ? match[1] : '乾';
        }
    } else {
        var text = activeBtn.textContent.trim();
        var match = text.match(/([乾坤震巽坎离艮兑])宅/);
        guaName = match ? match[1] : '乾';
    }

    var doorDir = document.getElementById('fs-door-dir').value;
    var mainDir = document.getElementById('fs-main-dir').value;
    var kitchenDir = document.getElementById('fs-kitchen-dir').value;
    var livingDir = document.getElementById('fs-living-dir').value;
    var studyDir = document.getElementById('fs-study-dir').value;
    var toiletDir = document.getElementById('fs-toilet-dir').value;

    showLoading('mz-analysis-result');
    ajax('/api/fengshui/mz_analysis', {
        door_dir: doorDir,
        main_dir: mainDir,
        kitchen_dir: kitchenDir,
        living_dir: livingDir,
        study_dir: studyDir,
        toilet_dir: toiletDir,
        gua: guaName,
    }, function(json) {
        if (!json.success) { showResult('mz-analysis-result', '<div class="error">分析失败</div>'); return; }
        var d = json.data;
        var comprehensive = d.comprehensive || {};
        var mzz = d.men_zhu_zao || {};

        var jxColors = {'大吉': '#81c784', '吉': '#81c784', '平': '#d4a843',
                        '次凶': '#ffb74d', '凶': '#e57373', '小凶': '#ffb74d', '大凶': '#e57373'};

        var zong = comprehensive.总评 || {};
        var zongColor = jxColors[zong.吉凶] || 'var(--text)';

        var html = '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:1rem;margin-top:0.5rem;">';
        html += '<h4 style="color:var(--gold);font-size:1rem;margin-bottom:0.75rem;">🏠 阳宅六要综合风水测算 · ' + guaName + '宅</h4>';
        html += '<p style="color:' + zongColor + ';font-size:0.95rem;font-weight:bold;margin:0.25rem 0;">📊 ' + (zong.标题 || '') + ' — ' + (zong.吉凶 || '') + '</p>';
        html += '<p style="color:var(--text);font-size:0.8rem;margin:0.25rem 0;line-height:1.6;">' + (zong.总结 || '') + '</p>';

        // 分项运势
        html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">📈 分项运势</h5>';
        html += '<table class="data-table" style="font-size:0.8rem;"><thead><tr>';
        html += '<th>项目</th><th>吉凶</th><th>详解</th></tr></thead><tbody>';

        var items = [
            {key: '财运', icon: '💰'},
            {key: '健康', icon: '🏥'},
            {key: '事业学业', icon: '💼'},
            {key: '家庭关系', icon: '👨‍👩‍👧‍👦'},
        ];

        items.forEach(function(item) {
            var data = comprehensive[item.key] || {};
            var jx = data.吉凶 || '平';
            var color = jxColors[jx] || 'var(--text)';
            html += '<tr>';
            html += '<td style="color:var(--gold);font-weight:bold;">' + item.icon + ' ' + item.key + '</td>';
            html += '<td style="color:' + color + ';font-weight:bold;">' + (data.标题 || jx) + '</td>';
            html += '<td style="color:var(--text);font-size:0.75rem;">' + (data.详解 || '') + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';

        // 阳宅六要详情
        html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">🔍 阳宅六要详情</h5>';
        html += '<table class="data-table" style="font-size:0.8rem;"><thead><tr>';
        html += '<th>项目</th><th>关系</th><th>详解</th></tr></thead><tbody>';

        var mzItems = [
            {key: '门主', data: mzz.门主},
            {key: '门灶', data: mzz.门灶},
            {key: '主灶', data: mzz.主灶},
        ];

        mzItems.forEach(function(item) {
            var data = item.data || {};
            var jx = data.吉凶 || '平';
            var color = jxColors[jx] || 'var(--text)';
            html += '<tr>';
            html += '<td style="color:var(--gold);font-weight:bold;">' + item.key + '</td>';
            html += '<td style="color:' + color + ';font-weight:bold;">' + (data.关系 || jx) + '</td>';
            html += '<td style="color:var(--text);font-size:0.75rem;">' + (data.详解 || '') + '</td>';
            html += '</tr>';
        });

        // 客厅、书房、厕所
        ['客厅', '书房', '厕所'].forEach(function(room) {
            var data = comprehensive[room] || {};
            var jx = data.吉凶 || '平';
            var color = jxColors[jx] || 'var(--text)';
            html += '<tr>';
            html += '<td style="color:var(--gold);font-weight:bold;">' + room + '</td>';
            html += '<td style="color:' + color + ';font-weight:bold;">' + jx + ' · ' + (data.九星 || '') + '</td>';
            html += '<td style="color:var(--text);font-size:0.75rem;">' + (data.原理 || '') + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';

        // 关键问题
        if (comprehensive.关键问题 && comprehensive.关键问题.length > 0) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">⚠️ 关键问题</h5>';
            comprehensive.关键问题.forEach(function(prob) {
                var probColor = prob.indexOf('✅') >= 0 ? '#81c784' : '#e57373';
                html += '<p style="padding:0.4rem 0.75rem;margin:0.25rem 0;background:rgba(255,255,255,0.02);border-radius:4px;border-left:3px solid ' + probColor + ';color:var(--text);font-size:0.8rem;">' + prob + '</p>';
            });
        }

        // 化解建议
        if (comprehensive.化解建议 && comprehensive.化解建议.length > 0) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">💡 化解建议</h5>';
            comprehensive.化解建议.forEach(function(sol) {
                html += '<p style="padding:0.4rem 0.75rem;margin:0.25rem 0;background:rgba(212,168,67,0.05);border-radius:4px;border-left:3px solid var(--gold);color:var(--text);font-size:0.8rem;">' + sol + '</p>';
            });
        }

        html += '</div>';
        showResult('mz-analysis-result', html);
        trackAction('feature_use', 'fengshui_mz_analysis', { gua: guaName });
    });
}
function doQueJiangAnalysis() {
    var area = document.getElementById('qj-area').value;
    var isQue = document.getElementById('qj-type').value === 'true';

    showLoading('que-jiang-result');
    ajax('/api/fengshui/que_jiang', { area: area, is_que_jiang: isQue }, function(json) {
        if (!json.success) { showResult('que-jiang-result', '<div class="error">分析失败</div>'); return; }
        var d = json.data;

        var typeLabel = isQue ? '缺角' : '凸角';
        var html = '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:1rem;margin-top:0.5rem;">';
        html += '<h4 style="color:var(--gold);font-size:1rem;margin-bottom:0.75rem;">🏠 ' + area + '方位' + typeLabel + '分析</h4>';

        if (d.影响) {
            html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;"><b style="color:var(--gold);">影响：</b>' + d.影响 + '</p>';
        }
        if (d.化解) {
            html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;"><b style="color:var(--gold);">化解：</b>' + d.化解 + '</p>';
        }
        if (d.详细说明) {
            html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;line-height:1.6;">' + d.详细说明 + '</p>';
        }
        if (d.相关卦象) {
            html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;"><b style="color:var(--gold);">相关卦象：</b>' + d.相关卦象 + '</p>';
        }

        html += '</div>';
        showResult('que-jiang-result', html);
        trackAction('feature_use', 'fengshui_que_jiang', { area: area, is_que_jiang: isQue });
    });
}


// ========== 综合分析 ==========
function doComprehensiveAnalysis() {
    // 获取当前选中的卦
    var activeBtn = document.querySelector('#fengshui-gua-select .gua-btn.active');
    var guaName = '';
    if (activeBtn) {
        var text = activeBtn.textContent.trim();
        var match = text.match(/([乾坤震巽坎离艮兑])宅/);
        guaName = match ? match[1] : '乾';
    }

    var shengxiao = document.getElementById('zong-shengxiao').value;
    var year = parseInt(document.getElementById('zong-year').value) || 1990;

    // 读取缺角凸角面板（与程序版一致）
    var qjArea = document.getElementById('qj-area')?.value || '';
    var qjType = document.getElementById('qj-type')?.value || 'true';
    var houseShape = '';
    if (qjArea) {
        houseShape = (qjType === 'true' ? '缺' : '凸') + qjArea;
    }

    showLoading('zong-result');
    ajax('/api/fengshui/comprehensive_bazhai', {
        house_gua: guaName,
        door_dir: document.getElementById('fs-door-dir').value,
        main_dir: document.getElementById('fs-main-dir').value,
        kitchen_dir: document.getElementById('fs-kitchen-dir').value,
        living_dir: document.getElementById('fs-living-dir').value,
        study_dir: document.getElementById('fs-study-dir').value,
        toilet_dir: document.getElementById('fs-toilet-dir').value,
        resident_shengxiao: shengxiao,
        resident_year: year,
        house_shape: houseShape,
    }, function(json) {
        if (!json.success) { showResult('zong-result', '<div class="error">分析失败</div>'); return; }
        var d = json.data;

        var html = '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:1rem;margin-top:0.5rem;">';
        html += '<h4 style="color:var(--gold);font-size:1rem;margin-bottom:0.75rem;">🔮 八宅·九宫·命理 综合分析</h4>';

        // 总评（综合评分在 总评.综合评分）
        var zp = d.总评 || {};
        var score = zp.综合评分 || 0;
        var jxColor = 'var(--gold)';
        if (typeof score === 'number') {
            if (score >= 7) jxColor = '#81c784';
            else if (score >= 4) jxColor = '#d4a843';
            else jxColor = '#e57373';
        }
        html += '<p style="color:' + jxColor + ';font-size:1.2rem;font-weight:bold;margin:0.25rem 0;">综合评分：' + score + ' / 10</p>';
        if (zp.标题) html += '<p style="color:var(--gold);font-size:0.95rem;margin:0.25rem 0;">📊 ' + zp.标题 + '</p>';
        if (zp.总结) html += '<p style="color:var(--text);font-size:0.85rem;margin:0.25rem 0;line-height:1.6;">' + zp.总结 + '</p>';

        // 房屋信息
        if (d.房屋信息) {
            var fi = d.房屋信息;
            html += '<p style="color:var(--text-muted);font-size:0.8rem;margin:0.5rem 0;">坐山：' + (fi['坐山卦'] || '') + ' · ' + (fi['东西宫'] || '') + '宅</p>';
            html += '<p style="color:var(--text-muted);font-size:0.8rem;margin:0.15rem 0;">大门：' + (fi['大门方位'] || '') + ' · 主卧：' + (fi['主卧方位'] || '') + ' · 厨房：' + (fi['厨房方位'] || '') + '</p>';
        }

        // 居住人分析
        if (d.居住人分析) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">👤 居住人命理</h5>';
            var mr = d.居住人分析;
            if (mr.生肖) html += '<p style="color:var(--text);font-size:0.8rem;margin:0.15rem 0;">生肖：' + mr.生肖 + ' · 出生年：' + mr['出生年'] + '</p>';
            if (mr.命卦) html += '<p style="color:var(--text);font-size:0.8rem;margin:0.15rem 0;">命卦：' + mr.命卦 + ' · 本命五行：' + (mr['本命五行'] || '') + '</p>';

            // 吉凶方位
            if (mr.吉凶方位) {
                html += '<h6 style="color:var(--gold);font-size:0.8rem;margin:0.5rem 0 0.25rem;">吉凶方位</h6>';
                for (var starName in mr.吉凶方位) {
                    var dir = mr.吉凶方位[starName];
                    html += '<span style="color:#81c784;font-size:0.75rem;margin-right:0.75rem;">' + starName + '：' + dir + '</span>';
                }
                html += '<br>';
            }
            // 冲克方位
            if (mr.冲克方位) {
                html += '<h6 style="color:var(--gold);font-size:0.8rem;margin:0.5rem 0 0.25rem;">冲克方位</h6>';
                for (var ck in mr.冲克方位) {
                    html += '<span style="color:#e57373;font-size:0.75rem;margin-right:0.75rem;">' + ck + '：' + mr.冲克方位[ck] + '</span>';
                }
                html += '<br>';
            }
        }

        // 九宫方位分析
        if (d.九宫方位分析) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">🧭 九宫方位</h5>';
            var jg = d.九宫方位分析;
            var dirs = ['西北', '正北', '东北', '正东', '东南', '正南', '西南', '正西'];
            dirs.forEach(function(dir) {
                var info = jg[dir];
                if (!info) return;
                var star = info.八宅星曜 || info.洛书九宫?.白星 || '';
                var jx2 = info.吉凶 || '';
                var use = info.实际用途 || '';
                var dcolor = jx2 === '吉' || jx2 === '大吉' ? '#81c784' : (jx2 === '凶' || jx2 === '大凶' ? '#e57373' : 'var(--text-muted)');
                html += '<span style="color:' + dcolor + ';font-size:0.75rem;margin-right:0.75rem;">' + dir + '：' + (star || '平') + '</span>';
                if (use && use !== '空闲/通道') {
                    html += '<span style="color:var(--text-muted);font-size:0.7rem;">(' + use + ')</span>';
                }
                html += ' · ';
            });
            html += '<br>';
        }

        // 五行平衡
        if (d.五行平衡) {
            var wb = d.五行平衡;
            if (wb.缺失五行 && wb.缺失五行.length > 0) {
                html += '<p style="color:#e57373;font-size:0.8rem;margin:0.25rem 0;">缺：' + wb.缺失五行.join('、') + '</p>';
            }
            if (wb.过强五行 && wb.过强五行.length > 0) {
                html += '<p style="color:#d4a843;font-size:0.8rem;margin:0.25rem 0;">旺：' + wb.过强五行.join('、') + '</p>';
            }
        }

        // 评分明细
        if (d.评分明细) {
            var sm = d.评分明细;
            html += '<p style="color:var(--text-muted);font-size:0.75rem;margin:0.5rem 0 0.25rem;">门主：' + (sm['门主'] || 0) + ' · 九宫：' + (sm['九宫'] || 0) + ' · 命理：' + (sm['命理'] || 0) + '</p>';
        }

        // 问题诊断
        if (d.问题诊断 && d.问题诊断.length > 0) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">⚠️ 问题诊断</h5>';
            d.问题诊断.forEach(function(prob) {
                var probText = '';
                if (prob.类型 && prob.类型 !== '无') probText += '<strong style="color:#e57373;font-size:0.75rem;">[' + prob.类型 + ']</strong> ';
                probText += prob.问题 || '';
                if (prob.影响) probText += '<br><span style="color:var(--text-muted);font-size:0.75rem;">影响：' + prob.影响 + '</span>';
                html += '<div style="margin:0.4rem 0;padding:0.5rem 0.75rem;background:rgba(229,115,115,0.06);border-radius:6px;border-left:3px solid #e57373;">' + probText + '</div>';
            });
        }

        // 化解建议
        if (d.化解建议 && d.化解建议.length > 0) {
            html += '<h5 style="color:var(--gold);font-size:0.85rem;margin:0.75rem 0 0.5rem;">💡 化解建议</h5>';
            d.化解建议.forEach(function(sol) {
                html += '<p style="color:var(--text);font-size:0.8rem;margin:0.15rem 0;padding:0.25rem 0.5rem;background:rgba(212,168,67,0.05);border-radius:4px;border-left:3px solid var(--gold);">' + sol + '</p>';
            });
        }

        html += '</div>';
        showResult('zong-result', html);
        trackAction('feature_use', 'fengshui_comprehensive', { gua: guaName });
    });
}

// ========== 函数别名（匹配 HTML onclick） ==========
var tossCoin = doCoinToss;
var doYarrow = doYarrowToss;

// ========== 移动端菜单切换 ==========
function toggleMobileMenu() {
    var nav = document.getElementById('navbar-nav');
    if (nav) nav.classList.toggle('open');
}

// ========== 导航栏滚动效果 ==========
(function() {
    var navbar = document.getElementById('navbar');
    if (!navbar) return;
    window.addEventListener('scroll', function() {
        if (window.scrollY > 10) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
})();

// ========== 八卦详解 ==========
function queryBaguaDetail(gua) {
    showLoading('bagua-detail-result');
    ajax('/api/bagua/detail', { gua: gua }, function(json) {
        if (!json.success) { showResult('bagua-detail-result', '<div class="error">查询失败</div>'); return; }
        var d = json.data;
        var triSym = trigramSymbol(gua);
        var xiang = d.xiang || {};
        var leiXiang = d.lei_xiang || {};

        var html = '<div class="hex-display">';
        html += '<div class="hex-symbol">' + triSym + '</div>';
        html += '<div class="hex-name">' + gua + '</div>';

        // 基本属性
        var attrs = [];
        if (xiang.element) attrs.push('五行：' + xiang.element);
        if (xiang.nature) attrs.push('自然：' + xiang.nature);
        if (xiang.family) attrs.push('家族：' + xiang.family);
        if (attrs.length) html += '<div class="hex-detail">' + attrs.join(' · ') + '</div>';

        // 卦辞
        if (xiang.gua_ci) {
            html += '<div class="hex-judgment"><h4 style="color:var(--primary);font-size:0.9rem;margin-bottom:0.35rem;">卦辞</h4>';
            html += '<p style="color:var(--text);font-size:0.85rem;line-height:1.7;">' + xiang.gua_ci + '</p></div>';
        }

        // 类象
        var keys = Object.keys(leiXiang);
        if (keys.length > 0) {
            html += '<h4 style="color:var(--primary);font-size:0.9rem;margin:1rem 0 0.5rem;">类象</h4>';
            html += '<div class="info-grid">';
            keys.forEach(function(k) {
                var v = leiXiang[k];
                if (v) {
                    html += '<div class="info-card-item"><h4>' + k + '</h4><p>' + v + '</p></div>';
                }
            });
            html += '</div>';
        }

        html += '</div>';
        showResult('bagua-detail-result', html);
    });
}

// ========== 主页特效 ==========

(function() {
    // --- 粒子背景 ---
    var particles = document.getElementById('hero-particles');
    if (!particles) return;
    var yiJingChars = ['☰', '☱', '☲', '☳', '☴', '☵', '☶', '☷', '☯', '⚊', '⚋', '乾', '坤', '震', '巽', '坎', '离', '艮', '兑'];

    function spawnParticle() {
        var el = document.createElement('span');
        el.className = 'particle';
        el.textContent = yiJingChars[Math.floor(Math.random() * yiJingChars.length)];
        el.style.left = Math.random() * 100 + '%';
        el.style.bottom = '-20px';
        el.style.fontSize = (0.8 + Math.random() * 1.2) + 'rem';
        el.style.animationDuration = (12 + Math.random() * 18) + 's';
        el.style.animationDelay = '0s';
        particles.appendChild(el);
        setTimeout(function() {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 30000);
    }

    // 初始生成一批粒子
    for (var i = 0; i < 15; i++) {
        setTimeout(spawnParticle, i * 400);
    }
    // 持续生成
    setInterval(spawnParticle, 2000);

    // --- 鼠标跟随光效 ---
    var glow = document.getElementById('hero-glow');
    var heroSplit = document.querySelector('.hero-split');
    if (glow && heroSplit) {
        heroSplit.addEventListener('mousemove', function(e) {
            var rect = heroSplit.getBoundingClientRect();
            glow.style.left = (e.clientX - rect.left) + 'px';
            glow.style.top = (e.clientY - rect.top) + 'px';
        });
        heroSplit.addEventListener('mouseleave', function() {
            glow.style.opacity = '0';
        });
        heroSplit.addEventListener('mouseenter', function() {
            glow.style.opacity = '1';
        });
    }

    // --- CTA 按钮波纹 ---
    window.createRipple = function(event) {
        var btn = event.currentTarget;
        var circle = document.createElement('span');
        var diameter = Math.max(btn.clientWidth, btn.clientHeight);
        var radius = diameter / 2;
        var rect = btn.getBoundingClientRect();
        circle.style.width = circle.style.height = diameter + 'px';
        circle.style.left = (event.clientX - rect.left - radius) + 'px';
        circle.style.top = (event.clientY - rect.top - radius) + 'px';
        circle.className = 'ripple';
        var existingRipple = btn.querySelector('.ripple');
        if (existingRipple) existingRipple.remove();
        btn.appendChild(circle);
        setTimeout(function() { if (circle.parentNode) circle.parentNode.removeChild(circle); }, 600);
    };

    // --- 打字机效果 ---
    var typingEl = document.getElementById('hero-typing');
    if (typingEl) {
        var typingText = '铜钱起卦 · 蓍草演算 · 八宅风水 · 五行生克 · 纳甲六亲';
        var typingIndex = 0;
        function typeWriter() {
            if (typingIndex < typingText.length) {
                typingEl.textContent = typingText.substring(0, typingIndex + 1);
                typingEl.style.borderRight = '2px solid var(--accent)';
                typingIndex++;
                setTimeout(typeWriter, 80 + Math.random() * 40);
            } else {
                // 打字完成后保留闪烁光标
                typingEl.style.borderRight = '2px solid var(--accent)';
                // 2秒后隐藏光标
                setTimeout(function() {
                    typingEl.style.borderRight = 'none';
                }, 2000);
            }
        }
        // 延迟启动
        setTimeout(typeWriter, 600);
    }

    // --- 滚动渐入动画 ---
    var scrollRevealElements = document.querySelectorAll('.scroll-reveal');
    if (scrollRevealElements.length > 0) {
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: '0px 0px -50px 0px'
        });
        scrollRevealElements.forEach(function(el) {
            observer.observe(el);
        });
    }
})();

// ============================================
// 用户认证
// ============================================

var _authChecked = false;

/** 检查登录状态（页面加载时调用一次） */
function checkAuthStatus(force) {
    if (_authChecked && !force) return;
    _authChecked = true;
    console.log('[auth] checkAuthStatus called, force=' + (force || false));
    ajax('/api/auth/session', {}, function(json) {
        console.log('[auth] session response:', json);
        if (json.success) {
            updateNavbarForAuth(json.logged_in, json.user || null);
        }
    });
}

/** 根据认证状态更新导航栏 */
function updateNavbarForAuth(loggedIn, user) {
    console.log('[auth] updateNavbarForAuth: loggedIn=' + loggedIn, 'user=' + JSON.stringify(user || null).substring(0,100));
    var authDiv = document.getElementById('navbar-auth');
    var userDiv = document.getElementById('user-dropdown');
    var logoutBtn = document.getElementById('navbar-logout-btn');
    if (!authDiv || !userDiv) { console.log('[auth] missing elements'); return; }

    if (loggedIn && user) {
        var profile = user.profile || {};
        var nickname = profile.nickname || user.user?.username || '用户';
        var email = user.user?.email || '';

        // 更新下拉菜单
        var avatarCircle = document.getElementById('user-avatar-circle');
        var displayName = document.getElementById('user-display-name');
        var dropUsername = document.getElementById('dropdown-username');
        var dropEmail = document.getElementById('dropdown-email');

        if (avatarCircle) avatarCircle.textContent = (nickname.charAt(0));
        if (displayName) displayName.textContent = nickname;
        if (dropUsername) dropUsername.textContent = nickname;
        if (dropEmail) dropEmail.textContent = email || '';

        // 显示用户菜单，隐藏登录注册按钮
        authDiv.style.display = 'none';
        userDiv.style.display = 'block';

        // 显示登出按钮
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
    } else {
        authDiv.style.display = 'flex';
        userDiv.style.display = 'none';

        // 隐藏登出按钮
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

/** 关闭用户下拉菜单 */
function closeUserDropdown() {
    var dd = document.getElementById('user-dropdown');
    if (dd) dd.classList.remove('open');
}

/** 切换用户下拉菜单 */
function toggleUserDropdown() {
    var dd = document.getElementById('user-dropdown');
    if (dd) dd.classList.toggle('open');
}

// 点击页面其他地方关闭下拉菜单
document.addEventListener('click', function(e) {
    var dd = document.getElementById('user-dropdown');
    if (dd && dd.classList.contains('open') && !dd.contains(e.target)) {
        closeUserDropdown();
    }
});

/** 显示登录模态框（clearPending: 是否清除暂存页面，默认清除）*/
function showLoginModal(clearPending) {
    if (clearPending === undefined || clearPending) _pendingPage = null;
    var modal = document.getElementById('auth-modal');
    var loginSection = document.getElementById('login-form-section');
    var regSection = document.getElementById('register-form-section');
    if (loginSection) loginSection.classList.remove('hidden');
    if (regSection) regSection.classList.add('hidden');
    if (modal) modal.classList.add('active');
    clearAuthError('login');
    var usernameInput = document.getElementById('login-username');
    if (usernameInput) setTimeout(function() { usernameInput.focus(); }, 100);
}

/** 显示注册模态框 */
function showRegisterModal() {
    var modal = document.getElementById('auth-modal');
    var loginSection = document.getElementById('login-form-section');
    var regSection = document.getElementById('register-form-section');
    if (loginSection) loginSection.classList.add('hidden');
    if (regSection) regSection.classList.remove('hidden');
    if (modal) modal.classList.add('active');
    clearAuthError('reg');
    var usernameInput = document.getElementById('reg-username');
    if (usernameInput) setTimeout(function() { usernameInput.focus(); }, 100);
}

/** 关闭模态框 */
function hideAuthModal() {
    var modal = document.getElementById('auth-modal');
    if (modal) modal.classList.remove('active');
}

/** 清除错误提示 */
function clearAuthError(prefix) {
    var errorEl = document.getElementById(prefix + '-error');
    if (errorEl) errorEl.textContent = '';
}

/** 显示错误提示 */
function showAuthError(prefix, msg) {
    var errorEl = document.getElementById(prefix + '-error');
    if (errorEl) errorEl.textContent = msg;
}

/** 登录表单提交 */
function doLogin(e) {
    if (e) e.preventDefault();
    console.log('[doLogin] form submitted');
    var username = document.getElementById('login-username').value.trim();
    var password = document.getElementById('login-password').value;
    console.log('[doLogin] username=', username, 'password_len=', password ? password.length : 0);
    if (!username || !password) {
        showAuthError('login', '请输入用户名和密码');
        return;
    }
    var btn = e && e.target ? e.target.querySelector('button[type="submit"]') : null;
    console.log('[doLogin] btn=', btn);
    if (btn) btn.disabled = true;
    ajax('/api/auth/login', { username: username, password: password }, function(json) {
        console.log('[doLogin] response:', json);
        if (btn) btn.disabled = false;
        if (json.success) {
            hideAuthModal();
            checkAuthStatus(true);
            _navigatePendingPage();
        } else {
            showAuthError('login', json.error || '登录失败');
        }
    });
}

/** 注册表单提交 */
function doRegister(e) {
    if (e) e.preventDefault();
    var username = document.getElementById('reg-username').value.trim();
    var email = document.getElementById('reg-email').value.trim() || null;
    var password = document.getElementById('reg-password').value;
    var password2 = document.getElementById('reg-password2').value;

    if (!username || username.length < 2) {
        showAuthError('reg', '用户名至少2个字符');
        return;
    }
    if (!password || password.length < 4) {
        showAuthError('reg', '密码至少4个字符');
        return;
    }
    if (password !== password2) {
        showAuthError('reg', '两次输入的密码不一致');
        return;
    }

    var btn = e && e.target ? e.target.querySelector('button[type="submit"]') : null;
    if (btn) btn.disabled = true;
    ajax('/api/auth/register', { username: username, password: password, email: email }, function(json) {
        if (btn) btn.disabled = false;
        if (json.success) {
            hideAuthModal();
            checkAuthStatus(true);
            _navigatePendingPage();
        } else {
            showAuthError('reg', json.error || '注册失败');
        }
    });
}

/** 登出 */
function doLogout() {
    closeUserDropdown();
    ajax('/api/auth/logout', {}, function(json) {
        if (json.success) {
            _authChecked = false;
            updateNavbarForAuth(false, null);
        }
    });
}

/** 启动时检查登录状态 */
(function() {
    checkAuthStatus();
    initTracking();
})();

// ============================================
// 用户个人中心
// ============================================

/** 加载用户资料到表单 */
function loadProfile() {
    console.log('[profile] loadProfile called');
    ajax('/api/user/profile', {}, function(json) {
        console.log('[profile] response:', json);
        if (!json.success || !json.data) {
            console.log('[profile] failed to load profile');
            return;
        }
        var data = json.data;
        var user = data.user || {};
        var profile = data.profile || {};

        // 基本信息
        setElValue('profile-username', user.username || '');
        setElValue('profile-email', user.email || '未设置');
        setElValue('profile-nickname', profile.nickname || '');
        setElValue('profile-phone', profile.phone || '');
        setElValue('profile-gender', profile.gender || '');
        setElValue('profile-created', user.created_at || '');

        // 出生信息
        setElValue('profile-birth-year', profile.birth_year || '');
        setElValue('profile-birth-month', profile.birth_month || '');
        setElValue('profile-birth-day', profile.birth_day || '');

        // 清除消息
        var msg = document.getElementById('profile-save-msg');
        if (msg) msg.textContent = '';
        var pwMsg = document.getElementById('change-pw-msg');
        if (pwMsg) pwMsg.textContent = '';
        if (pwMsg) pwMsg.style.color = '';
    });
}

/** 保存用户资料 */
function saveProfile() {
    var data = {
        nickname: document.getElementById('profile-nickname').value.trim(),
        phone: document.getElementById('profile-phone').value.trim(),
        gender: document.getElementById('profile-gender').value,
        birth_year: document.getElementById('profile-birth-year').value ? parseInt(document.getElementById('profile-birth-year').value) : null,
        birth_month: document.getElementById('profile-birth-month').value ? parseInt(document.getElementById('profile-birth-month').value) : null,
        birth_day: document.getElementById('profile-birth-day').value ? parseInt(document.getElementById('profile-birth-day').value) : null,
    };

    var msg = document.getElementById('profile-save-msg');
    msg.textContent = '保存中...';
    msg.style.color = 'var(--text-secondary)';

    ajax('/api/user/profile', data, function(json) {
        if (json.success) {
            msg.textContent = '✅ 保存成功';
            msg.style.color = 'var(--success)';
            trackAction('feature_use', 'profile_update', { fields: Object.keys(data).join(',') });
        } else {
            msg.textContent = '❌ ' + (json.error || '保存失败');
            msg.style.color = 'var(--error)';
        }
    });
}

/** 修改密码 */
function changePassword() {
    var oldPw = document.getElementById('change-old-pw').value;
    var newPw = document.getElementById('change-new-pw').value;
    var newPw2 = document.getElementById('change-new-pw2').value;
    var msg = document.getElementById('change-pw-msg');

    if (!oldPw || !newPw) {
        msg.textContent = '请填写原密码和新密码';
        msg.style.color = 'var(--error)';
        return;
    }
    if (newPw.length < 4) {
        msg.textContent = '新密码至少4个字符';
        msg.style.color = 'var(--error)';
        return;
    }
    if (newPw !== newPw2) {
        msg.textContent = '两次输入的新密码不一致';
        msg.style.color = 'var(--error)';
        return;
    }

    msg.textContent = '修改中...';
    msg.style.color = 'var(--text-secondary)';

    ajax('/api/user/change_password', {
        old_password: oldPw,
        new_password: newPw,
    }, function(json) {
        if (json.success) {
            msg.textContent = '✅ 密码修改成功';
            msg.style.color = 'var(--success)';
            document.getElementById('change-old-pw').value = '';
            document.getElementById('change-new-pw').value = '';
            document.getElementById('change-new-pw2').value = '';
            trackAction('feature_use', 'change_password', {});
        } else {
            msg.textContent = '❌ ' + (json.error || '修改失败');
            msg.style.color = 'var(--error)';
        }
    });
}

/** 设置元素值（兼容 input 和 select）*/
function setElValue(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value;
}
