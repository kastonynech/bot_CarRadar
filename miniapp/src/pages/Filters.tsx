import { useEffect, useState } from 'react'
import { api } from '../api'
import { CARS, label } from '../data/cars'
import { ago, fmtMoney, useI18n } from '../i18n'
import type { FilterDTO } from '../types'
import { Empty, ErrorBox, Icon, Modal, Skeletons, Switch, useApp } from '../ui'

export function summary(f: FilterDTO, t: (k: string) => string, lang: Parameters<typeof fmtMoney>[1]): string[] {
  const p = f.params
  const out: string[] = []
  if (p.make) out.push(label(p.make) + (p.model ? ' ' + label(p.model) : ''))
  if (p.price_min != null || p.price_max != null) out.push(`${p.price_min != null ? fmtMoney(p.price_min, lang) : '…'} – ${p.price_max != null ? fmtMoney(p.price_max, lang) : '…'}`)
  if (p.year_min != null || p.year_max != null) out.push(`${p.year_min ?? '…'}–${p.year_max ?? '…'}`)
  if (p.mileage_max != null) out.push(`≤ ${p.mileage_max.toLocaleString()} km`)
  if (p.engine_min != null || p.engine_max != null) out.push(`${p.engine_min ?? '…'}–${p.engine_max ?? '…'} cm³`)
  if (p.power_min != null || p.power_max != null) out.push(`${p.power_min ?? '…'}–${p.power_max ?? '…'} KM`)
  p.fuel.forEach(x => out.push(t(x))); p.gearbox.forEach(x => out.push(t(x))); p.body.forEach(x => out.push(t(x)))
  if (p.regions.length) out.push(p.regions.join(', '))
  if (p.cities.length) out.push(p.cities.join(', '))
  if (p.seller !== 'all') out.push(t(p.seller))
  if (p.exclude_words.length) out.push('− ' + p.exclude_words.join(', '))
  return out
}
void CARS

export default function Filters() {
  const { t, lang } = useI18n()
  const app = useApp()
  const [fs, setFs] = useState<FilterDTO[] | null>(null)
  const [err, setErr] = useState('')
  const [del, setDel] = useState<FilterDTO | null>(null)
  const load = () => api.filters().then(setFs).catch(e => setErr(e.message))
  useEffect(() => { load() }, [])

  const patch = async (f: FilterDTO, b: { active?: boolean; notify?: boolean }) => {
    setFs(x => x && x.map(y => y.id === f.id ? { ...y, ...b } : y))
    try { await api.patchFilter(f.id, b) } catch (e: any) { app.toast(e.message); load() }
  }
  if (err && !fs) return <ErrorBox msg={err} retry={load} />
  return (
    <>
      <div className="head"><h1>{t('filters')}</h1></div>
      {!fs ? <Skeletons n={3} h={130} /> : fs.length === 0 ? (
        <Empty title={t('noFilters')} hint={t('noFiltersHint')} action={<button className="btn primary" onClick={() => app.push({ k: 'filterForm' })}>{Icon.plus} {t('newFilter')}</button>} />
      ) : (
        <div className="stack">
          {fs.map(f => (
            <div className="card stack" key={f.id}>
              <div className="row between">
                <div style={{ minWidth: 0 }}><b style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.name}</b>
                  <span className="muted small">{f.active ? t('active') : t('paused')} · {t('created')} {ago(f.created_at, lang)}</span></div>
                <Switch on={f.active} onChange={v => patch(f, { active: v })} />
              </div>
              <div className="chips">{summary(f, t, lang).map((s, i) => <span key={i} className="chip static">{s}</span>)}</div>
              <div className="row between">
                <span className="small"><b>{f.found_total}</b> <span className="muted">{t('foundTotal')}</span>
                  {f.found_new > 0 && <> · <b style={{ color: 'var(--accent)' }}>{f.found_new}</b> <span className="muted">{t('foundNew')}</span></>}</span>
                <span className="row" style={{ gap: 6 }}>
                  <button className={'icon-btn' + (f.notify ? ' on' : '')} title={t('notifications')} onClick={() => patch(f, { notify: !f.notify })}>{Icon.bell}</button>
                  <button className="icon-btn" title={t('edit')} onClick={() => app.push({ k: 'filterForm', id: f.id })}>{Icon.edit}</button>
                  <button className="icon-btn" title={t('copy')} onClick={async () => { await api.copyFilter(f.id); load(); app.toast(t('saved')) }}>{Icon.copy}</button>
                  <button className="icon-btn" title={t('delete')} onClick={() => setDel(f)}>{Icon.trash}</button>
                </span>
              </div>
              <button className="btn ghost sm" onClick={() => { api.seenFilter(f.id); app.push({ k: 'results', filterId: f.id, name: f.name }) }}>{t('viewResults')} →</button>
            </div>
          ))}
        </div>
      )}
      <button className="btn primary fab" onClick={() => app.push({ k: 'filterForm' })}>{Icon.plus} {t('newFilter')}</button>
      {del && (
        <Modal onClose={() => setDel(null)}>
          <b style={{ fontSize: 17 }}>{t('confirmDelete')}</b>
          <p className="muted">{del.name}<br />{t('confirmDeleteText')}</p>
          <div className="row"><button className="btn block" onClick={() => setDel(null)}>{t('cancel')}</button>
            <button className="btn danger block" onClick={async () => { await api.deleteFilter(del.id); setDel(null); load() }}>{t('delete')}</button></div>
        </Modal>
      )}
    </>
  )
}
