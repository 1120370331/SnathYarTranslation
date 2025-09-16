// Minimal static file server for prebuilt React (Vite) app
// No external dependencies; suitable for runtime images.

import { createServer } from 'http'
import { readFile, stat } from 'fs/promises'
import { createReadStream } from 'fs'
import { extname, join, normalize } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const ROOT = normalize(join(__dirname, '..', 'dist'))

const PORT = process.env.PORT || process.env.FRONTEND_PORT || 1573
const HOST = process.env.HOST || process.env.FRONTEND_HOST || '0.0.0.0'

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.map': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
}

async function exists(p) {
  try { await stat(p); return true } catch { return false }
}

const server = createServer(async (req, res) => {
  try {
    const url = (req.url || '/').split('?')[0]
    let path = normalize(url)
    if (path.startsWith('..')) path = '/'
    let filePath = join(ROOT, path)

    // If path is a directory, serve index.html
    if (filePath.endsWith('/')) filePath = filePath + 'index.html'

    const hasFile = await exists(filePath)
    if (!hasFile) {
      // SPA fallback to index.html
      filePath = join(ROOT, 'index.html')
    }

    const ext = extname(filePath).toLowerCase()
    const ctype = MIME[ext] || 'application/octet-stream'
    res.statusCode = 200
    res.setHeader('Content-Type', ctype)
    createReadStream(filePath).pipe(res)
  } catch (e) {
    res.statusCode = 500
    res.setHeader('Content-Type', 'text/plain; charset=utf-8')
    res.end('Server error')
  }
})

server.listen(PORT, HOST, () => {
  console.log(`Frontend server listening on http://${HOST}:${PORT}`)
})

