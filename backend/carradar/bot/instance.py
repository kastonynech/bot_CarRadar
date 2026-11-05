from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from carradar.shared.config import settings

bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
