from pathlib import Path
p=Path('frontend/src/services/api-client.ts')
s=p.read_text(encoding='utf-8')
s=s.replace("const { data } = await http.get('/session/quota')","const { data } = await http.get('/session/quota', { timeout: 90000 })")
s=s.replace("throw new Error('无法获取配额 / Failed to fetch quota')","throw new Error('后端冷启动中，正在唤醒 / Backend cold start, waking up…')")
p.write_text(s, encoding='utf-8')
print('patched', p)
