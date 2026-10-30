# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
import os,re,json,sys
base=sys.argv[1]
pats={
 'dialog':r'\b(DialogBox(Param)?|CreateDialog(Param)?|StaticDialog|DockingDlgInterface|NPPM_DMMREGASDCKDLG)\b',
 'window':r'\b(CreateWindowEx?W?|RegisterClassEx?W?|BeginPaint)\b',
 'mfc':r'#\s*include\s*[<"]afx',
 'com':r'\b(CoCreateInstance|CoInitialize(Ex)?)\b|#\s*include\s*[<"]atl|#\s*import\b',
 'registry':r'\bReg(Open|Create|Query)Key',
 'thread':r'\b(CreateThread|_beginthreadex)\b',
 'process':r'\bCreateProcessW?\b',
 'lexer':r'\b(GetLexerCount|CreateLexer|ILexer5?)\b',
}
cre={k:re.compile(v) for k,v in pats.items()}
skip=re.compile(r'(^|/)(scintilla|lexilla|boost|third.?party|external|deps|vendor|lib)(/|$)',re.I)
res={}
for d in sorted(os.listdir(base)):
    root=os.path.join(base,d); hits={k:0 for k in pats}; nsrc=0; loc=0; rc=0
    for dp,dn,fn in os.walk(root):
        rel=os.path.relpath(dp,root)
        if skip.search(rel): continue
        for f in fn:
            e=os.path.splitext(f)[1].lower()
            if e=='.rc': rc+=1
            if e not in ('.c','.cpp','.cc','.cxx','.h','.hpp'): continue
            try: t=open(os.path.join(dp,f),encoding='utf-8',errors='replace').read()
            except: continue
            nsrc+=1; loc+=t.count('\n')
            for k,c in cre.items(): hits[k]+=len(c.findall(t))
    res[d]={'nsrc':nsrc,'loc':loc,'rc':rc,**hits}
json.dump(res,open(sys.argv[2],'w'),indent=0)
