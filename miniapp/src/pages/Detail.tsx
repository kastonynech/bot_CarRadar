import { useEffect, useState } from 'react'
import { api, tg } from '../api'
import { ago, fmtDate, fmtMoney, fmtNum, useI18n } from '../i18n'
import type { ListingDetail } from '../types'
import { ErrorBox, Icon, ListingCardView, Skeletons, useApp } from '../ui'

function Spark({ pts }: { pts: number[] }) {
  const min = Math.min(...pts), max = Math.max(...pts), span = max - min || 1
  const xy = pts.map((v, i) => `${(i / (pts.length - 1)) * 100},${56 - ((v - min) / span) * 48}`).join(' ')
  return <svg className="sparkline" viewBox="0 0 100 64" preserveAspectRatio="none"><polyline points={xy} fill="none" stroke="var(--accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>
}

export default function Detail({ id }: { id: number }) {
  const { t, lang } = useI18n()
  const app = useApp()
  const [d, setD] = useState<ListingDetail | null>(null)
  const [err, setErr] = useState('')
  const [fav, setFav] = useState(false)
  const load = () => { setErr(''); api.listing(id).then(x => { setD(x); setFav(x.is_fav) }).catch(e => setErr(e.message)) }
  useEffect(load, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (err) return <ErrorBox msg={err} retry={load} />
  if (!d) return <><Skeletons n={1} h={240} /><div className="muted small" style={{ marginTop: 12 }}>{t('loadingDetail')}</div></>
  const x = d.detail
  const rows: [string, string | null | undefined][] = [
    [t('year'), d.year?.toString()], [t('mileage'), d.mileage != null ? fmtNum(d.mileage, lang, 'km') : null],
    [t('engine'), d.engine_cc ? fmtNum(d.engine_cc, lang, 'cm³') : null], [t('power'), d.power_hp ? d.power_hp + ' KM' : null],
    [t('fuel'), d.fuel ? t(d.fuel) : null], [t('gearbox'), d.gearbox ? t(d.gearbox) : null],
    [t('body'), x?.body ?? d.body], [t('drive'), x?.drive ?? d.drive], [t('color'), x?.color], [t('doors'), x?.doors], [t('seats'), x?.seats],
    [t('damaged'), x?.damaged], [t('serviceRecord'), x?.service_record], [t('vin'), d.vin],
  ]
  const toggleFav = async () => {
    const n = !fav; setFav(n)
    try { await (n ? api.addFav(d.id) : api.delFav(d.id)) } catch { setFav(!n) }
  }
  const copy = async () => { try { await navigator.clipboard.writeText(d.url); app.toast(t('copied')) } catch { app.toast(d.url) } }
  const open = () => (tg?.openLink ? tg.openLink(d.url) : window.open(d.url, '_blank'))
  const ph = d.price_history
  const inCmp = app.cmp.includes(d.id)

  return (
    <div className="stack" style={{ gap: 14 }}>
      {d.images.length > 0 ? <div className={'gal' + (d.images.length === 1 ? ' one' : '')}>{d.images.map((u, i) => <img key={u} src={u} loading={i < 2 ? 'eager' : 'lazy'} alt="" />)}</div> : <div className="sk" style={{ height: 200 }} />}
      {d.images.length > 1 && <div className="muted small" style={{ marginTop: -6 }}>{d.images.length} foto</div>}
      {!d.is_active && <div className="banner">{t('unavailableAd')}</div>}
      <div>
        <div className="muted small">{d.source.toUpperCase()} · {t('published')}: {fmtDate(d.published_at, lang)} · {t('found')}: {fmtDate(d.first_seen_at, lang)}</div>
        <h1 style={{ margin: '6px 0' }}>{d.title}</h1>
        <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent)' }}>{fmtMoney(d.price, lang, d.currency)}</div>
      </div>

      <div className="actions">
        <button className={'btn' + (fav ? ' primary' : '')} onClick={toggleFav}>{Icon.heart} {fav ? t('removeFav') : t('addFav')}</button>
        <button className={'btn' + (inCmp ? ' primary' : '')} onClick={() => app.toggleCmp(d.id)}>{t('compare')}</button>
        <button className="btn" onClick={copy}>{t('copyLink')}</button>
        <button className="btn primary" onClick={open}>{t('openOriginal')} ↗</button>
        <button className="btn danger" onClick={async () => { await api.hide(d.id); app.toast(t('hidden')); app.back() }}>{t('hide')}</button>
      </div>

      <div><h2>{t('specs')}</h2>
        <div className="kv">{rows.filter(r => r[1]).map(([k, v]) => <div key={k}><span>{k}</span><b>{v}</b></div>)}</div></div>

      <div><h2>{t('priceHistory')}</h2>
        {ph.length > 1 ? <div className="card"><Spark pts={ph.map(p => p.price)} />
          {ph.map((p, i) => <div key={i} className="row between small" style={{ marginTop: 6 }}><span className="muted">{i === 0 ? t('initialPrice') : fmtDate(p.at, lang)}</span><b>{fmtMoney(p.price, lang)}</b></div>)}</div>
          : <div className="muted small">{t('noPriceChanges')}{ph[0] && <> · {t('initialPrice')}: {fmtMoney(ph[0].price, lang)}</>}</div>}</div>

      {d.description && <div><h2>{t('description')}</h2><div className="desc">{d.description}</div></div>}

      {x && x.equipment.length > 0 && <div><h2>{t('equipment')}</h2>
        {x.equipment.map(e => <div key={e.label} style={{ marginBottom: 10 }}><div className="muted small" style={{ marginBottom: 5 }}>{e.label}</div>
          <div className="chips">{e.values.map(v => <span key={v} className="chip static">{v}</span>)}</div></div>)}</div>}

      <div><h2>{t('seller')}</h2>
        <div className="kv">
          <div><span>{t('seller')}</span><b>{d.seller_name ?? '—'}</b></div>
          <div><span>&nbsp;</span><b>{d.seller_type ? t(d.seller_type) : '—'}</b></div>
          <div style={{ gridColumn: '1 / -1' }}><span>{t('location')}</span><b>{x?.address ?? [d.city, d.region].filter(Boolean).join(', ')}</b></div>
        </div></div>

      {d.filters.length > 0 && <div><h2>{t('matchedFilters')}</h2><div className="chips">{d.filters.map(f => <span key={f} className="chip static">{f}</span>)}</div></div>}
      {d.last_checked_at && <div className="muted small">{ago(d.last_checked_at, lang)}</div>}

      {d.possible_duplicates.length > 0 && <div><h2>{t('possibleDup')}</h2><div className="stack">{d.possible_duplicates.map(s => <ListingCardView key={s.id} item={s} />)}</div></div>}
      {d.similar.length > 0 && <div><h2>{t('similar')}</h2><div className="hscroll">{d.similar.map(s => <ListingCardView key={s.id} item={s} />)}</div></div>}
    </div>
  )
}
