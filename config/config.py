import yaml
from pathlib import Path
from typing import List, Dict

class Config:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "settings.yaml"
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    @property
    def addresses(self) -> List[str]:
        return self.config['addresses']
    
    @property
    def monitoring_settings(self) -> Dict:
        return self.config['monitoring']
    
    @property
    def alert_settings(self) -> Dict:
        return self.config['alerts'] 