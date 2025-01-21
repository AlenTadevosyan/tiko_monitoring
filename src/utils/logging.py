import logging
from pathlib import Path
from datetime import datetime

class UserFriendlyFormatter(logging.Formatter):
    """Custom formatter for user-friendly logs"""
    
    def format(self, record):
        if not hasattr(record, 'user_friendly'):
            return super().format(record)
            
        # Parse the user-friendly log data
        data = record.user_friendly
        timestamp = datetime.fromtimestamp(data.get('timestamp', 0))
        
        # Format for aggregated orders/fills
        if 'aggregated' in data.get('action', ''):
            return (
                f"{timestamp.strftime('%d/%m/%Y %H:%M')} | "
                f"{data.get('wallet', 'N/A')} | "
                f"{data.get('coin', 'N/A')} | "
                f"{data.get('action', 'N/A')} | "
                f"Total Size: {data.get('size', 'N/A')} | "
                f"Avg Price: {data.get('price', 'N/A')} | "
                f"Volume: ${data.get('total_volume', 0):,.2f} | "
                f"Count: {data.get('order_count', data.get('fill_count', 0))}"
            )
        
        # Format for individual events
        return (
            f"{timestamp.strftime('%d/%m/%Y %H:%M')} | "
            f"{data.get('wallet', 'N/A')} | "
            f"{data.get('coin', 'N/A')} | "
            f"{data.get('action', 'N/A')} | "
            f"{data.get('price', 'N/A')} | "
            f"{data.get('size', 'N/A')}"
        )

def log_user_action(logger, wallet: str, coin: str, action: str, price: float, size: float, timestamp: int = None, order_count: int = None, fill_count: int = None, total_volume: float = None):
    """Helper function to log user actions in a friendly format"""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
        
    extra_data = {
        'timestamp': timestamp,
        'wallet': wallet,
        'coin': coin,
        'action': action,
        'price': f"{price:,.2f}",
        'size': f"{size:,.8f}"
    }
    
    # Add additional data for aggregated events
    if order_count is not None:
        extra_data['order_count'] = order_count
        extra_data['total_volume'] = total_volume
    if fill_count is not None:
        extra_data['fill_count'] = fill_count
        extra_data['total_volume'] = total_volume
        
    logger.info("", extra={'user_friendly': extra_data})

def setup_logging():
    """Setup logging configuration for both technical and user-friendly logs"""
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Define log files
    technical_log = logs_dir / 'monitor.log'
    user_log = logs_dir / 'activity.log'
    
    # Remove any existing handlers to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure root logger for technical logs (file only, no console output)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(technical_log)
        ]
    )
    
    # Create user-friendly logger
    user_logger = logging.getLogger('user.activity')
    user_logger.setLevel(logging.INFO)
    user_logger.propagate = False  # Prevent propagation to root logger
    
    # File handler for user-friendly logs
    user_handler = logging.FileHandler(user_log)
    user_handler.setFormatter(UserFriendlyFormatter())
    user_logger.addHandler(user_handler)
    
    # Console handler for user-friendly logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(UserFriendlyFormatter())
    user_logger.addHandler(console_handler)
    
    # Disable debug logs from other libraries
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # Create a separate logger for alerts that only writes to file
    alerts_logger = logging.getLogger('alerts.console')
    alerts_logger.setLevel(logging.INFO)
    alerts_logger.propagate = False
    alerts_handler = logging.FileHandler(technical_log)
    alerts_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    alerts_logger.addHandler(alerts_handler) 