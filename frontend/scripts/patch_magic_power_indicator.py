from pathlib import Path
p=Path('frontend/src/components/MagicPowerIndicator.tsx')
s=p.read_text(encoding='utf-8')
# Replace percentage calculation
s=s.replace(
  'const percentage = total > 0 ? Math.round((remaining / total) * 100) : 0;',
  'const safeTotal = total > 0 ? total : 0;\n  const percentage = safeTotal > 0 ? Math.round((remaining / safeTotal) * 100) : 100;'
)
# Replace power level calc block by pattern
import re
s=re.sub(r"const getPowerLevelClass = \(\): string => \{[\s\S]*?\};",
  "const getPowerLevelClass = (): string => {\n    const safeTotal = total > 0 ? total : 0;\n    const ratio = safeTotal > 0 ? remaining / safeTotal : 1;\n    if (ratio >= 0.8) return 'high';\n    if (ratio >= 0.3) return 'medium';\n    return 'low';\n  };",
  s,
  count=1
)
# Replace header display of denominator
s=s.replace('{remaining}/{total}', "{remaining}/{total > 0 ? total : '—'}")
p.write_text(s, encoding='utf-8')
print('patched', p)
