// Build responsive WebP variants for bg1.webp using sharp
// Inputs: frontend/resources/bg1.webp (preferred) or frontend/public/resources/bg1.webp (fallback)
// Outputs: frontend/public/resources/bg1-1440.webp, bg1-2560.webp (quality tuned)

import { mkdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

async function ensureDir(p) {
  try { await mkdir(p, { recursive: true }) } catch {}
}

async function exists(p) {
  try { await stat(p); return true } catch { return false }
}

async function main() {
  const __dirname = path.dirname(fileURLToPath(import.meta.url))
  const frontendDir = path.resolve(__dirname, '..')
  const srcPreferred = path.resolve(frontendDir, 'resources/bg1.webp')
  const srcFallback = path.resolve(frontendDir, 'public/resources/bg1.webp')
  const outDir = path.resolve(frontendDir, 'public/resources')

  const srcPath = (await exists(srcPreferred)) ? srcPreferred : srcFallback
  if (!(await exists(srcPath))) {
    console.error('[images] Source not found:', srcPath)
    process.exit(1)
  }

  // Lazy import sharp to fail fast if not installed
  let sharp
  try {
    sharp = (await import('sharp')).default
  } catch (e) {
    console.error('\n[images] Missing dependency: sharp')
    console.error('Run: npm i -D sharp')
    process.exit(1)
  }

  await ensureDir(outDir)

  const sizes = [
    { width: 1440, name: 'bg1-1440.webp', quality: 72 },
    { width: 2560, name: 'bg1-2560.webp', quality: 72 }
  ]

  const input = sharp(srcPath)
  const meta = await input.metadata()
  console.log(`[images] Source: ${srcPath} ${meta.width}x${meta.height}`)

  for (const s of sizes) {
    const outPath = path.resolve(outDir, s.name)
    const pipeline = sharp(srcPath).resize({ width: s.width, withoutEnlargement: true }).webp({ quality: s.quality })
    await pipeline.toFile(outPath)
    const bytes = (await stat(outPath)).size
    console.log(`[images] Wrote ${s.name} (${Math.round(bytes/1024)} KB)`)    
  }
}

main().catch(err => { console.error(err); process.exit(1) })
