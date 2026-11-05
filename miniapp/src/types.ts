export interface NotifySettings {
  enabled: boolean; sources: string[]; photos: boolean; mode: 'instant' | 'digest'; digest_min: number
  price_alerts: boolean; night: { enabled: boolean; from: string; to: string }
}
export interface Me {
  id: number; username: string | null; lang: string; theme: 'dark' | 'light'; tz: string; created_at: string
  notify: NotifySettings; filters: number; favorites: number; found: number; is_admin: boolean
}
export interface ListingCard {
  id: number; source: string; title: string; make: string | null; model: string | null; price: number | null; currency: string
  year: number | null; mileage: number | null; engine_cc: number | null; power_hp: number | null; fuel: string | null
  gearbox: string | null; body: string | null; drive: string | null; city: string | null; region: string | null
  seller_type: string | null; url: string; image: string | null; published_at: string | null; first_seen_at: string
  is_active: boolean; is_new: boolean; is_fav: boolean; seller_name?: string | null
}
export interface ListingDetail extends ListingCard {
  images: string[]; description: string | null; vin: string | null; seller_name: string | null
  detail: null | {
    status: string; vin: string | null; body: string | null; drive: string | null; doors: string | null; seats: string | null
    color: string | null; damaged: string | null; service_record: string | null; new_used: string | null; imported: string | null
    details: { label: string; value: string }[]; equipment: { label: string; values: string[] }[]; address: string | null
  }
  display: Record<string, string>
  price_history: { price: number; at: string }[]
  filters: string[]; similar: ListingCard[]; possible_duplicates: ListingCard[]; last_checked_at: string | null
}
export interface FilterParams {
  make?: string | null; model?: string | null
  price_min?: number | null; price_max?: number | null; year_min?: number | null; year_max?: number | null
  mileage_min?: number | null; mileage_max?: number | null; engine_min?: number | null; engine_max?: number | null
  power_min?: number | null; power_max?: number | null
  fuel: string[]; gearbox: string[]; body: string[]; regions: string[]; cities: string[]
  seller: 'all' | 'private' | 'dealer'; with_photo: boolean
  exclude_words: string[]; exclude_models: string[]; exclude_fuel: string[]
}
export interface FilterDTO {
  id: number; name: string; sources: string[]; params: FilterParams; active: boolean; notify: boolean
  found_total: number; found_new: number; created_at: string
}
export interface ParserInfo { state: string; last_success_at: string | null; last_error: string | null }
export interface Dashboard {
  stats: { today: number; week: number; month: number }; active_filters: number; favorites: number
  latest: ListingCard[]; parsers: Record<string, ParserInfo>; last_update: string | null; interval: number
}
export interface AdminOverview {
  users: number; blocked: number; filters_active: number; filters_total: number; listings: number; listings_active: number
  notifications_sent: number; notifications_pending: number; notifications_failed: number; queries: number
  by_source: Record<string, number>; new_listings_1h: number; db_ping_ms: number; interval: number
  parsers: { source: string; state: string; last_success_at: string | null; last_error: string | null; requests: number; errors: number; paused_until: string | null }[]
  errors: { source: string; message: string; at: string }[]
}
export const emptyParams = (): FilterParams => ({
  fuel: [], gearbox: [], body: [], regions: [], cities: [], seller: 'all', with_photo: false,
  exclude_words: [], exclude_models: [], exclude_fuel: [],
})
