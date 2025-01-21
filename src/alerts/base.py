from abc import ABC, abstractmethod
from typing import Dict

class AlertHandler(ABC):
    @abstractmethod
    async def send_alert(self, message: str, metadata: Dict = None):
        """Send an alert through the specified channel"""
        pass 