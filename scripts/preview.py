"""Loopback-only lifecycle viewer; no provider or Azure calls."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
import json,argparse
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/':data=(ROOT/'preview/index.html').read_bytes();kind='text/html; charset=utf-8'
  elif self.path=='/data.json':data=json.dumps({'stages':json.loads((ROOT/'data/lifecycle.json').read_text()),'validation':json.loads((ROOT/'data/validation.json').read_text()),'dockerfile':(ROOT/'Dockerfile').read_text()}).encode();kind='application/json'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8144);a=p.parse_args();HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
