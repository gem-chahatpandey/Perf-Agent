from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    @abstractmethod
    async def save(self, key: str, data: dict) -> None:
        ...

    @abstractmethod
    async def load(self, key: str) -> dict:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def list(self, prefix: str) -> list[str]:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def save_file(self, key: str, content: bytes) -> None:
        ...

    @abstractmethod
    async def load_file(self, key: str) -> bytes:
        ...
