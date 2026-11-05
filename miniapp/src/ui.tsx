import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import { ago, fmtMoney, fmtNum, useI18n } from './i18n'
import type { ListingCard } from './types'

// ---------- app context ----------
export type Page =
  | { k: 'detail'; id: number } | { k: 'compare' } | { k: 'filterForm'; id?: number } | { k: 'admin' }
  | { k: 'results'; filterId: number; name: string }
export interface AppCtx {
  push: (p: Page) => void; back: () => void; toast: (m: string) => void
  cmp: number[]; toggleCmp: (id: number) => void; clearCmp: () => void; setTab: (t: string) => void
}
export const App = createContext<AppCtx>(null as unknown as AppCtx)
export const useApp = () => useContext(App)

// ---------- icons ----------
const P = (d: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
)
export const Icon = {
  home: P('M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10'),
  list: P('M4 6h16M4 12h16M4 18h10'),
  filter: P('M3 5h18l-7 8v6l-4 2v-8L3 5z'),
  heart: P('M12 20s-7-4.4-9-9a5 5 0 019-3 5 5 0 019 3c-2 4.6-9 9-9 9z'),
  user: P('M20 21a8 8 0 10-16 0M12 12a4 4 0 100-8 4 4 0 000 8z'),
  plus: P('M12 5v14M5 12h14'), back: P('M15 18l-6-6 6-6'), grid: P('M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z'),
  compare: P('M8 3v18M16 3v18M4 8l4-5 4 5M12 16l4 5 4-5'), link: P('M10 14a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 10a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1'),
  ext: P('M14 4h6v6M20 4l-9 9M18 14v6H4V6h6'), eye: P('M3 3l18 18M10.6 6.1A9.8 9.8 0 0112 6c5 0 9 6 9 6a16 16 0 01-3.2 3.7M6.6 7.6A15 15 0 003 12s4 6 9 6c1.3 0 2.5-.3 3.6-.8'),
  trash: P('M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3'), edit: P('M4 20h4L19 9l-4-4L4 16v4zM13 7l4 4'),
  copy: P('M9 9h11v11H9zM5 15H4V4h11v1'), bell: P('M6 16V11a6 6 0 1112 0v5l2 2H4l2-2zM10 21h4'), play: P('M7 4l13 8-13 8z'),
  pause: P('M8 5v14M16 5v14'), search: P('M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5'),
}

export function Switch({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return <label className="switch"><input type="checkbox" checked={on} onChange={e => onChange(e.target.checked)} /><i /></label>
}

export function Chip({ on, onClick, children }: { on?: boolean; onClick?: () => void; children: ReactNode }) {
  return <button type="button" className={'chip' + (on ? ' on' : '')} onClick={onClick}>{children}</button>
}

export function Skeletons({ n = 3, h = 220 }: { n?: number; h?: number }) {
  return <div className="stack">{Array.from({ length: n }, (_, i) => <div key={i} className="sk" style={{ height: h }} />)}</div>
}

export function Empty({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return <div className="empty"><b>{title}</b>{hint}{action && <div style={{ marginTop: 16 }}>{action}</div>}</div>
}

export function ErrorBox({ msg, retry }: { msg: string; retry?: () => void }) {
  const { t } = useI18n()
  return <div className="empty"><b>{t('error')}</b><span className="small">{msg}</span>{retry && <div style={{ marginTop: 14 }}><button className="btn" onClick={retry}>{t('retry')}</button></div>}</div>
}

export function Modal({ children, onClose }: { children: ReactNode; onClose: () => void }) {
  return <div className="modal-bg" onClick={onClose}><div className="modal" onClick={e => e.stopPropagation()}>{children}</div></div>
}

export function Status({ state }: { state: string }) {
  const { t } = useI18n()
  return <span className={'status ' + state}><i />{t(state)}</span>
}

export function TagInput({ value, onChange, placeholder }: { value: string[]; onChange: (v: string[]) => void; placeholder: string }) {
  const [v, setV] = useState('')
  const add = () => { const s = v.trim(); if (s && !value.includes(s)) onChange([...value, s]); setV('') }
  return (
    <div>
      {value.length > 0 && <div className="chips" style={{ marginBottom: 8 }}>{value.map(x => (
        <span className="tag" key={x}>{x}<button type="button" onClick={() => onChange(value.filter(y => y !== x))}>×</button></span>))}</div>}
      <input type="text" value={v} placeholder={placeholder} onChange={e => setV(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} onBlur={add} />
    </div>
  )
}

// ---------- listing card / row ----------
function useCardState(item: ListingCard) {
  const app = useApp()
  const { t } = useI18n()
  const [fav, setFav] = useState(item.is_fav)
  useEffect(() => setFav(item.is_fav), [item.is_fav])
  const toggleFav = async (e: React.MouseEvent) => {
    e.stopPropagation()
    const next = !fav
    setFav(next)
    try { await (next ? api.addFav(item.id) : api.delFav(item.id)); app.toast(next ? t('addFav') : t('removeFav')) } catch { setFav(!next) }
  }
  return { fav, toggleFav, inCmp: app.cmp.includes(item.id), app }
}

export function specsOf(l: ListingCard, lang: ReturnType<typeof useI18n>['lang'], t: (k: string) => string) {
  return [l.year, l.mileage != null ? fmtNum(l.mileage, lang, 'km') : null, l.engine_cc ? fmtNum(l.engine_cc, lang, 'cm³') : null,
    l.power_hp ? l.power_hp + ' KM' : null, l.fuel ? t(l.fuel) : null, l.gearbox ? t(l.gearbox) : null].filter(Boolean)
}

export function ListingCardView({ item }: { item: ListingCard }) {
  const { t, lang } = useI18n()
  const { fav, toggleFav, inCmp, app } = useCardState(item)
  return (
    <div className={'lc' + (item.is_active ? '' : ' off')} onClick={() => app.push({ k: 'detail', id: item.id })}>
      <div className="img">
        {item.image && <img src={item.image} loading="lazy" alt="" />}
        {item.is_new && <span className="badge">{t('newBadge')}</span>}
        <span className="badge src">{item.source.toUpperCase()}</span>
        <button className={'icon-btn cmp' + (inCmp ? ' on' : '')} onClick={e => { e.stopPropagation(); app.toggleCmp(item.id) }}>{Icon.compare}</button>
        <button className={'icon-btn fav' + (fav ? ' on' : '')} onClick={toggleFav}>{Icon.heart}</button>
      </div>
      <div className="body">
        <div className="price">{fmtMoney(item.price, lang, item.currency)}</div>
        <div className="title">{item.title}</div>
        <div className="specs">{specsOf(item, lang, t).map((s, i) => <span key={i}>{s}</span>)}</div>
        <div className="specs" style={{ marginTop: 6 }}>
          <span>{item.city ?? '—'}</span><span>{ago(item.published_at ?? item.first_seen_at, lang)}</span>
          {!item.is_active && <span style={{ color: 'var(--bad)' }}>{t('unavailable')}</span>}
        </div>
      </div>
    </div>
  )
}

export function ListingRowView({ item }: { item: ListingCard }) {
  const { t, lang } = useI18n()
  const { fav, toggleFav, app } = useCardState(item)
  return (
    <div className="li" onClick={() => app.push({ k: 'detail', id: item.id })} style={item.is_active ? undefined : { opacity: .6 }}>
      {item.image ? <img className="th" src={item.image} loading="lazy" alt="" /> : <div className="th" />}
      <div className="mid">
        <div className="title">{item.title}</div>
        <div className="price">{fmtMoney(item.price, lang, item.currency)}</div>
        <div className="specs"><span>{specsOf(item, lang, t).slice(0, 3).join(' · ')}</span></div>
        <div className="specs"><span>{item.city ?? '—'} · {item.source.toUpperCase()} · {ago(item.published_at ?? item.first_seen_at, lang)}</span></div>
      </div>
      <button className={'icon-btn' + (fav ? ' on' : '')} style={{ alignSelf: 'center' }} onClick={toggleFav}>{Icon.heart}</button>
      {item.is_new && <span className="new" />}
    </div>
  )
}

// ---------- paged listing feed (shared by Listings, Favorites, Results) ----------
export function usePaged(params: Record<string, unknown>) {
  const key = JSON.stringify(params)
  const [items, setItems] = useState<ListingCard[]>([])
  const [more, setMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let dead = false
    setLoading(true); setError('')
    api.listings({ ...params, offset: 0, limit: 20 }).then(r => { if (!dead) { setItems(r.items); setMore(r.has_more) } })
      .catch(e => !dead && setError(e.message)).finally(() => !dead && setLoading(false))
    return () => { dead = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick])

  const loadMore = async () => {
    if (loading || !more) return
    setLoading(true)
    try { const r = await api.listings({ ...params, offset: items.length, limit: 20 }); setItems(x => [...x, ...r.items]); setMore(r.has_more) }
    catch (e: any) { setError(e.message) } finally { setLoading(false) }
  }
  return { items, more, loading, error, loadMore, reload: () => setTick(x => x + 1) }
}

export function Sentinel({ onVisible }: { onVisible: () => void }) {
  const [el, setEl] = useState<HTMLDivElement | null>(null)
  useEffect(() => {
    if (!el) return
    const io = new IntersectionObserver(es => es[0].isIntersecting && onVisible(), { rootMargin: '400px' })
    io.observe(el)
    return () => io.disconnect()
  })
  return <div ref={setEl} style={{ height: 1 }} />
}

export function Feed({ items, loading, error, more, loadMore, reload, view, emptyTitle, emptyHint }:
  { items: ListingCard[]; loading: boolean; error: string; more: boolean; loadMore: () => void; reload: () => void; view: 'cards' | 'list'; emptyTitle: string; emptyHint?: string }) {
  if (error && !items.length) return <ErrorBox msg={error} retry={reload} />
  if (loading && !items.length) return <Skeletons n={4} h={view === 'cards' ? 260 : 86} />
  if (!items.length) return <Empty title={emptyTitle} hint={emptyHint} />
  return (
    <>
      <div className={view === 'cards' ? 'cards' : 'stack'}>
        {items.map(i => view === 'cards' ? <ListingCardView key={i.id} item={i} /> : <ListingRowView key={i.id} item={i} />)}
      </div>
      {more && <Sentinel onVisible={loadMore} />}
      {loading && <div className="sk" style={{ height: 60, marginTop: 12 }} />}
    </>
  )
}
