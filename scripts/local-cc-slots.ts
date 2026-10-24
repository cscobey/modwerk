// Development-only package compiler. No firmware inputs, device access or public assets.
import type { Plugin } from 'vite'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createHash } from 'node:crypto'

export function localCcSlots(): Plugin {
  return { name: 'local-cc-slots', apply: 'serve', configureServer(server) {
    server.middlewares.use('/__local/midi-cc-slots', async (req, res) => {
      res.setHeader('Cache-Control', 'no-store')
      res.setHeader('Content-Type', 'application/json')
      if (req.method !== 'GET') { res.statusCode = 405; res.end(JSON.stringify({ error: 'Use GET.' })); return }
      const work = await mkdtemp(join(tmpdir(), 'modwerk-cc-slots-'))
      try {
        const output = join(work, 'trial.mwrm')
        await promisify(execFile)('python3', ['-B', join(server.config.root, 'sdk/drafts/midi-cc-slots/build_runtime.py'), '--output', output], { timeout: 30000 })
        const data = await readFile(output)
        res.end(JSON.stringify({ version: '0.0.3-experimental', sha256: createHash('sha256').update(data).digest('hex'), hex: data.toString('hex') }))
      } catch {
        res.statusCode = 500
        res.end(JSON.stringify({ error: 'Could not compile the local draft. Start the app with the prepared Python and m68k-elf tools on PATH.' }))
      } finally { await rm(work, { recursive: true, force: true }) }
    })
  } }
}
