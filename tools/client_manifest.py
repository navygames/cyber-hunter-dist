from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
MANIFEST=Path('client')/'client_manifest.json'
REQUIRED='data.npk','script.npk','patch.npk'
def repo_root()->Path:return Path(__file__).resolve().parents[1]
def _sha256(p:Path)->str:
	h=hashlib.sha256()
	with p.open('rb')as fh:
		for chunk in iter(lambda:fh.read(1<<20),b''):h.update(chunk)
	return h.hexdigest()
def scan(game:Path)->dict:
	packs={}
	for npk in sorted(game.rglob('*.npk')):
		rel=npk.relative_to(game).as_posix();row={'size':npk.stat().st_size};idx=npk.with_name(npk.name+'.info_ext')
		if idx.is_file():row['index_sha256']=_sha256(idx);row['index_size']=idx.stat().st_size
		if rel in REQUIRED:row['sha256']=_sha256(npk)
		packs[rel]=row
	return{'note':'Identity of the reference client. See tools/client_manifest.py.','required':list(REQUIRED),'packs':packs}
def compare(ref:dict,cur:dict)->dict:
	rp,cp=ref['packs'],cur['packs'];required=set(ref.get('required')or REQUIRED);fatal,content,extra=[],[],[]
	for(rel,want)in sorted(rp.items()):
		got=cp.get(rel);bucket=fatal if rel in required else content
		if got is None:bucket.append('MISSING   %s'%rel);continue
		if want.get('index_sha256')and got.get('index_sha256')and want['index_sha256']!=got['index_sha256']:bucket.append('INDEX     %s (entry table differs from reference)'%rel);continue
		if want.get('sha256')and got.get('sha256')and want['sha256']!=got['sha256']:bucket.append('CONTENT   %s (base pack bytes differ)'%rel);continue
		if want['size']!=got['size']:content.append('SIZE      %s (%d vs reference %d)'%(rel,got['size'],want['size']))
	for rel in sorted(set(cp)-set(rp)):extra.append('EXTRA     %s'%rel)
	return{'fatal':fatal,'content':content,'extra':extra}
def main(argv=None)->int:
	ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true',help='regenerate the manifest');ap.add_argument('--strict',action='store_true',help='exit 1 on content drift too');ap.add_argument('--game',default=None);ap.add_argument('--manifest',default=None);args=ap.parse_args(argv);root=repo_root();game=Path(args.game)if args.game else root/'game';mpath=Path(args.manifest)if args.manifest else root/MANIFEST
	if not game.is_dir():print('client manifest: %s not present (game/ is supplied per machine) - skipping'%game);return 0
	if args.write:data=scan(game);mpath.parent.mkdir(parents=True,exist_ok=True);mpath.write_text(json.dumps(data,indent=1,sort_keys=True)+'\n',encoding='utf-8');print('client manifest written: %d packs -> %s'%(len(data['packs']),mpath));return 0
	if not mpath.is_file():print('client manifest: %s missing - run --write on the reference PC'%mpath);return 0
	ref=json.loads(mpath.read_text(encoding='utf-8'));diff=compare(ref,scan(game));fatal,content,extra=diff['fatal'],diff['content'],diff['extra']
	if not fatal and not content:
		print('client matches the reference manifest (%d packs)'%len(ref['packs']))
		if extra:print('  %d extra pack(s) beyond the reference - fine'%len(extra))
		return 0
	if fatal:
		print('CLIENT MISMATCH - these stop the client booting coherently:')
		for line in fatal:print('  '+line)
		print('Your game/ base packs differ from the reference client. See docs/FRESH_CLONE_BOOT.md.')
	if content:
		print('client content differs from the reference (%d) - playable, but you have less/other content:'%len(content))
		for line in content[:20]:print('  '+line)
		if len(content)>20:print('  ... and %d more'%(len(content)-20))
	return 1 if fatal or args.strict and content else 0
if __name__=='__main__':sys.exit(main())