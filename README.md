# 周易八卦系统

周易八卦在线应用，包含铜钱起卦、蓍草起卦、时间起卦、五行生克、本命五行、八宅风水、八卦详解、纳甲排盘、二十八宿等功能。

## 功能清单

- 🪙 **铜钱起卦** — 模拟三枚铜钱摇卦
- 🌿 **蓍草起卦** — 模拟五十条茎演算
- 🕐 **时间起卦** — 按年月日时起卦
- ⚖️ **五行生克** — 五行关系查询与详解
- 🔮 **本命五行** — 按出生年月测算本命五行
- 🏠 **八宅风水** — 八宅风水方位分析
- ☯ **八卦详解** — 八卦卦象详解
- 📜 **纳甲排盘** — 六爻纳甲排盘
- 🌟 **二十八宿** — 二十八宿查询
- 📊 **六十四卦** — 全卦查询与搜索
- 👤 **用户系统** — 注册、登录、个人资料

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
python server.py
```

访问 http://localhost:5500

## 部署

### 部署到 Render（推荐）

1. 将本项目推送到 GitHub 仓库
2. 登录 [Render](https://render.com)
3. 点击 **New +** → **Web Service**
4. 选择你的 GitHub 仓库
5. 配置如下：
   - **Name**: yijing-web（自定义）
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
6. 点击 **Create Web Service**

免费额度：750 小时/月（足够 24/7 运行）

### 部署到 Railway

1. 将本项目推送到 GitHub 仓库
2. 登录 [Railway](https://railway.app)
3. 点击 **New Project** → **Deploy from GitHub repo**
4. 选择仓库，Railway 会自动检测 Python 项目
5. 添加环境变量（可选）：
   - `ADMIN_PASSWORD`: 管理后台密码
   - `FLASK_SECRET_KEY`: Session 密钥（建议随机生成）

### 部署到 PythonAnywhere

1. 登录 [PythonAnywhere](https://www.pythonanywhere.com)
2. 创建新账户（Free）
3. 在 **Files** 中上传项目 ZIP 或使用 Git 克隆
4. 在 **Web** 标签页创建新的 Web 应用
5. 选择 **Manual configuration**，Python 3.11
6. 配置 WSGI 文件指向 `wsgi.py`
7. 在 **Consoles** 中安装依赖：`pip install -r requirements.txt`

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `ADMIN_PASSWORD` | 管理后台密码 | `admin123` |
| `FLASK_SECRET_KEY` | Session 密钥 | `yijing-web-dev-key` |

## 管理后台

访问 `/admin` 进入管理后台，默认密码 `admin123`。

功能：
- 📊 数据总览（用户数、行为数、趋势图）
- 👥 用户列表与详情
- 📜 最近行为记录

## 版本

当前版本：1.5.1

## License

MIT
