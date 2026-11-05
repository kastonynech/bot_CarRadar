import { useEffect, useState } from 'react'
import { api } from '../api'
import { fmtMoney, useI18n } from '../i18n'
import { Catalog } from './Listings'
import { Empty, useApp } from '../ui'

export default function Favorites() {
  const { t, lang } = useI18n()
  const app = useApp()
  const [hist, setHist] = useState<Record<string, { price: number; at: string }[]>>({})
  useEffect(() => { api.favHistory().then(setHist).catch(() => undefined) }, [])
  const changes = Object.entries(hist)
  return (
    <>
      <div className="head"><h1>{t('favorites')}</h1>
        {app.cmp.length >= 2 && <button className="btn primary sm" onClick={() => app.push({ k: 'compare' })}>{t('compareN', { n: app.cmp.length })}</button>}</div>
      {changes.length > 0 && (
        <div className="card stack" style={{ marginBottom: 12 }}>
          <b>{t('priceHistory')}</b>
          {changes.map(([id, h]) => {
            const first = h[0].price, last = h[h.length - 1].price
            return <div key={id} className="row between small" style={{ cursor: 'pointer' }} onClick={() => app.push({ k: 'detail', id: Number(id) })}>
              <span className="muted">#{id}</span>
              <span>{fmtMoney(first, lang)} → <b style={{ color: last < first ? 'var(--ok)' : 'var(--bad)' }}>{fmtMoney(last, lang)}</b> ({t(last < first ? 'priceDown' : 'priceUp')})</span></div>
          })}
        </div>
      )}
      <Catalog base={{ fav: true }} emptyTitle={t('noFavorites')} emptyHint={t('noFavoritesHint')} />
      {false && <Empty title="" />}
    </>
  )
}
