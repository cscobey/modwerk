import { afterEach, expect, it, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

afterEach(() => { vi.unstubAllEnvs(); vi.resetModules() })
async function local(enabled = true, dev = true) {
  vi.resetModules(); vi.stubEnv('DEV', dev); vi.stubEnv('MODE', 'development'); vi.stubEnv('VITE_LOCAL_CC_SLOTS', enabled ? '1' : '')
  return import('./local-cc-module')
}
it('requires both an explicit local opt-in and a development build', async () => {
  expect((await local(false)).localCcDocuments).toEqual([])
  expect((await local(true, false)).localCcPackages).toEqual([])
  expect((await local()).localCcPackages[0]).toMatchObject({ id: 'midi-cc-slots', name: 'Midi Mode 2', bytes: 33386, abi: 8, sites: 24, copies: 25 })
})
it('registers the local listing, source, artwork, real screenshots and installed runtime identity together', async () => {
  await local()
  const { MODULES, resolveSelection } = await import('../catalog/modules')
  const { MODULE_DOCUMENTS_BY_ID } = await import('../catalog/documents')
  const { inventoryFrom, runtimeId, USB_MODULE_IDS, moduleSetReview } = await import('../engine/elekloader/module-set')
  const { ModuleGrid } = await import('../components/ModuleGrid')
  const { ModuleAccess } = await import('../components/ModuleAccess')
  const { ModuleCard } = await import('../components/ModuleCard')
  const { ModuleDetail } = await import('../components/ModuleDetail')
  const { cardBuildError } = await import('../catalog/usb-only')
  const { newConfiguration, validateConfiguration } = await import('../config/workspace')
  const module = MODULES.find(m => m.id === 'midi-cc-slots')!
  expect(module.name).toBe('Midi Mode 2');expect(module.sourcePath).toContain('sdk/drafts/')
  expect(resolveSelection([module.id])).toEqual([module])
  expect(MODULE_DOCUMENTS_BY_ID[module.id].media).toHaveLength(8)
  expect(runtimeId(module.id)).toBe('f36a496d');expect(USB_MODULE_IDS).toContain(module.id)
  const inventory=inventoryFrom([{module:'f36a496d',name:'MIDI CC Slots',layout:1,handle:1}])
  expect(inventory.moduleIds).toEqual([module.id])
  const grid=renderToStaticMarkup(createElement(ModuleGrid,{ids:[module.id],inventory,describe:()=>module.detail,onOpen(){},onRemove(){},onKeep(){},onSaveUnit(){}}))
  expect(grid).toContain('Midi Mode 2');expect(grid).not.toContain('Not in the library')
  expect(grid).toContain('module-media/midi-cc-slots/0.0.13-experimental/presentation/thumbnail.svg')
  const access=renderToStaticMarkup(createElement(ModuleAccess,{id:module.id}))
  expect(access).toContain('media/03-control-1.png');expect(access).toContain('media/07-name-editor.png');expect(access).toContain('LEAD')
  const { moduleMediaGuide }=await import('../catalog/module-media-guides')
  const guide=moduleMediaGuide(module.id,module.version,MODULE_DOCUMENTS_BY_ID[module.id].media)
  expect(guide.primary).toHaveLength(5);expect(guide.additional).toHaveLength(3)
  expect(guide.primary.map(item=>item.path)).toContain('media/08-bank1-name.png')
  const card=renderToStaticMarkup(createElement(ModuleCard,{module,selected:false,baseline:null,compared:false,canCompare:true,onToggle(){},onCompare(){}}))
  expect(card).toContain('Local draft');expect(card).toContain('Add Midi Mode 2')
  const detail=renderToStaticMarkup(createElement(ModuleDetail,{module,selected:false,onToggle(){}}))
  expect(detail).toContain('Install through Sync to Octatrack');expect(detail).toContain('Add to ')
  expect(moduleSetReview({name:'Keep current',moduleIds:[module.id]},inventory).needsSync).toBe(false)
  expect(cardBuildError([module.id])).toContain('local USB draft')
  const saved=newConfiguration('Local MIDI',['miniverb',module.id])
  expect(validateConfiguration(JSON.parse(JSON.stringify(saved))).moduleIds).toEqual(saved.moduleIds)
})
it('reviews a single local add or removal, preserving companions and requiring the advertised loader capabilities', async () => {
  await local()
  const { moduleSetReview } = await import('../engine/elekloader/module-set')
  const current={moduleIds:['miniverb'],removedStockFx:[]}, target={name:'Local',moduleIds:['miniverb','midi-cc-slots']}
  const caps={abi:8,features:3,maxSites:24,maxCopies:25}
  expect(moduleSetReview(target,current,caps).changes).toMatchObject({add:['midi-cc-slots'],remove:[]})
  expect(moduleSetReview(target,current,caps).problem).toBeUndefined()
  expect(moduleSetReview(target,current,{...caps,maxCopies:7}).problem).toBeTruthy()
  expect(moduleSetReview({name:'Remove CC',moduleIds:['miniverb']},{...current,moduleIds:target.moduleIds},caps).changes).toMatchObject({add:[],remove:['midi-cc-slots']})
})
