import json;d=json.load(open('riddles.json'));s=json.dumps(d,ensure_ascii=False).replace('</','<\\/')
open('index.html','w').write(open('src.html').read().replace('%%INLINE%%',s))
