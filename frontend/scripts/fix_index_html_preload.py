from pathlib import Path
p=Path('frontend/index.html')
html=p.read_text(encoding='utf-8')
lines=html.splitlines()
new_lines=[]
inserted=False
for i,line in enumerate(lines):
    # skip previous broken insertion containing backticks
    if 'DPR-aware preloads' in line or 'resources/bg1-1440.webp' in line and 'preload' in line:
        # skip old preload line(s) referencing bg1-1440
        if 'link' in line and 'preload' in line:
            continue
    if line.strip().startswith('</head>') and not inserted:
        new_lines.append('    <!-- DPR-aware preloads to avoid warning -->')
        new_lines.append('    <link rel="preload" as="image" href="resources/bg1-1440.webp" type="image/webp" media="(max-resolution: 191dpi)" fetchpriority="high" />')
        new_lines.append('    <link rel="preload" as="image" href="resources/bg1-2560.webp" type="image/webp" media="(min-resolution: 192dpi)" fetchpriority="high" />')
        inserted=True
    new_lines.append(line)
# Also remove stray literal `</head>` injected incorrectly with backticks
fixed='\n'.join(new_lines)
fixed=fixed.replace('<!-- DPR-aware preloads to avoid warning -->`n','')
fixed=fixed.replace('`n  </head>','')
p.write_text(fixed, encoding='utf-8')
print('fixed index.html')
