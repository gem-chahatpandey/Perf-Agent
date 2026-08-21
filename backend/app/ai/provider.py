from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: str = "") -> str:
        ...

    @abstractmethod
    async def generate_structured(self, prompt: str, context: str = "") -> dict:
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        ...
