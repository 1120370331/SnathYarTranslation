from pathlib import Path
import re
p=Path('frontend/src/pages/TranslationPage.tsx')
s=p.read_text(encoding='utf-8')
pat=re.compile(r"setMagicPower\(prev => \(\{[\s\S]*?\}\)\)\s*\)\n\s*\n\s*// If quota unchanged, show ")
if not pat.search(s):
    # fallback: find the line and insert after
    anchor='setMagicPower(prev => ({\n      ...prev,\n      remaining: nextRemaining\n    }))\n\n'
    if anchor in s:
        s=s.replace(anchor, anchor+"    if (!magicPower.total || magicPower.total <= 0) {\n      apiClient.getQuota().then(q => {\n        setMagicPower({ remaining: q.tokens_remaining, total: q.daily_limit, resetTime: q.reset_time })\n      }).catch(() => {/* ignore; will retry later */})\n    }\n\n")
    else:
        raise SystemExit('anchor not found')
else:
    s=pat.sub("setMagicPower(prev => ({\\n      ...prev,\\n      remaining: nextRemaining\\n    }))\\n\\n    if (!magicPower.total || magicPower.total <= 0) {\\n      apiClient.getQuota().then(q => {\\n        setMagicPower({ remaining: q.tokens_remaining, total: q.daily_limit, resetTime: q.reset_time })\\n      }).catch(() => {/* ignore; will retry later */})\\n    }\\n\\n// If quota unchanged, show ", s, count=1)

p.write_text(s, encoding='utf-8')
print('patched', p)
