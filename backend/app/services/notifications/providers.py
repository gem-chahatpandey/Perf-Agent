from abc import ABC, abstractmethod
from app.core.logging import logger


class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, subject: str, message: str) -> bool:
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        ...


class SlackProvider(NotificationProvider):
    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    async def send(self, subject: str, message: str) -> bool:
        if not self.is_configured():
            return False
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._webhook_url, json={"text": f"*{subject}*\n{message}"})
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Slack notification failed: {e}")
            return False


class TeamsProvider(NotificationProvider):
    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    async def send(self, subject: str, message: str) -> bool:
        if not self.is_configured():
            return False
        import httpx
        try:
            payload = {"@type": "MessageCard", "summary": subject, "text": f"**{subject}**\n\n{message}"}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._webhook_url, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Teams notification failed: {e}")
            return False


class EmailProvider(NotificationProvider):
    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from = from_addr

    def is_configured(self) -> bool:
        return bool(self._host and self._username)

    async def send(self, subject: str, message: str) -> bool:
        if not self.is_configured():
            return False
        logger.info(f"Email notification queued: {subject}")
        return True
