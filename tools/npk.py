from __future__ import annotations
import argparse
import hashlib
import pickle
import re
import struct
import sys
import zlib
from pathlib import Path
_DN,_DT,_DF='j2h56ogodh3se','=dziaq.','|os=5v7!"-234'
KEY=_DN*4+(_DT+_DN+_DF)*5+'!'+'#'+_DT*7+_DF*2+"*&'"
HEADER=struct.Struct('<4s5I')
RECORD=struct.Struct('<6I2H')
NEOXTRACTOR=Path('D:\\CyberHunter_backup\\archive\\tools\\NeoXtractor')
class Entry:
	__slots__='pack','index','path','off','clen','olen','zip_flag','md5'
	def __init__(self,pack,index,path,rec):_sign,self.off,self.clen,self.olen,_zc,_cc,self.zip_flag,_ff=rec;self.pack=pack;self.index=index;self.path=path;self.md5=None
	@property
	def ext(self)->str:return Path(self.path).suffix.lower()
	def stored(self)->bytes:
		with self.pack.npk.open('rb')as fh:fh.seek(self.off);return fh.read(self.clen)
	def raw(self)->bytes:
		blob=self.stored()
		if self.clen!=self.olen:import lz4.block;blob=lz4.block.decompress(blob,uncompressed_size=self.olen)
		return blob
	def decoded(self)->bytes:blob=self.raw();return decode_nxs(blob)if self.ext=='.nxs'else blob
	def verify(self)->bool|None:
		if self.md5 is None:return None
		return hashlib.md5(self.stored()).digest()==self.md5
	def __repr__(self)->str:return'<Entry %s %d bytes>'%(self.path,self.olen)
def reverse_string(b:bytes)->bytes:head=bytes(c^154 for c in b[:128]);return(head+b[128:])[::-1]
def decode_nxs(raw:bytes)->bytes:
	if raw[:1]!=b'\x1d':import lz4.block;return lz4.block.decompress(raw,uncompressed_size=1<<20)
	if str(NEOXTRACTOR)not in sys.path:sys.path.insert(0,str(NEOXTRACTOR))
	from core.rotor import Rotor;return reverse_string(zlib.decompress(Rotor(KEY).decrypt(raw)))
class Pack:
	def __init__(self,npk:Path):
		self.npk=Path(npk)
		if not self.npk.is_file():raise SystemExit('no pack: %s'%self.npk)
		self.entries=self._load();self._attach_md5()
	def _load(self)->list[Entry]:
		size=self.npk.stat().st_size
		with self.npk.open('rb')as fh:
			magic,count,_z1,_z2,self.mode,idx=HEADER.unpack(fh.read(HEADER.size))
			if magic!=b'NXPK':raise SystemExit('%s: not an NXPK pack (magic %r)'%(self.npk.name,magic))
			end=idx+count*RECORD.size
			if end>size:raise SystemExit('%s: index runs past end of file'%self.npk.name)
			fh.seek(idx);index=fh.read(count*RECORD.size);names=[n.decode('utf-8','replace').replace('\\','/')for n in fh.read().split(b'\x00')if n]
		if len(names)!=count:raise SystemExit('%s: %d records but %d names'%(self.npk.name,count,len(names)))
		out=[]
		for i in range(count):
			rec=RECORD.unpack_from(index,i*RECORD.size);e=Entry(self,i,names[i],rec)
			if e.off+e.clen>idx:raise SystemExit('%s: entry %d runs into the index'%(self.npk.name,i))
			out.append(e)
		return out
	def _attach_md5(self)->None:
		info=self.npk.with_name(self.npk.name+'.info_ext');self.info=info if info.is_file()else None
		if self.info is None:return
		try:_blob,names=pickle.loads(zlib.decompress(info.read_bytes()),encoding='latin-1')
		except Exception:self.info=None;return
		if len(names)!=len(self.entries):self.info=None;return
		by_name={}
		for row in names:
			key=row[0]
			if isinstance(key,str):key=key.encode('latin-1')
			by_name[key.replace(b'\\',b'/').lower()]=row[1]
		for e in self.entries:
			digest=by_name.get(e.path.replace('\\','/').lower().encode('utf-8'))
			if digest is None:continue
			e.md5=digest.encode('latin-1')if isinstance(digest,str)else digest
	def __len__(self)->int:return len(self.entries)
	def __iter__(self):return iter(self.entries)
	def get(self,path:str)->Entry|None:want=path.replace('\\','/').lower();return next((e for e in self.entries if e.path.lower()==want),None)
	def find(self,pattern:str)->list[Entry]:rx=re.compile(pattern,re.IGNORECASE);return[e for e in self.entries if rx.search(e.path)]
	def module_map(self)->dict[str,Entry]:return{e.path[:-4].replace('/','.'):e for e in self.entries if e.ext=='.nxs'}
def content_hash(e:Entry)->str:
	try:return hashlib.md5(e.decoded()).hexdigest()
	except Exception:return'undecodable:%d'%e.olen
def cmd_list(a)->int:
	pack=Pack(a.pack);rows=pack.find(a.pattern)if a.pattern else list(pack);print('%s  mode=%d  %d entries  info_ext=%s  (%d shown)'%(pack.npk.name,pack.mode,len(pack),'yes'if pack.info else'no',len(rows)))
	for e in rows[:a.limit]:print('  %6d  %10s  %s'%(e.index,format(e.olen,','),e.path))
	if len(rows)>a.limit:print('  ... %d more'%(len(rows)-a.limit))
	return 0
def cmd_cat(a)->int:
	pack=Pack(a.pack);e=pack.get(a.path)or next(iter(pack.find(a.path)),None)
	if e is None:raise SystemExit('not in %s: %s'%(pack.npk.name,a.path))
	blob=e.raw()if a.raw else e.decoded()
	if a.out:Path(a.out).write_bytes(blob);print('wrote %s (%d bytes) from %s'%(a.out,len(blob),e.path))
	else:sys.stdout.buffer.write(blob)
	return 0
def cmd_grep(a)->int:
	pack=Pack(a.pack);needle=a.needle.encode();scope=pack.find(a.only)if a.only else list(pack);hits=0
	for e in scope:
		try:blob=e.decoded()
		except Exception:continue
		if needle in blob:
			hits+=1;print('  %s'%e.path)
			if hits>=a.limit:break
	print('%d file(s) contain %r in %s'%(hits,a.needle,pack.npk.name));return 0 if hits else 1
def cmd_dump(a)->int:
	pack=Pack(a.pack);out=Path(a.out);ok=fail=skip=bad_md5=0;problems=[]
	for e in pack:
		if a.nxs_only and e.ext!='.nxs':skip+=1;continue
		try:blob=e.decoded()
		except Exception as exc:fail+=1;problems.append((e.path,type(exc).__name__,str(exc)[:70]));continue
		if e.verify()is False:bad_md5+=1
		rel=e.path[:-4]+'.marshal'if e.ext=='.nxs'else e.path;dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);ok+=1
	print('%s -> %s : ok=%d fail=%d skip=%d md5_mismatch=%d'%(pack.npk.name,out,ok,fail,skip,bad_md5))
	for p in problems[:10]:print('   FAIL %s (%s: %s)'%p)
	return 1 if fail else 0
def cmd_diff(a)->int:
	left,right=Pack(a.pack),Pack(a.other);lm,rm=left.module_map(),right.module_map();lk,rk=set(lm),set(rm);only_l,only_r,both=sorted(lk-rk),sorted(rk-lk),sorted(lk&rk);changed=[k for k in both if content_hash(lm[k])!=content_hash(rm[k])];print('LEFT  %s  %d modules'%(left.npk,len(lm)));print('RIGHT %s  %d modules'%(right.npk,len(rm)));print('only-left=%d  only-right=%d  shared=%d  changed=%d'%(len(only_l),len(only_r),len(both),len(changed)))
	for(label,rows)in(('ONLY IN RIGHT (added by right)',only_r),('ONLY IN LEFT (absent from right)',only_l),('CHANGED',changed)):
		if not rows:continue
		print('\n%s (%d)'%(label,len(rows)))
		for k in rows[:a.limit]:print('  %s'%k)
		if len(rows)>a.limit:print('  ... %d more'%(len(rows)-a.limit))
	return 0
def _demo()->None:game=Path(__file__).resolve().parents[1]/'game';pack=Pack(game/'script.npk');assert len(pack)>1000,len(pack);e=pack.get('xgame/entity.nxs');assert e is not None,'xgame/entity.nxs missing from script.npk';assert e.verify()is not False,'md5 mismatch on xgame/entity.nxs';blob=e.decoded();assert blob[:1]==b'c','marshal blob should start with a code object';assert b'entity.py'in blob,'embedded filename missing from marshal blob';print('npk self-check OK: %d entries, xgame/entity.nxs decodes to %d bytes'%(len(pack),len(blob)))
def main(argv=None)->int:ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);sub=ap.add_subparsers(dest='cmd',required=True);p=sub.add_parser('list',help='list entries');p.add_argument('pack',type=Path);p.add_argument('pattern',nargs='?');p.add_argument('--limit',type=int,default=200);p.set_defaults(fn=cmd_list);p=sub.add_parser('cat',help='decode one entry to stdout or a file');p.add_argument('pack',type=Path);p.add_argument('path');p.add_argument('--out');p.add_argument('--raw',action='store_true',help='skip the .nxs unwrap');p.set_defaults(fn=cmd_cat);p=sub.add_parser('grep',help='search decoded payloads for a literal');p.add_argument('pack',type=Path);p.add_argument('needle');p.add_argument('--only',help='restrict to paths matching this regex');p.add_argument('--limit',type=int,default=40);p.set_defaults(fn=cmd_grep);p=sub.add_parser('dump',help='extract the whole pack');p.add_argument('pack',type=Path);p.add_argument('--out',required=True);p.add_argument('--nxs-only',action='store_true');p.set_defaults(fn=cmd_dump);p=sub.add_parser('diff',help='compare two packs by module');p.add_argument('pack',type=Path);p.add_argument('other',type=Path);p.add_argument('--limit',type=int,default=60);p.set_defaults(fn=cmd_diff);p=sub.add_parser('selfcheck',help='verify the reader against the live packs');p.set_defaults(fn=lambda a:(_demo(),0)[1]);a=ap.parse_args(argv);return a.fn(a)
if __name__=='__main__':raise SystemExit(main())