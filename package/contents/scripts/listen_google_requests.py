from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import logging
import os
from datetime import datetime

log_dir = "~/.local/share/plasma/plasmoids/org.kde.plasma.eventcalendar/contents/scripts"
log_file = "listen_google_requests.log"

log_dir = os.path.expanduser(log_dir)

# 如果日志文件存在，以当前时间为后缀重命名
if os.path.exists(os.path.join(log_dir, log_file)):
    os.rename(
        os.path.join(log_dir, log_file),
        os.path.join(log_dir, f'{datetime.now().strftime("%Y%m%d%H%M%S")}-{log_file}')
    )

# 如果日志文件大于30个，删除最旧的日志文件，保留最新的5个
log_files = [
    os.path.join(log_dir, f)
    for f in os.listdir(log_dir)
    if f.endswith('.log')
]
if len(log_files) > 30:
    log_files.sort()
    for f in log_files[:-5]:
        os.remove(f)


# 配置日志记录
logging.basicConfig(
    filename=os.path.join(log_dir, log_file),  # 日志文件
    level=logging.INFO,      # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s'  # 日志格式
)


class RequestHandler(BaseHTTPRequestHandler):
    proxy = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }

    def log_message(self, format, *args):
        super().log_message(format, *args)
        logging.info(format % args)

    def do_GET(self):
        # 提取 new_url
        path_parts = self.path.split('/', 1)
        new_url = path_parts[1]
        headers = {key: value for key, value in self.headers.items()
                   if key != 'Host'}

        # 转发请求到 new_url
        try:
            response = requests.get(
                new_url, headers=headers, proxies=self.proxy)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except requests.exceptions.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        # 提取 new_url
        path_parts = self.path.split('/', 1)
        new_url = path_parts[1]
        headers = {key: value for key, value in self.headers.items()
                   if key != 'Host'}
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # 转发请求到 new_url
        try:
            response = requests.post(
                new_url, headers=headers, data=post_data, proxies=self.proxy)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except requests.exceptions.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())


def run(server_class=HTTPServer, handler_class=RequestHandler, port=61616):
    server_address = ('127.0.0.1', port)  # 只监听本机请求
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
