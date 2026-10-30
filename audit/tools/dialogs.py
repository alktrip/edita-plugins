# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
import os,re,json,sys
base=sys.argv[1]
tmpl=re.compile(r'(StaticDialog|DockingDlgInterface|Docking|Window|dockingResource|PluginInterface|Notepad_plus_msgs|menuCmdID|Scintilla|Sci_Position|SciLexer|ILexer|Lexilla)\.(h|cpp)$',re.I)
skip=re.compile(r'(^|/)(scintilla|lexilla|boost|third.?party|external|deps|vendor|test|tests)(/|$)',re.I)
dlgres=re.compile(r'^\s*\w+\s+DIALOG(EX)?\b',re.M)
use=re.compile(r'\b(DialogBox(Param)?W?|CreateDialog(Param)?W?|NPPM_DMMREGASDCKDLG|::create\s*\(|\.doDialog\s*\(|->doDialog\s*\()')
res={}
for d in sorted(os.listdir(base)):
    root=os.path.join(base,d); dl=0; us=0; files=[]
    for dp,dn,fn in os.walk(root):
        rel=os.path.relpath(dp,root)
        if skip.search(rel): continue
        for f in fn:
            p=os.path.join(dp,f); e=os.path.splitext(f)[1].lower()
            try: t=open(p,encoding='utf-8',errors='replace').read() if e in ('.rc','.c','.cpp','.cc','.h','.hpp','.cxx') else None
            except: continue
            if t is None:
                try: t=open(p,encoding='utf-16',errors='replace').read() if e=='.rc' else None
                except: t=None
            if t is None: continue
            if e=='.rc':
                if 'DIALOG' not in t:
                    try: t2=open(p,encoding='utf-16').read(); t=t2
                    except: pass
                dl+=len(dlgres.findall(t))
            elif not tmpl.search(f):
                n=len(use.findall(t)); us+=n
    res[d]={'dlgres':dl,'dlguse':us}
json.dump(res,open(sys.argv[2],'w'))
