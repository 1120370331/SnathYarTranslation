from pathlib import Path
import json, re
p=Path('frontend/src/services/api-client.ts')
s=p.read_text(encoding='utf-8')
# Insert cache helpers and warmup
insertion = '''
// Quota cache (1-day TTL based on backend reset_time)
const QS_KEY = 'shathyar_quota_cache_v2'

function loadCachedQuota(): QuotaStatus | null {
  try {
    const raw = localStorage.getItem(QS_KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || !data.reset_time) return null
    const rt = new Date(data.reset_time).getTime()
    if (isNaN(rt) || rt <= Date.now()) {
      // expired (past reset), clear
      try { localStorage.removeItem(QS_KEY) } catch {}
      return null
    }
    return data as QuotaStatus
  } catch { return null }
}

function saveCachedQuota(q: QuotaStatus) {
  try { localStorage.setItem(QS_KEY, JSON.stringify(q)) } catch {}
}

export function getCachedQuota(): QuotaStatus | null {
  return loadCachedQuota()
}

export async function warmupBackend(): Promise<void> {
  try {
    const base = getAppConfig().apiBaseUrl || '/api/v1'
    let healthUrl = '/health'
    try {
      const u = new URL(base, window.location.origin)
      healthUrl = u.origin + '/health'
    } catch {}
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 60000)
    try {
      await fetch(healthUrl, { signal: ctrl.signal, cache: 'no-store', mode: 'cors' })
    } catch {}
    clearTimeout(t)
  } catch {}
}
'''
if 'QS_KEY' not in s:
    # place after interceptor setup
    s = re.sub(r"\)\s*\n\}\)\s*\n", ")\n  return config\n})\n\n" + insertion, s, count=1)

# Extend getQuota to save cache and fallback to cache on error
s = s.replace("const { data } = await http.get('/session/quota', { timeout: 90000 })",
              "const { data } = await http.get('/session/quota', { timeout: 90000 })")
# Add saveCachedQuota after q is built
s = re.sub(r"return q\n\s*}\s*catch \(err\) \{",
           "saveCachedQuota(q)\n      return q\n    } catch (err) {", s, count=1)
# On error: use cache
s = s.replace(
  "// No local fallback; surface error to UI\n      if (axios.isAxiosError(err)) {",
  "// On error: return cached quota if valid; else surface error\n      const cached = loadCachedQuota()\n      if (cached) return cached\n      if (axios.isAxiosError(err)) {"
)

# Update translate to refresh quota cache when we have one
s = s.replace(
  "return data\n    } catch (err) {",
  "// sync tokens in cache if present\n      try {\n        const cached = loadCachedQuota()\n        if (cached && typeof data.magic_power_remaining === 'number') {\n          saveCachedQuota({ ...cached, tokens_remaining: data.magic_power_remaining })\n        }\n      } catch {}\n      return data\n    } catch (err) {"
)

p.write_text(s, encoding='utf-8')
print('patched', p)
