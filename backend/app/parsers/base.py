from abc import ABC, abstractmethod
from app.models.performance import PerformanceMetrics


class ReportParser(ABC):
    @abstractmethod
    def can_parse(self, filename: str, content: bytes) -> bool:
        ...

    @abstractmethod
    async def parse(self, filename: str, content: bytes, run_id: str) -> PerformanceMetrics:
        ...
