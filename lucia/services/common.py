from httpx import AsyncClient


class ServiceException(Exception):
    'Base of exceptions thrown by the service side'
    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        return self.args[0]


async def fetch_text(uri: str) -> str:
    async with AsyncClient(headers={ 'User-Agent': 'box-s-ville.luciabot' }) as client:
        res = await client.get(uri)
        if res.is_error:
            raise ServiceException('API 服务目前不可用')
        return res.text
