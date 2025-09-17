from pathlib import Path
p=Path('frontend/src/services/api-client.ts')
s=p.read_text(encoding='utf-8')
s=s.replace('const http = axios.create({ timeout: 15000 })','const http = axios.create({ timeout: 15000 }) // default; translate() overrides to longer timeout')
s=s.replace("const { data } = await http.post('/translate', req)","const { data } = await http.post('/translate', req, { timeout: 120000 })")
p.write_text(s, encoding='utf-8')
print('patched', p)
