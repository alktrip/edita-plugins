# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
import json,re,subprocess,sys,os
from concurrent.futures import ThreadPoolExecutor
base=sys.argv[1]
os.makedirs(base+'/gh',exist_ok=True)
d=json.load(open(base+'/npl/pl.x64.json',encoding='utf-8-sig'))
def api(path):
    r=subprocess.run(['gh','api',path],capture_output=True,text=True)
    return json.loads(r.stdout) if r.returncode==0 else {'_error':r.stderr.strip()[:200]}
def one(p):
    urls=p['repository']+' '+p.get('homepage','')
    m=re.search(r'github\.com/([^/\s]+)/([^/\s#?]+)',urls)
    out={'folder':p['folder-name'],'version':p['version'],'repo':None}
    if m:
        o,r=m.group(1),m.group(2).removesuffix('.git')
        info=api(f'repos/{o}/{r}')
        if '_error' not in info:
            full=info['full_name']; out['repo']=full
            out['license']=(info.get('license') or {}).get('spdx_id')
            out['archived']=info['archived']; out['pushed']=info['pushed_at']; out['stars']=info['stargazers_count']
            out['langs']=api(f'repos/{full}/languages')
            t=api(f'repos/{full}/git/trees/{info["default_branch"]}?recursive=1')
            files=[x['path'] for x in t.get('tree',[]) if x['type']=='blob']
            out['nfiles']=len(files)
            ext={}
            for f in files:
                e=os.path.splitext(f)[1].lower(); ext[e]=ext.get(e,0)+1
            out['ext']=ext
            out['licfiles']=[f for f in files if re.search(r'(licen[cs]e|copying)',f,re.I)][:5]
        else: out['error']=info['_error']
    json.dump(out,open(f'{base}/gh/{re.sub(r"[^A-Za-z0-9_.-]","_",p["folder-name"])}.json','w'))
with ThreadPoolExecutor(8) as ex: list(ex.map(one,d['npp-plugins']))
# Resumen: lenguaje principal de cada repositorio
import glob
rows=[json.load(open(f)) for f in glob.glob(f'{base}/gh/*.json')]
for r in rows:
    if r.get('repo'):
        L=r['langs']; r['main']=max(L,key=L.get) if L else '(sin código)'
json.dump(rows,open(f'{base}/rows.json','w'))
