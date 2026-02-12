import threading

from flask import Flask
from threading import Thread
import os
status = "正常运行"
返回内容 = ""
port = "start.txt里面的第一行"

def 线程_网页():
    app = Flask(__name__)
    @app.route('/')
    def index_():
        return "用爱发电哦~"

    @app.route('/sub_base64')
    def index():
        if 返回内容=="":
            return "初次使用，请做设置...."
        if status=="维护中...":
            return "当前正在维护不可用"
        if status=="正常运行":
            return "返回相应的内容"#就是返回最新的订阅文件是txt，直接显示在网页上
        return "正常"

    @app.route('/sub_v2ray')
    def v2ray返回哦():
        if 返回内容=="":
            return "初次使用，请做设置...."
        if status=="维护中...":
            return "当前正在维护不可用"
        if status=="正常运行":
            return "返回相应的内容"#就是返回最新的订阅文件是txt，直接显示在网页上
    @app.route('/admin')
    def admin():
        return "admin"#这边是管理员面板，可以用到cookie的技术，也可以更改用户名和密码，首次登录网站的话要管理员设置用户名and密码
        #这边写管理员面板就是上传订阅文件txt啥的，然后可以设置状态，比如正常运行和维护中，然后还可以查看历史访问的ip啥的（服务器上就是保存在运行目录下的/uservisitlog.txt 详细记录用户的设备信息，比如ip，语言之类的可以溯源）
        #然后管理员可以查看和下载历史上传的文件就比如说管理员上传了新的订阅文件txt，之前的txt也要保留，管理员在后台可以下载，就像镜像源那样的历史版本,还有一个红色的紧急停止按钮就是防止突发情况，点了之后就关闭网页，停止程序，记得写进日志
        #然后还可以把v2ray的订阅的那种hy2://某某某  ss://某某某的这种 转换成一长串的base64在上面的返回  上传一个文件要自动识别是v2ray的那种hy2://某某某  ss://某某某的这种还是base64上面的两个返回路径要自动更新
    app.run(host='0.0.0.0', port=port)
def 获取data_txt():
    if not os.path.exists("data.txt"):
        o = open("data.txt","w")
        o.close()
        #这个文件的作用就是
网页 = threading.Thread(target=线程_网页)
网页.start()
#所有的动作都要写，比如管理员修改密码啊，程序的紧急停止啊，卸载logger.txt里面
#启动的端口写在start.txt里面的第一行(当前程序执行的路径/start.txt) 内容为  port=114514