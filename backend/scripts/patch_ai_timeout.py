from pathlib import Path, re
p=Path('backend/src/services/ai_client.py')
s=p.read_text(encoding='utf-8')
import re as _r
s=_r.sub(r"request_timeout: int = 60\s*# Request timeout in seconds \(some models are slower\)",
         "request_timeout: int = 120           # Request timeout in seconds (free cold starts can take ~60s+)", s, count=1)
s=_r.sub(r"timeout_duration: int = 60\s*# Seconds to wait before half-open",
         "timeout_duration: int = 90          # Seconds to wait before half-open (post-timeout cooldown)", s, count=1)
s=s.replace("self._timeout = aiohttp.ClientTimeout(total=timeout_val)",
           "self._timeout = aiohttp.ClientTimeout(total=timeout_val, connect=timeout_val, sock_read=timeout_val, sock_connect=timeout_val)")
p.write_text(s, encoding='utf-8')
print('patched', p)
