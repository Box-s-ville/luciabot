from aiocache import cached

from .common import fetch_text


@cached(ttl=60) # 结果缓存 60 秒
async def get_current_weather_short(city: str) -> str:
    return (await fetch_text(f'https://wttr.in/{city}?format=1')).strip()

