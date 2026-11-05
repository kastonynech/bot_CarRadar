import raw from './cars.json'

// make -> models, slugs verified against OTOMOTO (scripts/verify_models.py)
export const CARS = raw as Record<string, string[]>

const SPECIAL: Record<string, string> = {
  bmw: 'BMW', 'mercedes-benz': 'Mercedes-Benz', mini: 'MINI', seat: 'SEAT', kia: 'Kia', 'alfa-romeo': 'Alfa Romeo',
  'land-rover': 'Land Rover', 'ds-automobiles': 'DS', cupra: 'CUPRA', 'cr-v': 'CR-V', 'hr-v': 'HR-V', 'c-hr': 'C-HR', 'rav4': 'RAV4',
  'x-trail': 'X-Trail', 'cx-5': 'CX-5', 'cx-3': 'CX-3', 'cx-30': 'CX-30', 'mx-5': 'MX-5', 'xc40': 'XC40', 'xc60': 'XC60',
  'xc70': 'XC70', 'xc90': 'XC90', 'f-pace': 'F-Pace', 's-max': 'S-Max', 'c-max': 'C-Max', 't-roc': 'T-Roc', 't-cross': 'T-Cross',
}
export const label = (slug: string) =>
  SPECIAL[slug] ?? slug.split('-').map(w => (/^\d/.test(w) || w.length <= 2 ? w.toUpperCase() : w[0].toUpperCase() + w.slice(1))).join(' ')

export const MAKES = Object.keys(CARS).sort()

export const REGIONS = ['Dolnośląskie', 'Kujawsko-pomorskie', 'Lubelskie', 'Lubuskie', 'Łódzkie', 'Małopolskie', 'Mazowieckie', 'Opolskie',
  'Podkarpackie', 'Podlaskie', 'Pomorskie', 'Śląskie', 'Świętokrzyskie', 'Warmińsko-mazurskie', 'Wielkopolskie', 'Zachodniopomorskie']
export const FUELS = ['petrol', 'diesel', 'lpg', 'petrol-lpg', 'hybrid', 'plug-in-hybrid', 'electric']
export const GEARBOXES = ['manual', 'automatic']
export const BODIES = ['sedan', 'combi', 'compact', 'suv', 'coupe', 'cabrio', 'minivan', 'city-car', 'small-cars']
