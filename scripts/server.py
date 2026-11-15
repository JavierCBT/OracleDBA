import http.server
import socket
import socketserver
import os
import sys

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

PORT = 8080
local_ip = get_local_ip()
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(web_dir)

class CustomHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and caching headers for PWA
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

print("=" * 60)
print("  ORACLE 19c DBA EXAM SIMULATOR - LOCAL SERVER")
print("=" * 60)
print(f" Directorio raíz : {web_dir}")
print(f" Acceso desde PC : http://localhost:{PORT}")
print(f" Acceso TABLET   : http://{local_ip}:{PORT}")
print("=" * 60)
print(" Para salir del servidor presiona Ctrl+C en esta consola.\n")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", PORT), CustomHTTPHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        sys.exit(0)
