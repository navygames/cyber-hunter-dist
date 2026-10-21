#!/usr/bin/env python3
from __future__ import annotations
import argparse
import logging
import socket
import threading
import time
from pathlib import Path
LOG=Path(__file__).resolve().parents[2]/'decompiled'/'gateway_stub.log'
def handle(conn:socket.socket,addr)->None:
	peer=f"{addr[0]}:{addr[1]}"
	try:
		conn.settimeout(1e1);logged=False
		while True:
			try:
				data=conn.recv(4096)
				if not data:break
				if not logged:
					logged=True;line=f"{time.strftime("%H:%M:%S")} ACCEPT {peer} bytes={len(data)} hex={data[:64].hex()}\n"
					try:
						LOG.parent.mkdir(parents=True,exist_ok=True)
						with LOG.open('a',encoding='utf-8')as fh:fh.write(line)
					except Exception:pass
					logging.info('%s',line.strip())
			except socket.timeout:continue
			except(ConnectionResetError,BrokenPipeError):break
	except Exception as exc:logging.info('handler err %s: %s',peer,exc)
	finally:
		try:conn.close()
		except OSError:pass
def main()->int:
	ap=argparse.ArgumentParser();ap.add_argument('--host',default='0.0.0.0');ap.add_argument('--port',type=int,default=10001);args=ap.parse_args();logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s');LOG.parent.mkdir(parents=True,exist_ok=True)
	try:LOG.write_text('',encoding='utf-8')
	except Exception:pass
	sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind((args.host,args.port));sock.listen(32);logging.info('gateway stub listening on %s:%s (log %s)',args.host,args.port,LOG)
	while True:conn,addr=sock.accept();threading.Thread(target=handle,args=(conn,addr),daemon=True).start()
if __name__=='__main__':raise SystemExit(main())