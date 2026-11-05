import { useEffect, useState } from 'react'
import { useI18n } from '../i18n'
import { FUELS, GEARBOXES } from '../data/cars'
import { Chip, Feed, Icon, usePaged, useApp } from '../ui'

const SORTS = [['new', 'sortNew'], ['found', 'sortFound'], ['cheap', 'sortCheap'], ['expensive', 'sortExpensive'], ['year', 'sortYear'], ['mileage', 'sortMileage']]
const lsGet = (k: string, d: string) => { try { return localStorage.getItem(k) ?? d } catch { return d } }
const lsSet = (k: string, v: string) => { try { localStorage.setItem(k, v) } catch { /* ignore */ } }

export function Catalog({ base, emptyTitle, emptyHint }: { base: Record<string, unknown>; emptyTitle?: string; emptyHint?: string }) {
  const { t } = useI18n()
  const [q, setQ] = useState('')
  const [dq, setDq] = useState('')
  const [sort, setSort] = useState(lsGet('sort', 'new'))
  const [view, setView] = useState<'cards' | 'list'>(lsGet('view', 'cards') as 'cards' | 'list')
  const [open, setOpen] = useState(false)
  const [f, setF] = useState<{ source: string; fuel: string; gearbox: string; price_min: string; price_max: string; year_min: string; year_max: string }>(
    { source: '', fuel: '', gearbox: '', price_min: '', price_max: '', year_min: '', year_max: '' })
  useEffect(() => { const h = setTimeout(() => setDq(q), 350); return () => clearTimeout(h) }, [q])
  const p = usePaged({ ...base, q: dq, sort, ...f })
  const active = Object.values(f).filter(Boolean).length
  const set = (k: keyof typeof f, v: string) => setF(x => ({ ...x, [k]: x[k] === v && (k === 'fuel' || k === 'gearbox' || k === 'source') ? '' : v }))

  return (
    <>
      <div className="row" style={{ marginBottom: 10 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input type="search" value={q} placeholder={t('search')} onChange={e => setQ(e.target.value)} style={{ paddingLeft: 36 }} />
          <span style={{ position: 'absolute', left: 11, top: 11, width: 18, color: 'var(--muted)' }}>{Icon.search}</span>
        </div>
        <button className={'icon-btn' + (active ? ' on' : '')} onClick={() => setOpen(!open)}>{Icon.filter}</button>
        <button className="icon-btn" onClick={() => { const v = view === 'cards' ? 'list' : 'cards'; setView(v); lsSet('view', v) }}
          title={view === 'cards' ? t('list') : t('cards')}>{view === 'cards' ? Icon.list : Icon.grid}</button>
      </div>
      <select value={sort} onChange={e => { setSort(e.target.value); lsSet('sort', e.target.value) }} style={{ marginBottom: 10 }}>
        {SORTS.map(([k, l]) => <option key={k} value={k}>{t(l)}</option>)}
      </select>
      {open && (
        <div className="card stack" style={{ marginBottom: 12 }}>
          <div><label className="f">{t('source')}</label><div className="chips">
            <Chip on={f.source === 'otomoto'} onClick={() => set('source', 'otomoto')}>OTOMOTO</Chip>
            <Chip on={f.source === 'olx'} onClick={() => set('source', 'olx')}>OLX</Chip></div></div>
          <div><label className="f">{t('fuel')}</label><div className="chips">{FUELS.map(x => <Chip key={x} on={f.fuel === x} onClick={() => set('fuel', x)}>{t(x)}</Chip>)}</div></div>
          <div><label className="f">{t('gearbox')}</label><div className="chips">{GEARBOXES.map(x => <Chip key={x} on={f.gearbox === x} onClick={() => set('gearbox', x)}>{t(x)}</Chip>)}</div></div>
          <div className="grid2">
            <div><label className="f">{t('priceFrom')}</label><input type="number" inputMode="numeric" value={f.price_min} onChange={e => set('price_min', e.target.value)} /></div>
            <div><label className="f">{t('priceTo')}</label><input type="number" inputMode="numeric" value={f.price_max} onChange={e => set('price_max', e.target.value)} /></div>
            <div><label className="f">{t('yearFrom')}</label><input type="number" inputMode="numeric" value={f.year_min} onChange={e => set('year_min', e.target.value)} /></div>
            <div><label className="f">{t('yearTo')}</label><input type="number" inputMode="numeric" value={f.year_max} onChange={e => set('year_max', e.target.value)} /></div>
          </div>
          <button className="btn ghost" onClick={() => setF({ source: '', fuel: '', gearbox: '', price_min: '', price_max: '', year_min: '', year_max: '' })}>{t('reset')}</button>
        </div>
      )}
      <Feed {...p} view={view} emptyTitle={emptyTitle ?? t('noResults')} emptyHint={emptyHint ?? t('noResultsHint')} />
    </>
  )
}

export default function Listings() {
  const { t } = useI18n()
  useApp()
  return <><div className="head"><h1>{t('listings')}</h1></div><Catalog base={{}} /></>
}
