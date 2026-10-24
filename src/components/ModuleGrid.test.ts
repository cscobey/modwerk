import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, it, vi } from 'vitest'
import { sha } from '../../vendor/elekloader/kit/src/bytes'
import { inventoryFrom } from '../engine/elekloader/module-set'
import { ModuleGrid } from './ModuleGrid'

it('keeps the Octatrack module grid readable when its inventory includes an unlisted USB draft', () => {
  const draft = sha(new TextEncoder().encode('midi-cc-slots')).slice(0, 8)
  const inventory = inventoryFrom([{ module: draft, name: 'MIDI CC Slots', layout: 1, handle: 1 }])
  const html = renderToStaticMarkup(createElement(ModuleGrid, {
    ids: ['miniverb'], inventory, describe: () => 'Existing module',
    onOpen: vi.fn(), onRemove: vi.fn(), onKeep: vi.fn(), onSaveUnit: vi.fn(),
  }))
  expect(html).toContain('Existing module')
  expect(html).toContain(draft)
  expect(html).toContain('Not in the library')
  expect(html).toContain('Add modules')
  expect(html).not.toContain('/undefined/')
})
