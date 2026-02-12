import threading
import os
import base64
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, make_response, send_file
from functools import wraps
import hashlib

# 全局变量
status = "正常运行"
返回内容_base64 = ""
返回内容_v2ray = ""
port = 5000
admin_username = ""
admin_password = ""

# 获取当前脚本的绝对路径目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def 获取路径(filename):
    """获取文件的绝对路径"""
    return os.path.join(BASE_DIR, filename)


# 初始化配置
def 初始化配置():
    global port, admin_username, admin_password

    # 读取端口配置
    start_file = 获取路径("start.txt")
    if os.path.exists(start_file):
        with open(start_file, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            if line.startswith("port="):
                port = int(line.split("=")[1])
    else:
        with open(start_file, "w", encoding="utf-8") as f:
            f.write("port=5000")
        port = 5000

    # 读取管理员账户
    admin_file = 获取路径("admin.json")
    if os.path.exists(admin_file):
        with open(admin_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            admin_username = data.get("username", "")
            admin_password = data.get("password", "")

    # 创建必要的目录和文件
    data_file = 获取路径("data.txt")
    if not os.path.exists(data_file):
        with open(data_file, "w", encoding="utf-8") as f:
            f.write("")

    log_file = 获取路径("uservisitlog.txt")
    if not os.path.exists(log_file):
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")

    logger_file = 获取路径("logger.txt")
    if not os.path.exists(logger_file):
        with open(logger_file, "w", encoding="utf-8") as f:
            f.write("")

    history_dir = 获取路径("history")
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)


def 写入日志(action, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action} - {details}\n"
    logger_file = 获取路径("logger.txt")
    with open(logger_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def 记录访问(path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    accept_language = request.headers.get('Accept-Language', '')

    log_entry = f"[{timestamp}] IP: {ip} | Path: {path} | UA: {user_agent} | Lang: {accept_language}\n"
    log_file = 获取路径("uservisitlog.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def v2ray转base64(content):
    """将v2ray格式转换为base64"""
    try:
        # 假设每行一个节点
        lines = content.strip().split('\n')
        valid_lines = [line for line in lines if line.strip() and ('://' in line)]

        if valid_lines:
            combined = '\n'.join(valid_lines)
            base64_content = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
            return base64_content
        return content
    except:
        return content


def 检测订阅格式(content):
    """检测订阅文件格式"""
    if not content.strip():
        return "empty"

    # 检查是否包含v2ray协议
    protocols = ['ss://', 'vmess://', 'vless://', 'trojan://', 'hy2://', 'hysteria2://']
    if any(protocol in content for protocol in protocols):
        return "v2ray"

    # 尝试解析base64
    try:
        base64.b64decode(content)
        return "base64"
    except:
        return "unknown"


def 保存历史版本(content, file_type):
    """保存历史版本"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{file_type}_{timestamp}.txt"
    filepath = 获取路径(os.path.join("history", filename))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    写入日志("保存历史版本", f"文件: {filename}")


def 需要登录(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token or not 验证token(token):
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def 生成token(username, password):
    return hashlib.sha256(f"{username}:{password}:secret_salt".encode()).hexdigest()


def 验证token(token):
    if not admin_username or not admin_password:
        return False
    expected_token = 生成token(admin_username, admin_password)
    return token == expected_token


# HTML模板
首页模板 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>订阅服务 - 用爱发电</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #ff2e63;
            --secondary: #08d9d6;
            --dark: #1a1a2e;
            --light: #eaeaea;
            --accent: #ffbe0b;
        }

        body {
            font-family: 'Noto Sans SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        body::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(255,255,255,0.03) 10px,
                rgba(255,255,255,0.03) 20px
            );
            animation: move 20s linear infinite;
        }

        @keyframes move {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }

        .container {
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            padding: 60px;
            max-width: 600px;
            width: 90%;
            box-shadow: 0 30px 60px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            animation: fadeIn 0.6s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        h1 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 3.5em;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 20px;
            font-weight: 700;
            letter-spacing: -2px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.2em;
            margin-bottom: 40px;
            font-weight: 400;
        }

        .links {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .link-item {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 15px;
            padding: 25px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .link-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }

        .link-item:hover::before {
            left: 100%;
        }

        .link-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        }

        .link-title {
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 8px;
            font-family: 'JetBrains Mono', monospace;
        }

        .link-desc {
            font-size: 0.95em;
            opacity: 0.9;
        }

        .footer {
            margin-top: 40px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }

        .heart {
            color: var(--primary);
            animation: heartbeat 1.5s ease-in-out infinite;
        }

        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        @media (max-width: 768px) {
            .container {
                padding: 40px 30px;
            }

            h1 {
                font-size: 2.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ 订阅</h1>
        <p class="subtitle">快速、稳定、安全的订阅服务</p>

        <div class="links">
            <a href="/sub_base64" class="link-item">
                <div class="link-title">📦 Base64 订阅</div>
                <div class="link-desc">获取 Base64 编码的订阅链接</div>
            </a>

            <a href="/sub_v2ray" class="link-item">
                <div class="link-title">🚀 V2Ray 订阅</div>
                <div class="link-desc">获取 V2Ray 原始格式订阅</div>
            </a>
        </div>

        <div class="footer">
            用 <span class="heart">❤️</span> 发电 | Powered by Flask
        </div>
    </div>
</body>
</html>
"""

登录模板 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理员登录</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Sans SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-container {
            background: white;
            border-radius: 20px;
            padding: 50px;
            max-width: 450px;
            width: 90%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }

        h2 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: #666;
            margin-bottom: 40px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }

        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #eee;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
            font-family: 'JetBrains Mono', monospace;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Noto Sans SC', sans-serif;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .error {
            background: #ffe5e5;
            color: #d32f2f;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #d32f2f;
        }

        .info {
            background: #e3f2fd;
            color: #1976d2;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #1976d2;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🔐 登录</h2>
        <p class="subtitle">管理员控制面板</p>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if info %}
        <div class="info">{{ info }}</div>
        {% endif %}

        <form method="POST">
            <div class="form-group">
                <label>用户名</label>
                <input type="text" name="username" required {% if is_first_time %}placeholder="设置管理员用户名"{% endif %}>
            </div>

            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" required {% if is_first_time %}placeholder="设置管理员密码"{% endif %}>
            </div>

            <button type="submit">{% if is_first_time %}创建管理员账户{% else %}登录{% endif %}</button>
        </form>
    </div>
</body>
</html>
"""

管理面板模板 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理面板</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Sans SC', sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 30px 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2em;
            margin-bottom: 5px;
        }

        .header .status {
            opacity: 0.9;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }

        .card h2 {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
            font-family: 'JetBrains Mono', monospace;
        }

        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }

        .status-normal {
            background: #d4edda;
            color: #155724;
        }

        .status-maintenance {
            background: #fff3cd;
            color: #856404;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Noto Sans SC', sans-serif;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        }

        .btn-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        textarea {
            width: 100%;
            min-height: 150px;
            padding: 15px;
            border: 2px solid #eee;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9em;
            resize: vertical;
            margin-bottom: 15px;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .file-input {
            display: none;
        }

        .file-label {
            display: inline-block;
            padding: 12px 24px;
            background: #eee;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .file-label:hover {
            background: #ddd;
        }

        .log-viewer {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85em;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .history-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .history-item {
            padding: 12px;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .history-item:hover {
            background: #e9ecef;
        }

        .emergency-stop {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
            font-size: 1.2em;
            padding: 20px 40px;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            font-weight: 700;
            box-shadow: 0 6px 12px rgba(255, 65, 108, 0.4);
            transition: all 0.3s;
        }

        .emergency-stop:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(255, 65, 108, 0.6);
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }

        .input-group input, .input-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #eee;
            border-radius: 8px;
            font-size: 1em;
        }

        .success-msg {
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #28a745;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .logout-btn:hover {
            background: white;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1400px; margin: 0 auto; padding: 0 40px;">
            <div class="top-bar">
                <div>
                    <h1>⚙️ 管理面板</h1>
                    <p class="status">当前状态: <span class="status-badge {% if status == '正常运行' %}status-normal{% else %}status-maintenance{% endif %}">{{ status }}</span></p>
                </div>
                <form method="POST" action="/logout" style="margin: 0;">
                    <button type="submit" class="logout-btn">退出登录</button>
                </form>
            </div>
        </div>
    </div>

    <div class="container">
        {% if success %}
        <div class="success-msg">{{ success }}</div>
        {% endif %}

        <div class="grid">
            <!-- 上传订阅文件 -->
            <div class="card">
                <h2>📤 上传订阅</h2>
                <form method="POST" action="/upload_subscription" enctype="multipart/form-data">
                    <textarea name="content" placeholder="粘贴订阅内容或使用下方按钮上传文件..."></textarea>
                    <input type="file" id="file-input" name="file" class="file-input" accept=".txt">
                    <label for="file-input" class="file-label">📁 选择文件</label>
                    <div style="margin-top: 15px;">
                        <button type="submit" class="btn btn-primary">上传并更新</button>
                    </div>
                </form>
            </div>

            <!-- 系统状态控制 -->
            <div class="card">
                <h2>🎛️ 系统控制</h2>
                <form method="POST" action="/change_status">
                    <div class="input-group">
                        <label>切换系统状态</label>
                        <select name="new_status" style="width: 100%; padding: 12px; border: 2px solid #eee; border-radius: 8px; font-size: 1em;">
                            <option value="正常运行" {% if status == '正常运行' %}selected{% endif %}>正常运行</option>
                            <option value="维护中..." {% if status == '维护中...' %}selected{% endif %}>维护中...</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-success">更新状态</button>
                </form>

                <div style="margin-top: 30px; text-align: center;">
                    <form method="POST" action="/emergency_stop" onsubmit="return confirm('确定要紧急停止服务器吗？');">
                        <button type="submit" class="emergency-stop">🚨 紧急停止</button>
                    </form>
                </div>
            </div>

            <!-- 修改密码 -->
            <div class="card">
                <h2>🔑 修改密码</h2>
                <form method="POST" action="/change_password">
                    <div class="input-group">
                        <label>新用户名</label>
                        <input type="text" name="new_username" value="{{ username }}" required>
                    </div>
                    <div class="input-group">
                        <label>新密码</label>
                        <input type="password" name="new_password" placeholder="留空则不修改">
                    </div>
                    <button type="submit" class="btn btn-primary">保存修改</button>
                </form>
            </div>
        </div>

        <!-- 历史版本 -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2>📚 历史版本</h2>
            <div class="history-list">
                {% for file in history_files %}
                <div class="history-item">
                    <span style="font-family: 'JetBrains Mono', monospace;">{{ file }}</span>
                    <a href="/download_history/{{ file }}" class="btn btn-primary" style="padding: 8px 16px; text-decoration: none; display: inline-block;">下载</a>
                </div>
                {% endfor %}
                {% if not history_files %}
                <p style="color: #999; text-align: center; padding: 20px;">暂无历史版本</p>
                {% endif %}
            </div>
        </div>

        <!-- 访问日志 -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2>📊 访问日志</h2>
            <div class="log-viewer">{{ visit_log }}</div>
        </div>

        <!-- 系统日志 -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2>📝 系统日志</h2>
            <div class="log-viewer">{{ system_log }}</div>
        </div>
    </div>

    <script>
        // 文件选择显示
        document.getElementById('file-input').addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || '未选择文件';
            document.querySelector('.file-label').textContent = '📁 ' + fileName;
        });
    </script>
</body>
</html>
"""


def 线程_网页():
    global status, 返回内容_base64, 返回内容_v2ray, admin_username, admin_password

    app = Flask(__name__)
    app.secret_key = 'your-secret-key-change-this-in-production'

    @app.route('/')
    def index_():
        记录访问('/')
        return render_template_string(首页模板)

    @app.route('/sub_base64')
    def index():
        记录访问('/sub_base64')
        if 返回内容_base64 == "":
            return "初次使用，请在管理面板设置订阅内容..."
        if status == "维护中...":
            return "当前正在维护，暂不可用"
        if status == "正常运行":
            写入日志("Base64订阅访问", f"IP: {request.remote_addr}")
            return 返回内容_base64
        return "服务异常"

    @app.route('/sub_v2ray')
    def v2ray返回哦():
        记录访问('/sub_v2ray')
        if 返回内容_v2ray == "":
            return "初次使用，请在管理面板设置订阅内容..."
        if status == "维护中...":
            return "当前正在维护，暂不可用"
        if status == "正常运行":
            写入日志("V2Ray订阅访问", f"IP: {request.remote_addr}")
            return 返回内容_v2ray
        return "服务异常"

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        global admin_username, admin_password

        记录访问('/login')
        is_first_time = not admin_username or not admin_password

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if is_first_time:
                # 首次设置管理员账户
                if username and password:
                    admin_username = username
                    admin_password = hashlib.sha256(password.encode()).hexdigest()

                    # 保存到文件
                    admin_file = 获取路径("admin.json")
                    with open(admin_file, "w", encoding="utf-8") as f:
                        json.dump({"username": admin_username, "password": admin_password}, f)

                    写入日志("创建管理员账户", f"用户名: {username}")

                    # 设置cookie并跳转
                    token = 生成token(admin_username, admin_password)
                    resp = make_response(redirect(url_for('admin')))
                    resp.set_cookie('admin_token', token, max_age=7 * 24 * 60 * 60)
                    return resp
                else:
                    return render_template_string(登录模板, error="用户名和密码不能为空", is_first_time=True)
            else:
                # 验证登录
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if username == admin_username and password_hash == admin_password:
                    写入日志("管理员登录", f"用户名: {username}, IP: {request.remote_addr}")
                    token = 生成token(admin_username, admin_password)
                    resp = make_response(redirect(url_for('admin')))
                    resp.set_cookie('admin_token', token, max_age=7 * 24 * 60 * 60)
                    return resp
                else:
                    写入日志("登录失败", f"用户名: {username}, IP: {request.remote_addr}")
                    return render_template_string(登录模板, error="用户名或密码错误", is_first_time=False)

        if is_first_time:
            return render_template_string(登录模板, info="首次使用，请设置管理员账户", is_first_time=True)

        return render_template_string(登录模板, is_first_time=False)

    @app.route('/logout', methods=['POST'])
    def logout():
        写入日志("管理员登出", f"IP: {request.remote_addr}")
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('admin_token', '', max_age=0)
        return resp

    @app.route('/admin')
    @需要登录
    def admin():
        记录访问('/admin')

        # 读取历史文件
        history_files = []
        history_dir = 获取路径("history")
        if os.path.exists(history_dir):
            history_files = sorted([f for f in os.listdir(history_dir) if f.endswith('.txt')], reverse=True)

        # 读取日志
        visit_log = ""
        log_file = 获取路径("uservisitlog.txt")
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                visit_log = "".join(lines[-50:])  # 最近50条

        system_log = ""
        logger_file = 获取路径("logger.txt")
        if os.path.exists(logger_file):
            with open(logger_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                system_log = "".join(lines[-50:])  # 最近50条

        success = request.args.get('success', '')

        return render_template_string(管理面板模板,
                                      status=status,
                                      username=admin_username,
                                      history_files=history_files,
                                      visit_log=visit_log or "暂无访问记录",
                                      system_log=system_log or "暂无系统日志",
                                      success=success)

    @app.route('/upload_subscription', methods=['POST'])
    @需要登录
    def upload_subscription():
        global 返回内容_base64, 返回内容_v2ray

        content = request.form.get('content', '').strip()

        # 如果没有文本内容，尝试从文件读取
        if not content and 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                content = file.read().decode('utf-8', errors='ignore')

        if content:
            # 检测格式
            format_type = 检测订阅格式(content)

            if format_type == "v2ray":
                返回内容_v2ray = content
                返回内容_base64 = v2ray转base64(content)
                保存历史版本(content, "v2ray")
                写入日志("上传V2Ray订阅", "自动转换为Base64")
            elif format_type == "base64":
                返回内容_base64 = content
                try:
                    decoded = base64.b64decode(content).decode('utf-8')
                    返回内容_v2ray = decoded
                except:
                    返回内容_v2ray = content
                保存历史版本(content, "base64")
                写入日志("上传Base64订阅", "自动解码为V2Ray格式")
            else:
                # 未知格式，同时保存
                返回内容_v2ray = content
                返回内容_base64 = content
                保存历史版本(content, "unknown")
                写入日志("上传订阅", "格式未知")

            # 保存到data.txt
            data_file = 获取路径("data.txt")
            with open(data_file, "w", encoding="utf-8") as f:
                f.write(f"base64:{返回内容_base64}\n")
                f.write(f"v2ray:{返回内容_v2ray}\n")

            return redirect(url_for('admin') + '?success=订阅内容已更新')

        return redirect(url_for('admin'))

    @app.route('/change_status', methods=['POST'])
    @需要登录
    def change_status():
        global status
        new_status = request.form.get('new_status', '')
        if new_status in ['正常运行', '维护中...']:
            old_status = status
            status = new_status
            写入日志("修改系统状态", f"从 {old_status} 改为 {new_status}")
        return redirect(url_for('admin') + '?success=状态已更新')

    @app.route('/change_password', methods=['POST'])
    @需要登录
    def change_password():
        global admin_username, admin_password

        new_username = request.form.get('new_username', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if new_username:
            admin_username = new_username

        if new_password:
            admin_password = hashlib.sha256(new_password.encode()).hexdigest()

        # 保存到文件
        admin_file = 获取路径("admin.json")
        with open(admin_file, "w", encoding="utf-8") as f:
            json.dump({"username": admin_username, "password": admin_password}, f)

        写入日志("修改管理员信息", f"新用户名: {new_username}")

        return redirect(url_for('admin') + '?success=账户信息已更新')

    @app.route('/download_history/<filename>')
    @需要登录
    def download_history(filename):
        filepath = 获取路径(os.path.join("history", filename))
        if os.path.exists(filepath):
            写入日志("下载历史文件", f"文件: {filename}")
            return send_file(filepath, as_attachment=True)
        return "文件不存在", 404

    @app.route('/emergency_stop', methods=['POST'])
    @需要登录
    def emergency_stop():
        写入日志("紧急停止", f"管理员触发紧急停止，IP: {request.remote_addr}")

        # 创建一个函数来停止服务器
        def shutdown():
            import time
            time.sleep(1)
            os._exit(0)

        # 在新线程中执行停止
        threading.Thread(target=shutdown).start()

        return "服务器即将停止..."

    写入日志("服务器启动", f"端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


def 获取data_txt():
    global 返回内容_base64, 返回内容_v2ray

    data_file = 获取路径("data.txt")
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("base64:"):
                    返回内容_base64 = line[7:].strip()
                elif line.startswith("v2ray:"):
                    返回内容_v2ray = line[6:].strip()


# 主程序
if __name__ == "__main__":
    初始化配置()
    获取data_txt()

    网页 = threading.Thread(target=线程_网页)
    网页.daemon = True
    网页.start()

    print(f"服务器已启动在端口 {port}")
    print(f"访问地址: http://localhost:{port}")
    print(f"管理面板: http://localhost:{port}/admin")
    print(f"工作目录: {BASE_DIR}")

    # 保持主线程运行
    try:
        网页.join()
    except KeyboardInterrupt:
        写入日志("服务器停止", "用户按下 Ctrl+C")
        print("\n服务器已停止")