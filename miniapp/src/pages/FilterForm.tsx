import { useEffect, useState } from 'react'
import { api } from '../api'
import { BODIES, CARS, FUELS, GEARBOXES, MAKES, REGIONS, label } from '../data/cars'
import { useI18n } from '../i18n'
import { emptyParams, type FilterParams } from '../types'
import { Chip, Skeletons, Switch, TagInput, useApp } from '../ui'

type NumKey = 'price' | 'year' | 'mileage' | 'engine' | 'power'
const toggle = (arr: string[], v: string) => (arr.includes(v) ? arr.filter(x => x !== v) : [...arr, v])
const num = (s: string) => (s === '' ? null : Math.max(0, Number(s)))

export default function FilterForm({ id }: { id?: number }) {
  const { t } = useI18n()
  const app = useApp()
  const [name, setName] = useState('')
  const [active, setActive] = useState(true)
  const [p, setP] = useState<FilterParams>(emptyParams())
  const [ready, setReady] = useState(!id)
  const [saving, setSaving] = useState(false)
  const [customModel, setCustomModel] = useState(false)

  useEffect(() => {
    if (!id) return
    api.filters().then(fs => {
      const f = fs.find(x => x.id === id)
      if (!f) return app.back()
      setName(f.name); setActive(f.active); setP({ ...emptyParams(), ...f.params })
      setCustomModel(!!f.params.make && !!f.params.model && !(CARS[f.params.make] ?? []).includes(f.params.model))
      setReady(true)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!ready) return <Skeletons n={4} h={100} />
  const set = <K extends keyof FilterParams>(k: K, v: FilterParams[K]) => setP(x => ({ ...x, [k]: v }))
  const range = (k: NumKey, lo: string, hi: string, step = 1) => (
    <div className="grid2">
      <input type="number" inputMode="numeric" step={step} value={(p as any)[`${k}_min`] ?? ''} placeholder={`${t('from')} ${lo}`.trim()}
        onChange={e => set(`${k}_min` as keyof FilterParams, num(e.target.value) as never)} />
      <input type="number" inputMode="numeric" step={step} value={(p as any)[`${k}_max`] ?? ''} placeholder={`${t('to')} ${hi}`.trim()}
        onChange={e => set(`${k}_max` as keyof FilterParams, num(e.target.value) as never)} />
    </div>
  )

  const autoName = () => [p.make && label(p.make), p.model && label(p.model), p.price_max != null && `≤ ${p.price_max} zł`].filter(Boolean).join(' ') || 'CarRadar'
  const save = async () => {
    setSaving(true)
    try {
      const body = { name: name.trim() || autoName(), sources: ['otomoto'], params: p, active }
      if (id) await api.updateFilter(id, body); else await api.createFilter(body)
      app.toast(t('saved')); app.back()
    } catch (e: any) { app.toast(e.message) } finally { setSaving(false) }
  }
  const models = p.make ? CARS[p.make] ?? [] : []

  return (
    <div className="stack" style={{ gap: 4 }}>
      <div className="head"><h1>{id ? t('editFilter') : t('newFilterTitle')}</h1></div>

      <h2>{t('sources')}</h2>
      <div className="chips"><Chip on>OTOMOTO</Chip><span className="chip static" style={{ opacity: .55 }}>OLX — {t('unavailable')}</span></div>
      <div className="muted small">{t('olxNote')}</div>

      <h2>{t('mainParams')}</h2>
      <div className="grid2">
        <div><label className="f">{t('make')}</label>
          <select value={p.make ?? ''} onChange={e => { set('make', e.target.value || null); set('model', null); setCustomModel(false) }}>
            <option value="">{t('anyMake')}</option>{MAKES.map(m => <option key={m} value={m}>{label(m)}</option>)}</select></div>
        <div><label className="f">{t('model')}</label>
          {customModel ? <input type="text" value={p.model ?? ''} placeholder="seria-3" onChange={e => set('model', e.target.value.trim().toLowerCase() || null)} />
            : <select value={p.model ?? ''} disabled={!p.make} onChange={e => { if (e.target.value === '__custom') { setCustomModel(true); set('model', null) } else set('model', e.target.value || null) }}>
              <option value="">{t('anyModel')}</option>{models.map(m => <option key={m} value={m}>{label(m)}</option>)}
              {p.make && <option value="__custom">{t('customModel')}…</option>}</select>}</div>
      </div>
      <label className="f" style={{ marginTop: 8 }}>{t('price')}, zł</label>{range('price', '0', '')}
      <label className="f" style={{ marginTop: 8 }}>{t('year')}</label>{range('year', '2010', '2025')}
      <label className="f" style={{ marginTop: 8 }}>{t('mileage')}, km</label>{range('mileage', '0', '', 1000)}
      <label className="f" style={{ marginTop: 8 }}>{t('engineCc')}</label>{range('engine', '1000', '', 100)}
      <label className="f" style={{ marginTop: 8 }}>{t('powerHp')}</label>{range('power', '0', '', 10)}
      <label className="f" style={{ marginTop: 8 }}>{t('fuel')}</label>
      <div className="chips">{FUELS.map(x => <Chip key={x} on={p.fuel.includes(x)} onClick={() => set('fuel', toggle(p.fuel, x))}>{t(x)}</Chip>)}</div>
      <label className="f" style={{ marginTop: 8 }}>{t('gearbox')}</label>
      <div className="chips">{GEARBOXES.map(x => <Chip key={x} on={p.gearbox.includes(x)} onClick={() => set('gearbox', toggle(p.gearbox, x))}>{t(x)}</Chip>)}</div>
      <label className="f" style={{ marginTop: 8 }}>{t('body')}</label>
      <div className="chips">{BODIES.map(x => <Chip key={x} on={p.body.includes(x)} onClick={() => set('body', toggle(p.body, x))}>{t(x)}</Chip>)}</div>

      <h2>{t('locationSec')}</h2>
      <label className="f">{t('voivodeship')} <span className="muted">({t('nationwide')})</span></label>
      <div className="chips">{REGIONS.map(x => <Chip key={x} on={p.regions.includes(x)} onClick={() => set('regions', toggle(p.regions, x))}>{x}</Chip>)}</div>
      <label className="f" style={{ marginTop: 8 }}>{t('cities')}</label>
      <TagInput value={p.cities} onChange={v => set('cities', v)} placeholder="Warszawa" />

      <h2>{t('sellerSec')}</h2>
      <div className="seg">{(['all', 'private', 'dealer'] as const).map(x => <button type="button" key={x} className={p.seller === x ? 'on' : ''} onClick={() => set('seller', x)}>{x === 'all' ? t('anySeller') : t(x)}</button>)}</div>

      <h2>{t('extras')}</h2>
      <div className="row between"><span>{t('withPhoto')}</span><Switch on={p.with_photo} onChange={v => set('with_photo', v)} /></div>
      <label className="f" style={{ marginTop: 10 }}>{t('excludeWords')}</label><TagInput value={p.exclude_words} onChange={v => set('exclude_words', v)} placeholder={t('addTag')} />
      <label className="f" style={{ marginTop: 10 }}>{t('excludeModels')}</label><TagInput value={p.exclude_models} onChange={v => set('exclude_models', v)} placeholder={t('addTag')} />
      <label className="f" style={{ marginTop: 10 }}>{t('excludeFuel')}</label>
      <div className="chips">{FUELS.map(x => <Chip key={x} on={p.exclude_fuel.includes(x)} onClick={() => set('exclude_fuel', toggle(p.exclude_fuel, x))}>{t(x)}</Chip>)}</div>
      <div className="hint" style={{ marginTop: 12 }}>{t('unsupported')}</div>

      <h2>{t('name')}</h2>
      <input type="text" value={name} placeholder={autoName()} maxLength={120} onChange={e => setName(e.target.value)} />
      <div className="row between" style={{ marginTop: 10 }}><span>{t('active')}</span><Switch on={active} onChange={setActive} /></div>

      <div className="form-end" />
      <div className="sticky-save row">
        <button className="btn block" onClick={() => app.back()}>{t('cancel')}</button>
        <button className="btn primary block" disabled={saving} onClick={save}>{t('save')}</button>
      </div>
    </div>
  )
}
