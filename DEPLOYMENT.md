# 周易八卦网站 - 部署与凭证资料

> 最后更新：2026-11-13  
> 版本：1.5.3

---

## 一、网站信息

| 项目 | 值 |
|------|------|
| **网站地址** | https://yijing-web-ka1f.onrender.com |
| **管理后台** | https://yijing-web-ka1f.onrender.com/admin |
| **当前版本** | 1.5.3 |
| **部署平台** | Render (免费层) |
| **Render Service ID** | `srv-dbr8glei0phs73f4c9h0` |
| **Render API Key** | `rnd_2FKfIMUwQl7wTNAHjD3PPXbiwCbv` |
| **管理密码** | `Yijing2026!Secure` |

---

## 二、数据库（Supabase）

| 项目 | 值 |
|------|------|
| **平台** | Supabase (免费层) |
| **项目引用** | `qkxzmmqhewhpflgyuoud` |
| **数据库密码** | `nDT5oOmUMxulOlX8` |
| **Region** | us-east-1 (AWS) |
| **连接方式** | REST API（绕过 PostgreSQL 连接问题） |

### API Keys

| 类型 | 值 | 用途 |
|------|------|------|
| **Anon Key** | `sb_publishable_Nw9wEQiSRNahY7fKgoDgUA_9p7GvNh6` | 客户端 REST API 访问 |
| **Service Role** | (需在 Dashboard 获取) | 服务端管理操作 |

### REST API 端点

```
https://qkxzmmqhewhpflgyuoud.supabase.co/rest/v1
```

### 数据库表结构

| 表名 | 用途 |
|------|------|
| `users` | 用户认证（username, email, password_hash） |
| `user_profiles` | 用户个人资料（昵称、生日、性别等） |
| `fengshui_profiles` | 风水资料（户型、朝向等） |
| `user_actions` | 用户行为追踪（起卦、浏览、功能使用） |
| `hexagram_records` | 起卦记录（卦象、变卦、参数） |
| `fengshui_records` | 风水分析记录 |
| `user_favorites` | 收藏卦象 |

### 索引

- `idx_user_actions_user` - user_actions(user_id)
- `idx_user_actions_type` - user_actions(action_type)
- `idx_user_actions_feature` - user_actions(feature)
- `idx_user_actions_created` - user_actions(created_at)
- `idx_hex_records_user` - hexagram_records(user_id)
- `idx_hex_records_created` - hexagram_records(created_at)
- `idx_fs_records_user` - fengshui_records(user_id)
- `idx_fs_records_created` - fengshui_records(created_at)
- `idx_fav_user` - user_favorites(user_id)

---

## 三、环境变量（Render）

| 变量名 | 值 | 说明 |
|--------|------|------|
| `SUPABASE_PROJECT_REF` | `qkxzmmqhewhpflgyuoud` | Supabase 项目引用 |
| `SUPABASE_ANON_KEY` | `sb_publishable_Nw9wEQiSRNahY7fKgoDgUA_9p7GvNh6` | Supabase 匿名密钥 |
| `SUPABASE_DB_PASSWORD` | `nDT5oOmUMxulOlX8` | Supabase 数据库密码 |
| `SUPABASE_DB_HOST` | `db.qkxzmmqhewhpflgyuoud.supabase.co` | Supabase 直连端点 |
| `ADMIN_PASSWORD` | `Yijing2026!Secure` | 管理后台密码 |
| `PYTHON_VERSION` | `3.11.0` | Python 版本 |

---

## 四、GitHub 仓库

| 项目 | 值 |
|------|------|
| **仓库地址** | https://github.com/bing00428/yijing-web |
| **分支** | main |
| **部署触发** | push to main → Render 自动部署 |

---

## 五、关键技术决策

### 为什么使用 REST API 而非 PostgreSQL？

1. **IPv6 问题** - Supabase 直连端点 `db.<project>.supabase.co` 只有 IPv6，Render 免费层仅支持 IPv4
2. **Pooler 问题** - Supabase pooler 需要 SNI 或 external_id 识别租户，psycopg2 在 Render 上无法正确发送
3. **Cloudflare 问题** - `qkxzmmqhewhpflgyuoud.supabase.co:5432` 被 Cloudflare 代理拦截，TCP 5432 超时
4. **REST API 验证通过** - 确认可用，认证正常

### 过滤器语法

PostgREST 使用 `col=op.val` 格式，例如：
```
GET /rest/v1/users?username=eq.test_user
GET /rest/v1/user_actions?user_id=eq.1&order=created_at.desc
```

### 排序语法

PostgREST 使用 `order=col.desc` 或 `order=col.asc`：
```
GET /rest/v1/hexagram_records?user_id=eq.1&order=created_at.desc&limit=50
```

---

## 六、常用操作

### 部署

```bash
cd D:\AI_Projects\yijing-web
git add -A
git commit -m "feat: 描述"
git push origin main
```

### 查看部署状态

```bash
curl -H "Authorization: Bearer rnd_2FKfIMUwQl7wTNAHjD3PPXbiwCbv" \
  https://api.render.com/v1/services/srv-dbr8glei0phs73f4c9h0/deploys
```

### 数据库管理

1. 登录 https://supabase.com/dashboard
2. 项目：`qkxzmmqhewhpflgyuoud`
3. SQL Editor - 执行 SQL
4. Table Editor - 查看/编辑数据

### 管理后台

1. 访问 https://yijing-web-ka1f.onrender.com/admin
2. 输入密码：`Yijing2026!Secure`
3. 功能：总览、用户列表、用户详情、最近行为

---

## 七、文件清单

| 文件 | 用途 |
|------|------|
| `server.py` | Flask 后端主程序 |
| `models.py` | 数据库模型（REST API 封装） |
| `requirements.txt` | Python 依赖 |
| `render.yaml` | Render 部署配置 |
| `hexagram_data.py` | 六十四卦完整数据 |
| `hexagram_lines.py` | 六十四卦爻辞数据 |
| `templates/admin.html` | 管理后台页面 |
| `static/script.js` | 前端脚本 |
| `VERSION` | 版本号 |

---

## 八、注意事项

1. **免费层限制** - Render 免费层 750 小时/月，Supabase 免费层 500MB 数据库
2. **冷启动** - Render 免费层首次请求可能较慢（约 30 秒）
3. **Session** - 基于 Flask session cookie，浏览器自动管理
4. **密码哈希** - 使用 werkzeug 的 scrypt 算法
5. **数据备份** - 目前无自动备份，建议定期从 Supabase Dashboard 导出

---

*此文件由 agent 自动维护，关键凭证变更时请同步更新。*
