import { useEffect, useState } from 'react'
import { api } from '../api'
import { fmtMoney, fmtNum, useI18n } from '../i18n'
import type { ListingCard } from '../types'
import { Empty, ErrorBox, Skeletons, useApp } from '../ui'

export default function Compare() {
  const { t, lang } = useI18n()
  const app = useApp()
  const [items, setItems] = useState<ListingCard[] | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    if (app.cmp.length < 2) { setItems([]); return }
    api.compare(app.cmp).then(setItems).catch(e => setErr(e.message))
  }, [app.cmp.join(',')]) // eslint-disable-line react-hooks/exhaustive-deps

  if (err) return <ErrorBox msg={err} />
  if (!items) return <Skeletons n={2} h={120} />
  if (items.length < 2) return <Empty title={t('compareTitle')} hint={t('pickTwo')} />

  type Row = { label: string; get: (l: ListingCard) => number | string | null; show: (l: ListingCard) => string; best?: 'min' | 'max' }
  const rows: Row[] = [
    { label: t('price'), get: l => l.price, show: l => fmtMoney(l.price, lang, l.currency), best: 'min' },
    { label: t('year'), get: l => l.year, show: l => l.year?.toString() ?? '—', best: 'max' },
    { label: t('mileage'), get: l => l.mileage, show: l => fmtNum(l.mileage, lang, 'km'), best: 'min' },
    { label: t('engine'), get: l => l.engine_cc, show: l => fmtNum(l.engine_cc, lang, 'cm³') },
    { label: t('power'), get: l => l.power_hp, show: l => (l.power_hp ? l.power_hp + ' KM' : '—'), best: 'max' },
    { label: t('fuel'), get: l => l.fuel, show: l => (l.fuel ? t(l.fuel) : '—') },
    { label: t('gearbox'), get: l => l.gearbox, show: l => (l.gearbox ? t(l.gearbox) : '—') },
    { label: t('drive'), get: l => l.drive, show: l => l.drive ?? '—' },
    { label: t('body'), get: l => l.body, show: l => l.body ?? '—' },
    { label: t('city'), get: l => l.city, show: l => l.city ?? '—' },
    { label: t('seller'), get: l => l.seller_name ?? l.seller_type, show: l => [l.seller_name, l.seller_type ? t(l.seller_type) : null].filter(Boolean).join(' · ') || '—' },
  ]
  return (
    <>
      <div className="head"><h1>{t('compareTitle')}</h1><button className="btn ghost sm" onClick={() => { app.clearCmp(); app.back() }}>{t('clear')}</button></div>
      <div className="cmp-wrap">
        <table className="cmp">
          <thead><tr><th />{items.map(l => (
            <th key={l.id} style={{ cursor: 'pointer' }} onClick={() => app.push({ k: 'detail', id: l.id })}>
              {l.image && <img src={l.image} alt="" style={{ width: '100%', borderRadius: 10, aspectRatio: '4/3', objectFit: 'cover' }} />}
              <div style={{ marginTop: 6, fontWeight: 600 }}>{l.title}</div></th>))}</tr></thead>
          <tbody>{rows.map(r => {
            const vals = items.map(r.get)
            const present = vals.filter(v => v != null) as (number | string)[]
            const differs = new Set(present.map(String)).size > 1
            let best: number | null = null
            if (r.best && differs) { const nums = present as number[]; best = r.best === 'min' ? Math.min(...nums) : Math.max(...nums) }
            return <tr key={r.label}><td>{r.label}</td>{items.map((l, i) => {
              const isBest = best != null && vals[i] === best
              return <td key={l.id} className={isBest ? 'best' : differs ? 'diff' : ''}>{r.show(l)}{isBest && ' ✓'}</td>
            })}</tr>
          })}</tbody>
        </table>
      </div>
      <div className="muted small" style={{ marginTop: 10 }}>✓ = {t('best')} · {t('limitNote')}</div>
    </>
  )
}
