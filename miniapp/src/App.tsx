import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, tg } from './api'
import { I18nCtx, makeT, type Lang } from './i18n'
import type { Me } from './types'
import { App as AppContext, Empty, ErrorBox, Icon, Skeletons, type AppCtx, type Page } from './ui'
import Admin from './pages/Admin'
import Compare from './pages/Compare'
import Detail from './pages/Detail'
import Favorites from './pages/Favorites'
import FilterForm from './pages/FilterForm'
import Filters from './pages/Filters'
import Home from './pages/Home'
import Listings, { Catalog } from './pages/Listings'
import Profile from './pages/Profile'

const TABS = [['home', 'home'], ['listings', 'list'], ['filters', 'filter'], ['favorites', 'heart'], ['profile', 'user']] as const
const lsGet = (k: string) => { try { return localStorage.getItem(k) } catch { return null } }
const lsSet = (k: string, v: string) => { try { localStorage.setItem(k, v) } catch { /* ignore */ } }

export default function Root() {
  const [me, setMe] = useState<Me | null>(null)
  const [err, setErr] = useState<{ status?: number; msg: string } | null>(null)
  const [tab, setTab] = useState<string>('home')
  const [stack, setStack] = useState<Page[]>([])
  const [cmp, setCmp] = useState<number[]>(() => { try { return JSON.parse(lsGet('cmp') ?? '[]') } catch { return [] } })
  const [toastMsg, setToastMsg] = useState('')
  const toastTimer = useRef<number>()

  const loadMe = useCallback(() => api.me().then(m => { setMe(m); setErr(null) }).catch(e => setErr({ status: e.status, msg: e.message })), [])
  useEffect(() => { tg?.ready?.(); tg?.expand?.(); loadMe() }, [loadMe])
  useEffect(() => { if (me) { document.documentElement.dataset.theme = me.theme; tg?.setHeaderColor?.(me.theme === 'dark' ? '#0e0f12' : '#f3f4f6'); tg?.setBackgroundColor?.(me.theme === 'dark' ? '#0e0f12' : '#f3f4f6') } }, [me?.theme]) // eslint-disable-line react-hooks/exhaustive-deps

  const back = useCallback(() => setStack(s => s.slice(0, -1)), [])
  useEffect(() => {
    const bb = tg?.BackButton
    if (!bb) return
    stack.length ? bb.show() : bb.hide()
    bb.onClick(back)
    return () => bb.offClick(back)
  }, [stack.length, back])
  useEffect(() => { window.scrollTo(0, 0) }, [stack.length, tab])

  const toast = useCallback((m: string) => { setToastMsg(m); window.clearTimeout(toastTimer.current); toastTimer.current = window.setTimeout(() => setToastMsg(''), 2000) }, [])
  const ctx: AppCtx = useMemo(() => ({
    push: p => setStack(s => [...s, p]), back, toast, cmp, setTab: t => { setStack([]); setTab(t) },
    toggleCmp: id => setCmp(c => { const n = c.includes(id) ? c.filter(x => x !== id) : [...c, id].slice(-4); lsSet('cmp', JSON.stringify(n)); return n }),
    clearCmp: () => { setCmp([]); lsSet('cmp', '[]') },
  }), [back, toast, cmp])

  const lang = (me?.lang ?? (['pl', 'ru', 'uk', 'en'].includes((tg?.initDataUnsafe?.user?.language_code ?? '').slice(0, 2)) ? tg.initDataUnsafe.user.language_code.slice(0, 2) : 'en')) as Lang
  const i18n = useMemo(() => ({ t: makeT(lang), lang }), [lang])
  const { t } = i18n

  if (err && !me) return (
    <I18nCtx.Provider value={i18n}><div className="app">
      {err.status === 401 ? <Empty title="CarRadar" hint={t('openInTelegram')} /> : <ErrorBox msg={err.msg} retry={loadMe} />}</div></I18nCtx.Provider>)
  if (!me) return <I18nCtx.Provider value={i18n}><div className="app"><Skeletons n={3} h={110} /></div></I18nCtx.Provider>

  const top = stack[stack.length - 1]
  let body
  if (top) {
    body = top.k === 'detail' ? <Detail key={top.id} id={top.id} />
      : top.k === 'compare' ? <Compare />
        : top.k === 'filterForm' ? <FilterForm id={top.id} />
          : top.k === 'admin' ? <Admin />
            : <><div className="head"><h1>{top.name}</h1></div><Catalog base={{ filter_id: top.filterId }} /></>
  } else {
    body = tab === 'home' ? <Home /> : tab === 'listings' ? <Listings /> : tab === 'filters' ? <Filters />
      : tab === 'favorites' ? <Favorites /> : <Profile me={me} reload={loadMe} />
  }

  return (
    <I18nCtx.Provider value={i18n}><AppContext.Provider value={ctx}>
      <div className="app" key={top ? JSON.stringify(top) : tab}>
        {top && !tg?.BackButton && <button className="btn ghost sm" style={{ marginBottom: 12 }} onClick={back}>{Icon.back}</button>}
        {body}
      </div>
      {cmp.length >= 2 && (top ? ['detail', 'results'].includes(top.k) : ['listings', 'favorites'].includes(tab)) && (
        <div className="cmp-bar"><div><b>{t('compareN', { n: cmp.length })}</b>
          <button className="btn primary sm" onClick={() => ctx.push({ k: 'compare' })}>{t('compare')}</button>
          <button className="icon-btn" onClick={ctx.clearCmp}>×</button></div></div>)}
      <nav className="nav"><div className="nav-in">{TABS.map(([k, icon]) => (
        <button key={k} className={!top && tab === k ? 'on' : ''} onClick={() => ctx.setTab(k)}>{Icon[icon]}<span>{t(k)}</span></button>))}</div></nav>
      {toastMsg && <div className="toast">{toastMsg}</div>}
    </AppContext.Provider></I18nCtx.Provider>
  )
}
