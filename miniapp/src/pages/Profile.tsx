import { useState } from 'react'
import { api } from '../api'
import { fmtDate, fmtNum, LANGS, useI18n, type Lang } from '../i18n'
import type { Me, NotifySettings } from '../types'
import { Switch, useApp } from '../ui'

const TZS = ['Europe/Warsaw', 'Europe/Kyiv', 'Europe/Moscow', 'Europe/Berlin', 'Europe/London', 'Europe/Vilnius', 'Europe/Prague', 'America/New_York', 'UTC']

export default function Profile({ me, reload }: { me: Me; reload: () => void }) {
  const { t, lang } = useI18n()
  const app = useApp()
  const [n, setN] = useState<NotifySettings>(me.notify)
  const save = async (b: Record<string, unknown>) => { try { await api.patchMe(b); reload() } catch (e: any) { app.toast(e.message) } }
  const setNotify = (patch: Partial<NotifySettings>) => { const next = { ...n, ...patch }; setN(next); save({ notify: patch }) }
  const tzs = TZS.includes(me.tz) ? TZS : [me.tz, ...TZS]
  const row = (label: string, ctl: React.ReactNode) => <div className="row between"><span>{label}</span>{ctl}</div>

  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="head"><h1>{t('profile')}</h1></div>
      <div className="card">
        <div className="row"><div className="tile hot" style={{ width: 52, height: 52, padding: 0, display: 'grid', placeItems: 'center', borderRadius: 16 }}><b style={{ fontSize: 22 }}>{(me.username ?? 'U')[0].toUpperCase()}</b></div>
          <div><b>{me.username ? '@' + me.username : 'Telegram'}</b><div className="muted small">{t('telegramId')}: {me.id}</div></div></div>
        <div className="hr" />
        <div className="grid2">
          <div><div className="muted small">{t('registered')}</div><b>{fmtDate(me.created_at, lang)}</b></div>
          <div><div className="muted small">{t('filters')}</div><b>{me.filters}</b></div>
          <div><div className="muted small">{t('carsFound')}</div><b>{fmtNum(me.found, lang)}</b></div>
          <div><div className="muted small">{t('favorites')}</div><b>{me.favorites}</b></div>
        </div>
      </div>

      <div className="card stack">
        <div><label className="f">{t('language')}</label>
          <select value={me.lang} onChange={e => save({ lang: e.target.value as Lang })}>{LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}</select></div>
        <div><label className="f">{t('theme')}</label>
          <div className="seg">{(['dark', 'light'] as const).map(x => <button key={x} className={me.theme === x ? 'on' : ''} onClick={() => save({ theme: x })}>{t(x)}</button>)}</div></div>
        <div><label className="f">{t('timezone')}</label>
          <select value={me.tz} onChange={e => save({ tz: e.target.value })}>{tzs.map(z => <option key={z}>{z}</option>)}</select></div>
      </div>

      <div className="card stack">
        <b>{t('notifSettings')}</b>
        {row(t('notifEnabled'), <Switch on={n.enabled} onChange={v => setNotify({ enabled: v })} />)}
        <div><label className="f">{t('sources')}</label><div className="chips">
          {(['otomoto', 'olx'] as const).map(s => <button key={s} className={'chip' + (n.sources.includes(s) ? ' on' : '')}
            onClick={() => setNotify({ sources: n.sources.includes(s) ? n.sources.filter(x => x !== s) : [...n.sources, s] })}>{s.toUpperCase()}</button>)}</div></div>
        {row(t('notifPhotos'), <Switch on={n.photos} onChange={v => setNotify({ photos: v })} />)}
        {row(t('priceAlerts'), <Switch on={n.price_alerts} onChange={v => setNotify({ price_alerts: v })} />)}
        <div><label className="f">{t('notifMode')}</label>
          <div className="seg">{(['instant', 'digest'] as const).map(x => <button key={x} className={n.mode === x ? 'on' : ''} onClick={() => setNotify({ mode: x })}>{t(x)}</button>)}</div></div>
        {n.mode === 'digest' && <div><label className="f">{t('digestEvery')}</label>
          <input type="number" min={15} max={1440} value={n.digest_min} onChange={e => setN({ ...n, digest_min: Number(e.target.value) })} onBlur={() => save({ notify: { digest_min: n.digest_min } })} /></div>}
        {row(t('night'), <Switch on={n.night.enabled} onChange={v => setNotify({ night: { ...n.night, enabled: v } })} />)}
        {n.night.enabled && <div className="grid2">
          <div><label className="f">{t('nightFrom')}</label><input type="time" value={n.night.from} onChange={e => setNotify({ night: { ...n.night, from: e.target.value } })} /></div>
          <div><label className="f">{t('nightTo')}</label><input type="time" value={n.night.to} onChange={e => setNotify({ night: { ...n.night, to: e.target.value } })} /></div></div>}
      </div>

      <div className="card"><b>{t('monitoringSettings')}</b><div className="muted small" style={{ marginTop: 6 }}>{t('checksEvery', { n: '60' })}<br />{t('olxNote')}</div></div>
      {me.is_admin && <button className="btn primary" onClick={() => app.push({ k: 'admin' })}>{t('admin')}</button>}
    </div>
  )
}
