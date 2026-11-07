import { createContext, useContext } from 'react'

export type Lang = 'pl' | 'ru' | 'uk' | 'en'
export const LANGS: { code: Lang; label: string }[] = [
  { code: 'pl', label: 'Polski' }, { code: 'ru', label: 'Русский' }, { code: 'uk', label: 'Українська' }, { code: 'en', label: 'English' },
]

type Dict = Record<string, string>
const en: Dict = {
  home: 'Home', listings: 'Listings', filters: 'Filters', favorites: 'Favorites', profile: 'Profile',
  today: 'Today', week: '7 days', month: '30 days', newToday: 'New today', activeFilters: 'Active filters', foundWeek: 'Found this week',
  inFavorites: 'In favorites', latestFinds: 'Latest finds', all: 'All', monitoring: 'Monitoring', lastUpdate: 'Last update',
  checksEvery: 'Checked about every {n} s (polling, not real-time)', statistics: 'Statistics', newFilter: 'New filter',
  ok: 'Working', degraded: 'Degraded', blocked: 'Blocked by site', schema_changed: 'Site layout changed', unknown: 'No data yet',
  unavailable: 'Unavailable', olxNote: 'OLX blocks automated access, so it is not monitored.',
  search: 'Search…', sortNew: 'Newest first', sortFound: 'Recently found', sortCheap: 'Cheapest first', sortExpensive: 'Most expensive first',
  sortYear: 'By year', sortMileage: 'By mileage', cards: 'Cards', list: 'List', source: 'Source', fuel: 'Fuel', gearbox: 'Gearbox',
  priceFrom: 'Price from', priceTo: 'Price to', yearFrom: 'Year from', yearTo: 'Year to', reset: 'Reset', apply: 'Apply',
  noResults: 'Nothing here yet', noResultsHint: 'New cars matching your filters will appear here as soon as they are found.',
  newBadge: 'NEW', published: 'Published', found: 'Found', unavailableAd: 'No longer available on the site',
  addFav: 'Add to favorites', removeFav: 'Remove from favorites', compare: 'Compare', copyLink: 'Copy link', copied: 'Link copied',
  openOriginal: 'Open original', hide: 'Hide', hidden: 'Hidden', specs: 'Specifications', equipment: 'Equipment', description: 'Description',
  seller: 'Seller', location: 'Location', private: 'Private', dealer: 'Dealer', priceHistory: 'Price history', noPriceChanges: 'No price changes seen yet',
  initialPrice: 'First seen', similar: 'Similar cars', possibleDup: 'Possible duplicate on another site', matchedFilters: 'Matched filters',
  loadingDetail: 'Loading full ad…', mileage: 'Mileage', year: 'Year', engine: 'Engine', power: 'Power', price: 'Price', drive: 'Drive', body: 'Body',
  city: 'City', vin: 'VIN', color: 'Color', doors: 'Doors', seats: 'Seats', damaged: 'Damaged', serviceRecord: 'Service history',
  compareTitle: 'Comparison', compareN: 'Compare ({n})', clear: 'Clear', best: 'best', pickTwo: 'Pick at least 2 cars to compare.',
  newFilterTitle: 'New filter', editFilter: 'Edit filter', name: 'Name', autoName: 'Name (optional)', sources: 'Sources', mainParams: 'Car',
  make: 'Make', model: 'Model', anyMake: 'Any make', anyModel: 'Any model', customModel: 'Other model (OTOMOTO slug)', from: 'From', to: 'To',
  engineCc: 'Engine, cm³', powerHp: 'Power, KM', locationSec: 'Location', voivodeship: 'Voivodeship', cities: 'Cities (add and press Enter)',
  nationwide: 'All of Poland', sellerSec: 'Seller', anySeller: 'Any', extras: 'Extras', withPhoto: 'Only with photos',
  excludeWords: 'Exclude words', excludeModels: 'Exclude models', excludeFuel: 'Exclude fuel', addTag: 'Add and press Enter',
  unsupported: 'Doors, color, equipment, origin and similar parameters are not present in the source listing feed, so they are not offered as filters (no guessing).',
  save: 'Save', cancel: 'Cancel', delete: 'Delete', edit: 'Edit', copy: 'Copy', confirmDelete: 'Delete this filter?', confirmDeleteText: 'Matches already found stay in the catalog.',
  active: 'Active', paused: 'Paused', foundTotal: 'found', foundNew: 'new', viewResults: 'Results', notifications: 'Notifications',
  noFilters: 'No filters yet', noFiltersHint: 'Create a filter and CarRadar will watch for new cars for you.', created: 'Created',
  noFavorites: 'No favorites yet', noFavoritesHint: 'Tap the heart on a car to save it here.', added: 'Added',
  priceDown: 'price dropped', priceUp: 'price rose',
  telegramId: 'Telegram ID', registered: 'Registered', carsFound: 'Cars found', language: 'Language', theme: 'Theme', dark: 'Dark', light: 'Light',
  timezone: 'Time zone', notifSettings: 'Notifications', notifEnabled: 'Notifications enabled', notifPhotos: 'Photos in notifications',
  notifMode: 'Delivery', instant: 'Instantly', digest: 'Digest', digestEvery: 'Digest every (min)', night: 'Quiet hours', nightFrom: 'From', nightTo: 'To',
  priceAlerts: 'Price change alerts', monitoringSettings: 'Monitoring', admin: 'Admin panel', error: 'Something went wrong', retry: 'Retry',
  openInTelegram: 'Open CarRadar from the Telegram bot.', saved: 'Saved', dupFilter: 'A preset with these parameters already exists. Replace it?', users: 'Users', blockedUsers: 'Blocked', queries: 'Polled queries',
  sent: 'Sent', pending: 'Pending', failed: 'Failed', errors: 'Errors', restart: 'Restart', interval: 'Check interval, s', block: 'Block', unblock: 'Unblock',
  total: 'total', requests: 'Requests', db: 'DB response', newHour: 'New listings / hour', pausedUntil: 'Paused until', limitNote: 'Use up to 4 cars',
  petrol: 'Petrol', diesel: 'Diesel', lpg: 'LPG', 'petrol-lpg': 'Petrol + LPG', hybrid: 'Hybrid', 'plug-in-hybrid': 'Plug-in hybrid', electric: 'Electric',
  manual: 'Manual', automatic: 'Automatic', sedan: 'Sedan', combi: 'Estate', compact: 'Hatchback', suv: 'SUV', coupe: 'Coupe', cabrio: 'Cabrio',
  minivan: 'Minivan', 'city-car': 'City car', 'small-cars': 'Small car',
}
const ru: Dict = {
  home: 'Главная', listings: 'Объявления', filters: 'Фильтры', favorites: 'Избранное', profile: 'Профиль',
  today: 'Сегодня', week: '7 дней', month: '30 дней', newToday: 'Новых сегодня', activeFilters: 'Активных фильтров', foundWeek: 'Найдено за неделю',
  inFavorites: 'В избранном', latestFinds: 'Последние находки', all: 'Все', monitoring: 'Мониторинг', lastUpdate: 'Последнее обновление',
  checksEvery: 'Проверка примерно раз в {n} с (опрос, не реальное время)', statistics: 'Статистика', newFilter: 'Новый фильтр',
  ok: 'Работает', degraded: 'Сбои', blocked: 'Заблокирован сайтом', schema_changed: 'Изменилась вёрстка сайта', unknown: 'Пока нет данных',
  unavailable: 'Недоступен', olxNote: 'OLX блокирует автоматический доступ, поэтому не отслеживается.',
  search: 'Поиск…', sortNew: 'Сначала новые', sortFound: 'По времени обнаружения', sortCheap: 'Сначала дешёвые', sortExpensive: 'Сначала дорогие',
  sortYear: 'По году выпуска', sortMileage: 'По пробегу', cards: 'Карточки', list: 'Список', source: 'Источник', fuel: 'Топливо', gearbox: 'Коробка',
  priceFrom: 'Цена от', priceTo: 'Цена до', yearFrom: 'Год от', yearTo: 'Год до', reset: 'Сбросить', apply: 'Применить',
  noResults: 'Пока ничего нет', noResultsHint: 'Новые авто по вашим фильтрам появятся здесь, как только будут найдены.',
  newBadge: 'НОВОЕ', published: 'Опубликовано', found: 'Найдено', unavailableAd: 'Объявление больше недоступно на площадке',
  addFav: 'В избранное', removeFav: 'Убрать из избранного', compare: 'Сравнить', copyLink: 'Скопировать ссылку', copied: 'Ссылка скопирована',
  openOriginal: 'Открыть оригинал', hide: 'Скрыть', hidden: 'Скрыто', specs: 'Характеристики', equipment: 'Оснащение', description: 'Описание',
  seller: 'Продавец', location: 'Местоположение', private: 'Частное лицо', dealer: 'Автосалон', priceHistory: 'История цены', noPriceChanges: 'Изменений цены пока не замечено',
  initialPrice: 'Первая цена', similar: 'Похожие автомобили', possibleDup: 'Возможный дубликат на другой площадке', matchedFilters: 'Подошло под фильтры',
  loadingDetail: 'Загружаю полное объявление…', mileage: 'Пробег', year: 'Год', engine: 'Двигатель', power: 'Мощность', price: 'Цена', drive: 'Привод', body: 'Кузов',
  city: 'Город', vin: 'VIN', color: 'Цвет', doors: 'Двери', seats: 'Места', damaged: 'Повреждения', serviceRecord: 'Сервисная история',
  compareTitle: 'Сравнение', compareN: 'Сравнить ({n})', clear: 'Очистить', best: 'лучшее', pickTwo: 'Выберите минимум 2 автомобиля для сравнения.',
  newFilterTitle: 'Новый фильтр', editFilter: 'Редактирование', name: 'Название', autoName: 'Название (необязательно)', sources: 'Источники', mainParams: 'Автомобиль',
  make: 'Марка', model: 'Модель', anyMake: 'Любая марка', anyModel: 'Любая модель', customModel: 'Другая модель (slug как в OTOMOTO)', from: 'От', to: 'До',
  engineCc: 'Объём, см³', powerHp: 'Мощность, KM', locationSec: 'Местоположение', voivodeship: 'Воеводство', cities: 'Города (введите и нажмите Enter)',
  nationwide: 'Вся Польша', sellerSec: 'Продавец', anySeller: 'Все', extras: 'Дополнительно', withPhoto: 'Только с фотографиями',
  excludeWords: 'Исключить слова', excludeModels: 'Исключить модели', excludeFuel: 'Исключить топливо', addTag: 'Введите и нажмите Enter',
  unsupported: 'Двери, цвет, оснащение, страна происхождения и подобные параметры не приходят в ленте объявлений источника, поэтому не предлагаются как фильтры (без выдумывания).',
  save: 'Сохранить', cancel: 'Отмена', delete: 'Удалить', edit: 'Изменить', copy: 'Копировать', confirmDelete: 'Удалить фильтр?', confirmDeleteText: 'Уже найденные объявления останутся в каталоге.',
  active: 'Активен', paused: 'Выключен', foundTotal: 'найдено', foundNew: 'новых', viewResults: 'Результаты', notifications: 'Уведомления',
  noFilters: 'Фильтров пока нет', noFiltersHint: 'Создайте фильтр, и CarRadar будет следить за новыми авто за вас.', created: 'Создан',
  noFavorites: 'Избранное пусто', noFavoritesHint: 'Нажмите на сердечко у автомобиля, чтобы сохранить его здесь.', added: 'Добавлено',
  priceDown: 'цена снизилась', priceUp: 'цена выросла',
  telegramId: 'Telegram ID', registered: 'Дата регистрации', carsFound: 'Найдено авто', language: 'Язык', theme: 'Тема', dark: 'Тёмная', light: 'Светлая',
  timezone: 'Часовой пояс', notifSettings: 'Уведомления', notifEnabled: 'Уведомления включены', notifPhotos: 'Фото в уведомлениях',
  notifMode: 'Доставка', instant: 'Сразу', digest: 'Подборкой', digestEvery: 'Подборка раз в (мин)', night: 'Тихие часы', nightFrom: 'С', nightTo: 'До',
  priceAlerts: 'Уведомления об изменении цены', monitoringSettings: 'Мониторинг', admin: 'Админ-панель', error: 'Что-то пошло не так', retry: 'Повторить',
  openInTelegram: 'Откройте CarRadar через Telegram-бота.', saved: 'Сохранено', dupFilter: 'Такой пресет уже есть. Заменить его?', users: 'Пользователи', blockedUsers: 'Заблокировано', queries: 'Опрашиваемых запросов',
  sent: 'Отправлено', pending: 'В очереди', failed: 'Ошибки', errors: 'Ошибки', restart: 'Перезапуск', interval: 'Интервал проверки, с', block: 'Заблокировать', unblock: 'Разблокировать',
  total: 'всего', requests: 'Запросы', db: 'Отклик БД', newHour: 'Новых объявлений / час', pausedUntil: 'Пауза до', limitNote: 'До 4 автомобилей',
  petrol: 'Бензин', diesel: 'Дизель', lpg: 'LPG', 'petrol-lpg': 'Бензин + LPG', hybrid: 'Гибрид', 'plug-in-hybrid': 'Плагин-гибрид', electric: 'Электро',
  manual: 'Механика', automatic: 'Автомат', sedan: 'Седан', combi: 'Универсал', compact: 'Хэтчбек', suv: 'SUV', coupe: 'Купе', cabrio: 'Кабриолет',
  minivan: 'Минивэн', 'city-car': 'Городской', 'small-cars': 'Малолитражка',
}
const pl: Dict = {
  home: 'Start', listings: 'Ogłoszenia', filters: 'Filtry', favorites: 'Ulubione', profile: 'Profil',
  today: 'Dzisiaj', week: '7 dni', month: '30 dni', newToday: 'Nowe dzisiaj', activeFilters: 'Aktywne filtry', foundWeek: 'Znalezione w tygodniu',
  inFavorites: 'W ulubionych', latestFinds: 'Ostatnie znaleziska', all: 'Wszystkie', monitoring: 'Monitoring', lastUpdate: 'Ostatnia aktualizacja',
  checksEvery: 'Sprawdzanie ok. co {n} s (odpytywanie, nie czas rzeczywisty)', statistics: 'Statystyki', newFilter: 'Nowy filtr',
  ok: 'Działa', degraded: 'Problemy', blocked: 'Zablokowany przez serwis', schema_changed: 'Zmienił się układ strony', unknown: 'Brak danych',
  unavailable: 'Niedostępny', olxNote: 'OLX blokuje automatyczny dostęp, dlatego nie jest monitorowany.',
  search: 'Szukaj…', sortNew: 'Najnowsze', sortFound: 'Ostatnio znalezione', sortCheap: 'Najtańsze', sortExpensive: 'Najdroższe',
  sortYear: 'Wg roku', sortMileage: 'Wg przebiegu', cards: 'Karty', list: 'Lista', source: 'Źródło', fuel: 'Paliwo', gearbox: 'Skrzynia',
  priceFrom: 'Cena od', priceTo: 'Cena do', yearFrom: 'Rok od', yearTo: 'Rok do', reset: 'Wyczyść', apply: 'Zastosuj',
  noResults: 'Na razie nic tu nie ma', noResultsHint: 'Nowe auta pasujące do filtrów pojawią się tutaj zaraz po znalezieniu.',
  newBadge: 'NOWE', published: 'Opublikowano', found: 'Znaleziono', unavailableAd: 'Ogłoszenie nie jest już dostępne w serwisie',
  addFav: 'Do ulubionych', removeFav: 'Usuń z ulubionych', compare: 'Porównaj', copyLink: 'Kopiuj link', copied: 'Skopiowano link',
  openOriginal: 'Otwórz oryginał', hide: 'Ukryj', hidden: 'Ukryto', specs: 'Dane techniczne', equipment: 'Wyposażenie', description: 'Opis',
  seller: 'Sprzedawca', location: 'Lokalizacja', private: 'Osoba prywatna', dealer: 'Dealer', priceHistory: 'Historia ceny', noPriceChanges: 'Nie zauważono zmian ceny',
  initialPrice: 'Pierwsza cena', similar: 'Podobne auta', possibleDup: 'Możliwy duplikat w innym serwisie', matchedFilters: 'Pasuje do filtrów',
  loadingDetail: 'Pobieram pełne ogłoszenie…', mileage: 'Przebieg', year: 'Rok', engine: 'Silnik', power: 'Moc', price: 'Cena', drive: 'Napęd', body: 'Nadwozie',
  city: 'Miasto', vin: 'VIN', color: 'Kolor', doors: 'Drzwi', seats: 'Miejsca', damaged: 'Uszkodzony', serviceRecord: 'Historia serwisowa',
  compareTitle: 'Porównanie', compareN: 'Porównaj ({n})', clear: 'Wyczyść', best: 'najlepsze', pickTwo: 'Wybierz co najmniej 2 auta do porównania.',
  newFilterTitle: 'Nowy filtr', editFilter: 'Edycja filtra', name: 'Nazwa', autoName: 'Nazwa (opcjonalnie)', sources: 'Źródła', mainParams: 'Samochód',
  make: 'Marka', model: 'Model', anyMake: 'Dowolna marka', anyModel: 'Dowolny model', customModel: 'Inny model (slug z OTOMOTO)', from: 'Od', to: 'Do',
  engineCc: 'Pojemność, cm³', powerHp: 'Moc, KM', locationSec: 'Lokalizacja', voivodeship: 'Województwo', cities: 'Miasta (wpisz i naciśnij Enter)',
  nationwide: 'Cała Polska', sellerSec: 'Sprzedawca', anySeller: 'Wszyscy', extras: 'Dodatkowo', withPhoto: 'Tylko ze zdjęciami',
  excludeWords: 'Wyklucz słowa', excludeModels: 'Wyklucz modele', excludeFuel: 'Wyklucz paliwo', addTag: 'Wpisz i naciśnij Enter',
  unsupported: 'Drzwi, kolor, wyposażenie, kraj pochodzenia itp. nie występują na liście ogłoszeń źródła, więc nie są oferowane jako filtry (bez zgadywania).',
  save: 'Zapisz', cancel: 'Anuluj', delete: 'Usuń', edit: 'Edytuj', copy: 'Kopiuj', confirmDelete: 'Usunąć filtr?', confirmDeleteText: 'Znalezione ogłoszenia pozostaną w katalogu.',
  active: 'Aktywny', paused: 'Wyłączony', foundTotal: 'znalezione', foundNew: 'nowe', viewResults: 'Wyniki', notifications: 'Powiadomienia',
  noFilters: 'Brak filtrów', noFiltersHint: 'Utwórz filtr, a CarRadar będzie pilnować nowych aut za Ciebie.', created: 'Utworzono',
  noFavorites: 'Brak ulubionych', noFavoritesHint: 'Dotknij serca przy aucie, aby zapisać je tutaj.', added: 'Dodano',
  priceDown: 'cena spadła', priceUp: 'cena wzrosła',
  telegramId: 'Telegram ID', registered: 'Data rejestracji', carsFound: 'Znalezione auta', language: 'Język', theme: 'Motyw', dark: 'Ciemny', light: 'Jasny',
  timezone: 'Strefa czasowa', notifSettings: 'Powiadomienia', notifEnabled: 'Powiadomienia włączone', notifPhotos: 'Zdjęcia w powiadomieniach',
  notifMode: 'Dostarczanie', instant: 'Od razu', digest: 'Zestawienie', digestEvery: 'Zestawienie co (min)', night: 'Cisza nocna', nightFrom: 'Od', nightTo: 'Do',
  priceAlerts: 'Powiadomienia o zmianie ceny', monitoringSettings: 'Monitoring', admin: 'Panel admina', error: 'Coś poszło nie tak', retry: 'Ponów',
  openInTelegram: 'Otwórz CarRadar przez bota w Telegramie.', saved: 'Zapisano', dupFilter: 'Taki preset już istnieje. Zastąpić go?', users: 'Użytkownicy', blockedUsers: 'Zablokowani', queries: 'Odpytywane zapytania',
  sent: 'Wysłane', pending: 'W kolejce', failed: 'Błędy', errors: 'Błędy', restart: 'Restart', interval: 'Interwał sprawdzania, s', block: 'Zablokuj', unblock: 'Odblokuj',
  total: 'razem', requests: 'Zapytania', db: 'Odpowiedź bazy', newHour: 'Nowych ogłoszeń / godz.', pausedUntil: 'Wstrzymano do', limitNote: 'Do 4 aut',
  petrol: 'Benzyna', diesel: 'Diesel', lpg: 'LPG', 'petrol-lpg': 'Benzyna + LPG', hybrid: 'Hybryda', 'plug-in-hybrid': 'Hybryda Plug-in', electric: 'Elektryczny',
  manual: 'Manualna', automatic: 'Automatyczna', sedan: 'Sedan', combi: 'Kombi', compact: 'Hatchback', suv: 'SUV', coupe: 'Coupe', cabrio: 'Cabrio',
  minivan: 'Minivan', 'city-car': 'Auto miejskie', 'small-cars': 'Małe auto',
}
const uk: Dict = {
  ...ru,
  home: 'Головна', listings: 'Оголошення', filters: 'Фільтри', favorites: 'Обране', profile: 'Профіль',
  today: 'Сьогодні', week: '7 днів', month: '30 днів', newToday: 'Нових сьогодні', activeFilters: 'Активних фільтрів', foundWeek: 'Знайдено за тиждень',
  inFavorites: 'В обраному', latestFinds: 'Останні знахідки', all: 'Усі', monitoring: 'Моніторинг', lastUpdate: 'Останнє оновлення',
  checksEvery: 'Перевірка приблизно раз на {n} с (опитування, не реальний час)', statistics: 'Статистика', newFilter: 'Новий фільтр',
  ok: 'Працює', degraded: 'Збої', blocked: 'Заблоковано сайтом', schema_changed: 'Змінилася верстка сайту', unknown: 'Ще немає даних',
  unavailable: 'Недоступний', olxNote: 'OLX блокує автоматичний доступ, тому не відстежується.',
  search: 'Пошук…', sortNew: 'Спочатку нові', sortFound: 'За часом виявлення', sortCheap: 'Спочатку дешевші', sortExpensive: 'Спочатку дорожчі',
  sortYear: 'За роком випуску', sortMileage: 'За пробігом', cards: 'Картки', list: 'Список', source: 'Джерело', fuel: 'Пальне', gearbox: 'Коробка',
  priceFrom: 'Ціна від', priceTo: 'Ціна до', yearFrom: 'Рік від', yearTo: 'Рік до', reset: 'Скинути', apply: 'Застосувати',
  noResults: 'Поки нічого немає', noResultsHint: 'Нові авто за вашими фільтрами з’являться тут, щойно будуть знайдені.',
  newBadge: 'НОВЕ', published: 'Опубліковано', found: 'Знайдено', unavailableAd: 'Оголошення більше недоступне на майданчику',
  addFav: 'В обране', removeFav: 'Прибрати з обраного', compare: 'Порівняти', copyLink: 'Скопіювати посилання', copied: 'Посилання скопійовано',
  openOriginal: 'Відкрити оригінал', hide: 'Сховати', hidden: 'Приховано', specs: 'Характеристики', equipment: 'Оснащення', description: 'Опис',
  seller: 'Продавець', location: 'Розташування', private: 'Приватна особа', dealer: 'Автосалон', priceHistory: 'Історія ціни', noPriceChanges: 'Змін ціни поки не помічено',
  initialPrice: 'Перша ціна', similar: 'Схожі автомобілі', possibleDup: 'Можливий дублікат на іншому майданчику', matchedFilters: 'Підійшло під фільтри',
  loadingDetail: 'Завантажую повне оголошення…', mileage: 'Пробіг', year: 'Рік', engine: 'Двигун', power: 'Потужність', price: 'Ціна', drive: 'Привід', body: 'Кузов',
  city: 'Місто', color: 'Колір', doors: 'Двері', seats: 'Місця', damaged: 'Пошкодження', serviceRecord: 'Сервісна історія',
  compareTitle: 'Порівняння', compareN: 'Порівняти ({n})', clear: 'Очистити', best: 'краще', pickTwo: 'Оберіть щонайменше 2 авто для порівняння.',
  newFilterTitle: 'Новий фільтр', editFilter: 'Редагування', name: 'Назва', autoName: 'Назва (необов’язково)', sources: 'Джерела', mainParams: 'Автомобіль',
  make: 'Марка', model: 'Модель', anyMake: 'Будь-яка марка', anyModel: 'Будь-яка модель', customModel: 'Інша модель (slug як в OTOMOTO)', from: 'Від', to: 'До',
  engineCc: 'Об’єм, см³', powerHp: 'Потужність, KM', locationSec: 'Розташування', voivodeship: 'Воєводство', cities: 'Міста (введіть і натисніть Enter)',
  nationwide: 'Уся Польща', sellerSec: 'Продавець', anySeller: 'Усі', extras: 'Додатково', withPhoto: 'Тільки з фото',
  excludeWords: 'Виключити слова', excludeModels: 'Виключити моделі', excludeFuel: 'Виключити пальне', addTag: 'Введіть і натисніть Enter',
  unsupported: 'Двері, колір, оснащення, країна походження тощо не приходять у стрічці оголошень джерела, тому не пропонуються як фільтри (без вигадування).',
  save: 'Зберегти', cancel: 'Скасувати', delete: 'Видалити', edit: 'Змінити', copy: 'Копіювати', confirmDelete: 'Видалити фільтр?', confirmDeleteText: 'Уже знайдені оголошення залишаться в каталозі.',
  active: 'Активний', paused: 'Вимкнений', foundTotal: 'знайдено', foundNew: 'нових', viewResults: 'Результати', notifications: 'Сповіщення',
  noFilters: 'Фільтрів поки немає', noFiltersHint: 'Створіть фільтр, і CarRadar стежитиме за новими авто за вас.', created: 'Створено',
  noFavorites: 'Обране порожнє', noFavoritesHint: 'Натисніть на сердечко біля авто, щоб зберегти його тут.', added: 'Додано',
  priceDown: 'ціна знизилась', priceUp: 'ціна зросла',
  registered: 'Дата реєстрації', carsFound: 'Знайдено авто', language: 'Мова', theme: 'Тема', dark: 'Темна', light: 'Світла',
  timezone: 'Часовий пояс', notifSettings: 'Сповіщення', notifEnabled: 'Сповіщення увімкнено', notifPhotos: 'Фото у сповіщеннях',
  notifMode: 'Доставка', instant: 'Одразу', digest: 'Добіркою', digestEvery: 'Добірка раз на (хв)', night: 'Тихі години', nightFrom: 'З', nightTo: 'До',
  priceAlerts: 'Сповіщення про зміну ціни', monitoringSettings: 'Моніторинг', admin: 'Адмін-панель', error: 'Щось пішло не так', retry: 'Повторити',
  openInTelegram: 'Відкрийте CarRadar через Telegram-бота.', saved: 'Збережено', dupFilter: 'Такий пресет уже є. Замінити його?', users: 'Користувачі', blockedUsers: 'Заблоковано', queries: 'Запитів що опитуються',
  sent: 'Надіслано', pending: 'У черзі', failed: 'Помилки', errors: 'Помилки', restart: 'Перезапуск', interval: 'Інтервал перевірки, с', block: 'Заблокувати', unblock: 'Розблокувати',
  total: 'всього', requests: 'Запити', db: 'Відгук БД', newHour: 'Нових оголошень / год', pausedUntil: 'Пауза до', limitNote: 'До 4 автомобілів',
  petrol: 'Бензин', diesel: 'Дизель', hybrid: 'Гібрид', 'plug-in-hybrid': 'Плагін-гібрид', electric: 'Електро', 'petrol-lpg': 'Бензин + LPG',
  manual: 'Механіка', automatic: 'Автомат', sedan: 'Седан', combi: 'Універсал', compact: 'Хетчбек', coupe: 'Купе', cabrio: 'Кабріолет',
  minivan: 'Мінівен', 'city-car': 'Міський', 'small-cars': 'Малолітражка',
}
const DICTS: Record<Lang, Dict> = { en, ru, pl, uk }

export type T = (k: string, vars?: Record<string, string | number>) => string
export function makeT(lang: Lang): T {
  const d = DICTS[lang] ?? en
  return (k, vars) => {
    let s = d[k] ?? en[k] ?? k
    if (vars) for (const [a, b] of Object.entries(vars)) s = s.replace(`{${a}}`, String(b))
    return s
  }
}
export const I18nCtx = createContext<{ t: T; lang: Lang }>({ t: makeT('en'), lang: 'en' })
export const useI18n = () => useContext(I18nCtx)

export const LOCALES: Record<Lang, string> = { pl: 'pl-PL', ru: 'ru-RU', uk: 'uk-UA', en: 'en-GB' }
export function fmtMoney(v: number | null, lang: Lang, cur = 'PLN') {
  if (v == null) return '—'
  return new Intl.NumberFormat(LOCALES[lang], { maximumFractionDigits: 0 }).format(v) + (cur === 'PLN' ? ' zł' : ' ' + cur)
}
export const fmtNum = (v: number | null | undefined, lang: Lang, unit = '') =>
  v == null ? '—' : new Intl.NumberFormat(LOCALES[lang]).format(v) + (unit ? ' ' + unit : '')
export function ago(iso: string | null, lang: Lang) {
  if (!iso) return '—'
  const sec = Math.round((new Date(iso).getTime() - Date.now()) / 1000)
  const rtf = new Intl.RelativeTimeFormat(LOCALES[lang], { numeric: 'auto' })
  const a = Math.abs(sec)
  if (a < 60) return rtf.format(Math.round(sec), 'second')
  if (a < 3600) return rtf.format(Math.round(sec / 60), 'minute')
  if (a < 86400) return rtf.format(Math.round(sec / 3600), 'hour')
  return rtf.format(Math.round(sec / 86400), 'day')
}
export const fmtDate = (iso: string | null, lang: Lang) =>
  iso ? new Date(iso).toLocaleString(LOCALES[lang], { dateStyle: 'medium', timeStyle: 'short' }) : '—'
