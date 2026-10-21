#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import logging
import ssl
import sys
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlparse
ROOT=Path(__file__).resolve().parent
CERT_DIR=ROOT/'certs'
RESPONSES=ROOT/'responses'
LOG_DIR=ROOT/'logs'
HOSTNAME='g94na.update.easebar.com'
DEFAULT_PROFILE='ret_code_ok'
def list_profiles()->list[str]:return sorted(p.stem for p in RESPONSES.glob('*.json')if p.stem!='npk_version')
def load_body(profile:str)->tuple[bytes,str]:
	path=RESPONSES/f"{profile}.json"
	if not path.exists():raise FileNotFoundError(f"unknown profile {profile!r}; available: {", ".join(list_profiles())}")
	text=path.read_text(encoding='utf-8');payload=json.dumps(json.loads(text),separators=(',',':'),ensure_ascii=False).encode('utf-8');return payload,'application/json; charset=utf-8'
def load_npk_version()->bytes:
	path=RESPONSES/'npk_version.json'
	if path.exists():payload=json.dumps(json.loads(path.read_text(encoding='utf-8')),separators=(',',':'),ensure_ascii=False)
	else:payload=json.dumps({'client_version':'1.251560.230461.251560','version':'1.251560.230461.251560','engine_version':'1.251560.230461.251560','force_update':0,'review':0},separators=(',',':'))
	return('##########\n'+payload).encode('utf-8')
class PatchHandler(BaseHTTPRequestHandler):
	server_version='CyberHunterPatchMock/1.0';profile=DEFAULT_PROFILE;sig_line='local'
	def log_message(self,fmt:str,*args)->None:logging.info('%s - %s',self.address_string(),fmt%args)
	def _send(self,code:int,body:bytes,content_type:str)->None:self.send_response(code);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Connection','close');self.send_header('Server',self.server_version);self.end_headers();self.wfile.write(body)
	def _log_request(self)->None:
		parsed=urlparse(self.path);qs=parse_qs(parsed.query,keep_blank_values=True);entry={'ts':datetime.now(timezone.utc).isoformat(),'method':self.command,'path':parsed.path,'query':qs,'headers':{k:v for(k,v)in self.headers.items()},'client':self.client_address[0],'profile':self.profile};LOG_DIR.mkdir(parents=True,exist_ok=True);log_file=LOG_DIR/'requests.jsonl'
		with log_file.open('a',encoding='utf-8')as fh:fh.write(json.dumps(entry,ensure_ascii=False)+'\n')
		logging.info('REQUEST %s %s qs=%s profile=%s',self.command,parsed.path,qs,self.profile)
	def do_GET(self)->None:
		self._log_request();parsed=urlparse(self.path);path=parsed.path.rstrip('/')
		if path=='/patch_map':
			try:body,ctype=load_body(self.profile)
			except FileNotFoundError as exc:self._send(500,str(exc).encode('utf-8'),'text/plain; charset=utf-8');return
			if self.sig_line is not None:body=body+b'\n'+self.sig_line.encode('utf-8')
			logging.info('RESPONSE profile=%s body=%s',self.profile,body.decode('utf-8','replace')[:500]);self._send(200,body,ctype);return
		if path.startswith('/npk_version'):body=load_npk_version();logging.info('RESPONSE npk_version body=%s',body.decode('utf-8','replace')[:500]);self._send(200,body,'text/plain; charset=utf-8');return
		if'serverlist'in path.lower()or path.endswith('/server.txt')or'server_list'in path.lower():
			sl=RESPONSES/'serverlist.txt';body=sl.read_bytes()if sl.exists()else b'127.0.0.1 10001 local\n'
			if self.sig_line is not None:body=body.rstrip()+b'\n'+self.sig_line.encode('utf-8')
			logging.info('RESPONSE serverlist path=%s',path);self._send(200,body,'text/plain; charset=utf-8');return
		if'notice'in path.lower():body=b'[]\nlocal';self._send(200,body,'text/plain; charset=utf-8');return
		if'query_product'in path.lower():body=b'{"ret_code":0,"code":0,"result":"ok","reason":"ok","product_info_list":[]}';logging.info('RESPONSE query_product empty product_info_list');self._send(200,body,'application/json; charset=utf-8');return
		self._send(200,b'{"ret_code":0,"code":0,"result":"ok"}','application/json; charset=utf-8')
	def do_HEAD(self)->None:self.do_GET()
	def do_POST(self)->None:
		self._log_request()
		try:
			length=int(self.headers.get('Content-Length',0))
			if length:self.rfile.read(length)
		except(ValueError,OSError):pass
		self._send(200,b'{"ret_code":0,"code":0,"result":"ok"}','application/json; charset=utf-8')
def build_ssl_context()->ssl.SSLContext:
	cert=CERT_DIR/'server.cert.pem';key=CERT_DIR/'server.key.pem'
	if not cert.exists()or not key.exists():raise FileNotFoundError(f"missing TLS files in {CERT_DIR}; run generate_certs.py first")
	ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(certfile=str(cert),keyfile=str(key));return ctx
def main(argv:list[str]|None=None)->int:
	parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--host',default='0.0.0.0',help='bind address (default: 0.0.0.0)');parser.add_argument('--port',type=int,default=443,help='bind port (default: 443, needs admin)');parser.add_argument('--profile',default=DEFAULT_PROFILE,choices=list_profiles(),help=f"response body template (default: {DEFAULT_PROFILE})");parser.add_argument('--sig-line',default='local',help="append '<newline><value>' after the JSON so fetch_list has a signature line to drop");parser.add_argument('-v','--verbose',action='store_true');args=parser.parse_args(argv);logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,format='%(asctime)s %(levelname)s %(message)s');PatchHandler.profile=args.profile;PatchHandler.sig_line=args.sig_line;httpd=ThreadingHTTPServer((args.host,args.port),PatchHandler);httpd.socket=build_ssl_context().wrap_socket(httpd.socket,server_side=True);logging.info('serving https://%s:%s/patch_map profile=%s',HOSTNAME,args.port,args.profile);logging.info('profiles: %s',', '.join(list_profiles()));logging.info('request log: %s',LOG_DIR/'requests.jsonl')
	try:httpd.serve_forever()
	except KeyboardInterrupt:logging.info('stopped');return 0
	finally:httpd.server_close()
	return 0
if __name__=='__main__':sys.exit(main())