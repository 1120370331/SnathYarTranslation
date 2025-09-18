from pathlib import Path
import re
p=Path('frontend/src/services/api-client.ts')
s=p.read_text(encoding='utf-8')
block='''
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
    s = s.replace('export const apiClient = {', block + '\nexport const apiClient = {', 1)
else:
    pass
p.write_text(s, encoding='utf-8')
print('inserted helpers', p)
