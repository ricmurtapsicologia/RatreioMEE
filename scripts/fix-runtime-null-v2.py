# Trigger lifecycle patch v2.1
from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="document.getElementById('splash').classList.add('hidden');"
new="document.getElementById('splash')?.classList.add('hidden');"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('EXPECTED_SPLASH_CALL_NOT_FOUND')
old_main="document.getElementById('mainContent').classList.add('show');"
new_main="document.getElementById('mainContent')?.classList.add('show');"
if old_main in s:
    s=s.replace(old_main,new_main,1)
elif new_main not in s:
    raise SystemExit('EXPECTED_MAIN_CALL_NOT_FOUND')
if 'Eu exijo respeito ao não permitir que os outros me intimidem ou mandem em mim.' not in s:
    raise SystemExit('QUESTION_SENTINEL_MISSING')
p.write_text(s,encoding='utf-8')
