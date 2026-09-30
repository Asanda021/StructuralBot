import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

WEB_ROOT = Path(__file__).resolve().parent.parent / "webapp"
MIME = {".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".svg":"image/svg+xml",".png":"image/png",".jpg":"image/jpeg",".webp":"image/webp"}

class MiniAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/miniapp" or self.path == "/miniapp/":
            rel="index.html"
        elif self.path.startswith("/webapp/"):
            rel=unquote(self.path[len("/webapp/"):]).split("?",1)[0]
        else:
            self.send_response(404); self.end_headers(); return
        target=(WEB_ROOT / rel).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())) or not target.is_file():
            self.send_response(404); self.end_headers(); return
        data=target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",MIME.get(target.suffix,"application/octet-stream"))
        self.send_header("Cache-Control","no-cache")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def log_message(self,*_): pass
