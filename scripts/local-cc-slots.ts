// Development-only package compiler. No firmware inputs, device access or public assets.
import type { Plugin } from 'vite'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createHash } from 'node:crypto'

export function verifiedCcDocument(data: Uint8Array, verified: { version: string; sha256: string }) {
  const digest = createHash('sha256').update(data).digest('hex')
  if (digest !== verified.sha256) throw new Error('The source changed since the last local software verification.')
  return { version: verified.version, sha256: digest, hex: Buffer.from(data).toString('hex') }
}

export function localCcSlots(): Plugin {
  return { name: 'local-cc-slots', apply: 'serve', configureServer(server) {
    const mediaRoot = '/module-media/midi-cc-slots/0.0.4-experimental'
    const media = new Map<string, string>([
      ['presentation/thumbnail.svg', 'image/svg+xml'],
      ...['01-native-setup.png', '02-cc-setup.png', '03-control-1.png', '04-control-2.png', '05-native-restored.png'].map(file => ['media/' + file, 'image/png'] as const),
    ])
    server.middlewares.use(mediaRoot, async (req, res) => {
      const path = new URL(req.url ?? '/', 'http://localhost').pathname.slice(1), type = media.get(path)
      res.setHeader('Cache-Control', 'no-store')
      if (req.method !== 'GET' || !type) { res.statusCode = req.method === 'GET' ? 404 : 405; res.end(); return }
      try {
        const data = await readFile(join(server.config.root, 'sdk/drafts/midi-cc-slots', path))
        res.setHeader('Content-Type', type); res.end(data)
      } catch { res.statusCode = 404; res.end() }
    })
    server.middlewares.use('/__local/midi-cc-slots', async (req, res) => {
      res.setHeader('Cache-Control', 'no-store')
      res.setHeader('Content-Type', 'application/json')
      if (req.method !== 'GET') { res.statusCode = 405; res.end(JSON.stringify({ error: 'Use GET.' })); return }
      const path = new URL(req.url ?? '/', 'http://localhost').pathname
      if (path !== '/' && path !== '/package.mwrm') { res.statusCode = 404; res.end(JSON.stringify({ error: 'Unknown local draft route.' })); return }
      const work = await mkdtemp(join(tmpdir(), 'modwerk-cc-slots-'))
      try {
        const output = join(work, 'trial.mwrm')
        await promisify(execFile)('python3', ['-B', join(server.config.root, 'sdk/drafts/midi-cc-slots/build_runtime.py'), '--output', output], { timeout: 30000 })
        const data = await readFile(output)
        const approved = JSON.parse(await readFile(join(server.config.root, 'sdk/drafts/midi-cc-slots/local-build.json'), 'utf8')) as { version: string; sha256: string }
        const document = verifiedCcDocument(data, approved)
        if (path === '/package.mwrm') { res.setHeader('Content-Type', 'application/octet-stream'); res.end(data) }
        else res.end(JSON.stringify(document))
      } catch {
        res.statusCode = 500
        res.end(JSON.stringify({ error: 'Could not prepare the verified local draft. The source may have changed, or Python and m68k-elf tools are missing from PATH.' }))
      } finally { await rm(work, { recursive: true, force: true }) }
    })
  } }
}
