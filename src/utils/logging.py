import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration for both file and console output"""
    # Create logs directory if it doesn't exist
    log_file = Path(__file__).parent.parent.parent / 'monitor.log'
    log_file.parent.mkdir(exist_ok=True)
    
    # Remove any existing handlers to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Disable debug logs from other libraries
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING) 