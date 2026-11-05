import { useEffect, useState } from 'react'
import { api } from '../api'
import { ago, fmtNum, useI18n } from '../i18n'
import type { Dashboard } from '../types'
import { Empty, ErrorBox, Icon, ListingRowView, Skeletons, Status, useApp } from '../ui'

export default function Home() {
  const { t, lang } = useI18n()
  const app = useApp()
  const [d, setD] = useState<Dashboard | null>(null)
  const [err, setErr] = useState('')
  const load = () => api.dashboard().then(setD).catch(e => setErr(e.message))
  useEffect(() => { load(); const i = setInterval(load, 30000); return () => clearInterval(i) }, [])

  if (err && !d) return <ErrorBox msg={err} retry={load} />
  if (!d) return <><h1 style={{ marginBottom: 14 }}>CarRadar</h1><Skeletons n={3} h={110} /></>
  const max = Math.max(1, d.stats.month)
  const mon = d.parsers.otomoto?.state ?? 'unknown'
  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="head">
        <div><h1>CarRadar</h1><span className="status"><span className={'status ' + mon}><i />{t('monitoring')}: {t(mon)}</span></span></div>
        <button className="btn primary sm" onClick={() => app.push({ k: 'filterForm' })}>+ {t('newFilter')}</button>
      </div>

      <div className="grid2">
        <div className="tile hot"><b>{fmtNum(d.stats.today, lang)}</b><span>{t('newToday')}</span></div>
        <div className="tile"><b>{d.active_filters}</b><span>{t('activeFilters')}</span></div>
        <div className="tile"><b>{fmtNum(d.stats.week, lang)}</b><span>{t('foundWeek')}</span></div>
        <div className="tile"><b>{d.favorites}</b><span>{t('inFavorites')}</span></div>
      </div>

      <div className="card stack">
        <div className="row between"><b>{t('monitoring')}</b><span className="muted small">{t('lastUpdate')}: {ago(d.last_update, lang)}</span></div>
        {(['otomoto', 'olx'] as const).map(s => (
          <div className="row between" key={s}><b style={{ fontWeight: 600 }}>{s === 'olx' ? 'OLX' : 'OTOMOTO'}</b><Status state={d.parsers[s]?.state ?? 'unknown'} /></div>
        ))}
        <div className="muted small">{t('checksEvery', { n: d.interval })}</div>
        <div className="muted small">{t('olxNote')}</div>
      </div>

      <div>
        <div className="row between"><h2 style={{ margin: '4px 0 10px' }}>{t('latestFinds')}</h2>
          <button className="btn ghost sm" onClick={() => app.setTab('listings')}>{t('all')} →</button></div>
        {d.latest.length === 0 ? <Empty title={t('noResults')} hint={t('noResultsHint')} action={
          <button className="btn primary" onClick={() => app.push({ k: 'filterForm' })}>{Icon.plus} {t('newFilter')}</button>} />
          : <div className="stack">{d.latest.map(i => <ListingRowView key={i.id} item={i} />)}</div>}
      </div>

      <div className="card stack">
        <b>{t('statistics')}</b>
        {([['today', d.stats.today], ['week', d.stats.week], ['month', d.stats.month]] as const).map(([k, v]) => (
          <div key={k}><div className="row between small"><span className="muted">{t(k)}</span><b>{fmtNum(v, lang)}</b></div>
            <div className="bar" style={{ marginTop: 5 }}><div style={{ width: `${(v / max) * 100}%` }} /></div></div>
        ))}
      </div>
    </div>
  )
}
