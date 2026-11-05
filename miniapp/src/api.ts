import type { Dashboard, FilterDTO, ListingCard, ListingDetail, Me, AdminOverview } from './types'

export const tg = (window as any).Telegram?.WebApp

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const r = await fetch('/api' + url, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-Init-Data': tg?.initData ?? '' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = r.statusText
    try { const j = await r.json(); msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail) } catch { /* ignore */ }
    throw new ApiError(r.status, msg)
  }
  return r.json()
}

const qs = (o: Record<string, unknown>) => {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(o)) if (v !== undefined && v !== '' && v !== null && v !== false) p.set(k, String(v))
  return p.toString()
}

export const api = {
  me: () => req<Me>('GET', '/me'),
  patchMe: (b: Record<string, unknown>) => req('PATCH', '/me', b),
  dashboard: () => req<Dashboard>('GET', '/dashboard'),
  filters: () => req<FilterDTO[]>('GET', '/filters'),
  createFilter: (b: unknown) => req<FilterDTO>('POST', '/filters', b),
  updateFilter: (id: number, b: unknown) => req<FilterDTO>('PUT', `/filters/${id}`, b),
  patchFilter: (id: number, b: unknown) => req<FilterDTO>('PATCH', `/filters/${id}`, b),
  copyFilter: (id: number) => req<FilterDTO>('POST', `/filters/${id}/copy`),
  seenFilter: (id: number) => req('POST', `/filters/${id}/seen`),
  deleteFilter: (id: number) => req('DELETE', `/filters/${id}`),
  listings: (o: Record<string, unknown>) => req<{ items: ListingCard[]; has_more: boolean }>('GET', '/listings?' + qs(o)),
  listing: (id: number) => req<ListingDetail>('GET', `/listings/${id}`),
  addFav: (id: number) => req('PUT', `/favorites/${id}`),
  delFav: (id: number) => req('DELETE', `/favorites/${id}`),
  favHistory: () => req<Record<string, { price: number; at: string }[]>>('GET', '/favorites/history'),
  hide: (id: number) => req('PUT', `/hidden/${id}`),
  compare: (ids: number[]) => req<ListingCard[]>('GET', `/compare?ids=${ids.join(',')}`),
  admin: {
    overview: () => req<AdminOverview>('GET', '/admin/overview'),
    interval: (seconds: number) => req('POST', '/admin/interval', { seconds }),
    restart: (src: string) => req('POST', `/admin/restart/${src}`),
    users: () => req<{ id: number; username: string | null; lang: string; blocked: boolean; created_at: string; filters: number }[]>('GET', '/admin/users'),
    block: (id: number, blocked: boolean) => req('POST', `/admin/users/${id}/block?blocked=${blocked}`),
  },
}
