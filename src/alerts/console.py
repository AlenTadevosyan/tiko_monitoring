import logging
from typing import Dict
from .base import AlertHandler

class ConsoleAlertHandler(AlertHandler):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_alert(self, message: str, metadata: Dict = None):
        self.logger.info(message) 