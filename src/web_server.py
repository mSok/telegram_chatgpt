import http.server
import socketserver

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)

def run_web_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
