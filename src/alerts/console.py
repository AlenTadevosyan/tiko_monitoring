import logging
from typing import Dict
from .base import AlertHandler

class ConsoleAlertHandler:
    def __init__(self):
        self.logger = logging.getLogger('alerts.console')
    
    async def send_alert(self, message: str):
        """Send alert to log file only"""
        self.logger.info(message) 