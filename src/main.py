import asyncio
import logging
from pathlib import Path

from config.config import Config
from monitor import HyperliquidWatcher
from utils.logging import setup_logging

async def main():
    # Setup logging with INFO level
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    config = Config()
    
    # Initialize watcher
    watcher = HyperliquidWatcher(
        addresses=config.addresses,
        **config.monitoring_settings
    )
    
    try:
        await watcher.watch()
    except KeyboardInterrupt:
        logging.info("Shutting down monitor...")
    except Exception as e:
        logging.error(f"Error in monitor: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 