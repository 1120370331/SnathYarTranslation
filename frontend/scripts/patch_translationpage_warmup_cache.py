from pathlib import Path
p=Path('frontend/src/pages/TranslationPage.tsx')
s=p.read_text(encoding='utf-8')
# Insert cached quota load and warmup on mount
anchor='// Initialize magic power from backend on mount'
if anchor in s and 'warmupBackend' not in s:
    s=s.replace("import { apiClient } from '../services/api-client'","import { apiClient, getCachedQuota, warmupBackend } from '../services/api-client'")
    s=s.replace(
        anchor+"\n  useEffect(() => {",
        anchor+"\n  useEffect(() => {\n    // Silent warm-up (Render free cold start)\n    try { warmupBackend() } catch {}\n\n    // Use cached quota immediately if present (1-day TTL)\n    try {\n      const cached = getCachedQuota && getCachedQuota()\n      if (cached) {\n        setMagicPower({ remaining: cached.tokens_remaining, total: cached.daily_limit, resetTime: cached.reset_time })\n      }\n    } catch {}\n"
    )
    # Remove toast.error on quota failure (silent)
    s=s.replace("      try {\n        toast.error('无法连接后端服务，请稍后重试 / Cannot connect to backend service')\n      } catch {}\n","      // silent warm-up: no toast on quota failure during cold start\n")
    p.write_text(s, encoding='utf-8')
    print('patched', p)
else:
    print('no change needed')
