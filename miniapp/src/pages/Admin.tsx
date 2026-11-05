import { useEffect, useState } from 'react'
import { api } from '../api'
import { ago, fmtNum, useI18n } from '../i18n'
import type { AdminOverview } from '../types'
import { ErrorBox, Skeletons, Status, useApp } from '../ui'

export default function Admin() {
  const { t, lang } = useI18n()
  const app = useApp()
  const [o, setO] = useState<AdminOverview | null>(null)
  const [users, setUsers] = useState<Awaited<ReturnType<typeof api.admin.users>>>([])
  const [err, setErr] = useState('')
  const [iv, setIv] = useState('')
  const load = () => {
    api.admin.overview().then(x => { setO(x); setIv(v => v || String(x.interval)) }).catch(e => setErr(e.message))
    api.admin.users().then(setUsers).catch(() => undefined)
  }
  useEffect(() => { load(); const i = setInterval(load, 15000); return () => clearInterval(i) }, [])
  if (err) return <ErrorBox msg={err} retry={load} />
  if (!o) return <Skeletons n={3} h={100} />
  const stat = (k: string, v: number | string) => <div className="tile" key={k}><b style={{ fontSize: 22 }}>{typeof v === 'number' ? fmtNum(v, lang) : v}</b><span>{k}</span></div>
  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="head"><h1>{t('admin')}</h1></div>
      <div className="grid2">
        {stat(t('users'), o.users)}{stat(t('activeFilters'), o.filters_active)}{stat(t('listings'), o.listings)}{stat(t('queries'), o.queries)}
        {stat(t('sent'), o.notifications_sent)}{stat(t('pending'), o.notifications_pending)}{stat(t('failed'), o.notifications_failed)}{stat(t('newHour'), o.new_listings_1h)}
        {stat(t('db'), o.db_ping_ms + ' ms')}{stat(t('blockedUsers'), o.blocked)}
      </div>
      <div className="card stack">
        <b>{t('source')}</b>
        {Object.entries(o.by_source).map(([s, n]) => <div className="row between" key={s}><span>{s.toUpperCase()}</span><b>{fmtNum(n, lang)}</b></div>)}
      </div>
      <div className="card stack">
        <b>{t('monitoring')}</b>
        {o.parsers.map(p => (
          <div key={p.source} className="stack" style={{ gap: 4 }}>
            <div className="row between"><b>{p.source.toUpperCase()}</b><Status state={p.state} /></div>
            <div className="muted small">{t('lastUpdate')}: {ago(p.last_success_at, lang)} · {t('requests')}: {p.requests} · {t('errors')}: {p.errors}
              {p.paused_until && new Date(p.paused_until) > new Date() && <> · {t('pausedUntil')} {new Date(p.paused_until).toLocaleTimeString()}</>}</div>
            {p.last_error && <div className="small" style={{ color: 'var(--bad)' }}>{p.last_error}</div>}
            <button className="btn sm" onClick={async () => { await api.admin.restart(p.source); app.toast(t('saved')); load() }}>{t('restart')}</button>
          </div>))}
        <div className="hr" />
        <label className="f">{t('interval')}</label>
        <div className="row"><input type="number" min={15} max={3600} value={iv} onChange={e => setIv(e.target.value)} />
          <button className="btn primary" onClick={async () => { try { await api.admin.interval(Number(iv)); app.toast(t('saved')) } catch (e: any) { app.toast(e.message) } }}>{t('save')}</button></div>
      </div>
      <div className="card stack">
        <b>{t('users')}</b>
        {users.map(u => <div key={u.id} className="row between small"><span>{u.username ? '@' + u.username : u.id} <span className="muted">· {u.filters} {t('filters').toLowerCase()}</span></span>
          <button className="btn sm" onClick={async () => { try { await api.admin.block(u.id, !u.blocked); load() } catch (e: any) { app.toast(e.message) } }}>{u.blocked ? t('unblock') : t('block')}</button></div>)}
      </div>
      <div className="card stack">
        <b>{t('errors')}</b>
        {o.errors.length === 0 ? <span className="muted small">—</span> : o.errors.map((e, i) => <div key={i} className="small"><span className="muted">{ago(e.at, lang)} · {e.source}</span><br />{e.message}</div>)}
      </div>
    </div>
  )
}
