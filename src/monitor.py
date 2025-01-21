import asyncio
import logging
import json
from typing import List, Dict, Set
from datetime import datetime
from pathlib import Path

from client import HyperliquidClient
from alerts.console import ConsoleAlertHandler

class HyperliquidWatcher:
    def __init__(self, addresses: List[str], interval: int, min_trade_value: float, aggregation_window: int):
        self.addresses = addresses
        self.interval = interval
        self.min_trade_value = min_trade_value
        self.aggregation_window = aggregation_window
        self.client = HyperliquidClient()
        self.alert_handler = ConsoleAlertHandler()
        self.logger = logging.getLogger(__name__)
        
        # Initialize logs directory
        self.logs_dir = Path("data")
        self.logs_dir.mkdir(exist_ok=True)
        self.logs_file = self.logs_dir / "state.json"
        self.logs = self.load_logs()
        
        # Track active orders that need status checking
        self.active_orders: Dict[str, Dict[str, str]] = {}  # {order_id: {"address": address, "last_status": status}}

    def load_logs(self) -> Dict:
        """Load existing logs or create new if doesn't exist"""
        if self.logs_file.exists():
            try:
                with open(self.logs_file) as f:
                    data = json.load(f)
                    # Ensure required keys exist
                    if not isinstance(data, dict):
                        self.logger.warning("Invalid logs format, resetting")
                        return {"orders": {}, "fills": {}, "status_changes": {}}
                    data.setdefault("orders", {})
                    data.setdefault("fills", {})
                    data.setdefault("status_changes", {})
                    return data
            except json.JSONDecodeError as e:
                self.logger.warning(f"Error loading logs: {e}, resetting")
                return {"orders": {}, "fills": {}, "status_changes": {}}
            except Exception as e:
                self.logger.warning(f"Unexpected error loading logs: {e}, resetting")
                return {"orders": {}, "fills": {}, "status_changes": {}}
        return {"orders": {}, "fills": {}, "status_changes": {}}

    def save_logs(self):
        """Save current state to logs file"""
        try:
            with open(self.logs_file, "w") as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving logs: {e}")

    def format_order(self, order: Dict) -> str:
        """Format an order for display"""
        try:
            side = "Ask" if order["side"] == "A" else "Bid"
            timestamp = datetime.fromtimestamp(order["timestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            volume = float(order["sz"]) * float(order["limitPx"])
            
            return (
                f"Token: {order['coin']}, "
                f"Side: {side}, "
                f"Size: {order['sz']}, "
                f"Price: {order['limitPx']}, "
                f"Volume: ${volume:.2f}, "
                f"Type: {order['orderType']}, "
                f"Time: {timestamp}"
            )
        except Exception as e:
            self.logger.error(f"Error formatting order: {e}, order data: {order}")
            return str(order)

    def is_new_event(self, event_type: str, event_id: str, timestamp: int) -> bool:
        """Check if an event is new based on its ID and timestamp"""
        try:
            events = self.logs.get(event_type, {})
            return not (event_id in events and events[event_id] == timestamp)
        except Exception as e:
            self.logger.error(f"Error checking event: {e}, type: {event_type}, id: {event_id}")
            return True

    def log_event(self, event_type: str, event_id: str, timestamp: int):
        """Log an event with its timestamp"""
        try:
            if event_type not in self.logs:
                self.logs[event_type] = {}
            self.logs[event_type][event_id] = timestamp
            self.save_logs()
        except Exception as e:
            self.logger.error(f"Error logging event: {e}, type: {event_type}, id: {event_id}")

    async def process_orders(self, address: str, orders: List[Dict]):
        """Process open orders for an address"""
        try:
            current_order_ids = set()
            
            for order in orders:
                order_id = str(order.get("oid", ""))
                timestamp = order.get("timestamp", 0)
                
                if not order_id or not timestamp:
                    self.logger.warning(f"Invalid order data: {order}")
                    continue
                
                current_order_ids.add(order_id)
                
                if self.is_new_event("orders", order_id, timestamp):
                    await self.alert_handler.send_alert(
                        f"\nNew open order for {address}:\n{self.format_order(order)}"
                    )
                    self.log_event("orders", order_id, timestamp)
                    # Add to active orders for status tracking
                    self.active_orders[order_id] = {"address": address, "last_status": "open"}
            
            # Remove orders that are no longer open from active tracking
            for order_id in list(self.active_orders.keys()):
                if order_id not in current_order_ids and self.active_orders[order_id]["address"] == address:
                    await self.check_order_status(order_id, address)
                    
        except Exception as e:
            self.logger.error(f"Error processing orders: {e}, address: {address}")

    async def check_order_status(self, order_id: str, address: str):
        """Check status of an order and notify if it changed"""
        try:
            status_data = await self.client.get_order_status(
                address=address,
                order_id=order_id,
                order_type="orderStatus"
            )
            
            if not status_data:
                return
            
            current_status = status_data.get("status", "unknown")
            last_status = self.active_orders.get(order_id, {}).get("last_status", "unknown")
            
            # If status changed and it's not open/filled (we handle fills separately)
            if current_status != last_status and current_status not in ["open", "filled"]:
                status_key = f"{order_id}_{current_status}"
                timestamp = status_data.get("statusTimestamp", 0)
                
                coin = status_data.get("coin", "UNKNOWN")
                
                if self.is_new_event("status_changes", status_key, timestamp):
                    await self.alert_handler.send_alert(
                        f"\nOrder status change for {address}:\n"
                        f"Order {order_id} is now {current_status}\n"
                        f"Token: {coin}"
                    )
                    self.log_event("status_changes", status_key, timestamp)
            
            # Update status in active orders or remove if final state
            if current_status in ["canceled", "rejected", "marginCanceled"]:
                self.active_orders.pop(order_id, None)
            else:
                self.active_orders[order_id] = {"address": address, "last_status": current_status}
                
        except Exception as e:
            self.logger.error(f"Error checking order status: {str(e)}", exc_info=True)

    async def process_fills(self, address: str, fills: List[Dict]):
        """Process fills for an address"""
        try:
            for fill in fills:
                fill_id = str(fill.get("tid", ""))
                timestamp = fill.get("time", 0)
                
                if not fill_id or not timestamp:
                    self.logger.warning(f"Invalid fill data: {fill}")
                    continue
                
                if self.is_new_event("fills", fill_id, timestamp):
                    side = "Bought" if fill.get("side") == "B" else "Sold"
                    volume = float(fill.get("sz", 0)) * float(fill.get("px", 0))
                    await self.alert_handler.send_alert(
                        f"\nNew fill for {address}:\n"
                        f"{side} {fill.get('sz')} {fill.get('coin')} @ {fill.get('px')} "
                        f"(${volume:.2f})"
                    )
                    self.log_event("fills", fill_id, timestamp)
        except Exception as e:
            self.logger.error(f"Error processing fills: {e}, address: {address}")

    async def watch(self):
        """Main monitoring loop"""
        self.logger.info(f"Starting open orders monitor for addresses: {self.addresses}")
        
        while True:
            try:
                for address in self.addresses:
                    # Check open orders
                    orders = await self.client.get_open_orders(address)
                    await self.process_orders(address, orders)
                    
                    # Check fills
                    fills = await self.client.get_fills(address)
                    await self.process_fills(address, fills)
                    
                    # Check status of active orders
                    for order_id, data in list(self.active_orders.items()):
                        if data["address"] == address:
                            await self.check_order_status(order_id, address)
                    
            except Exception as e:
                self.logger.error(f"Error in watch loop: {e}")
                
            await asyncio.sleep(self.interval)

async def test_order_status():
    """Test function to check a specific order status"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hyperliquid_watcher.log'),
            logging.StreamHandler()
        ]
    )
    
    # Test configuration
    test_address = "0xDd4c3d252c29da6F584a9b83D2b61AD82ac92FaB"
    test_order_id = "65426885794"  # Make sure this is a valid, recent order ID
    
    # Initialize watcher with minimal config
    watcher = HyperliquidWatcher(
        addresses=[test_address],
        interval=10,
        min_trade_value=0,
        aggregation_window=60
    )
    
    # Test the specific order
    await watcher.check_order_status(test_order_id, test_address)

if __name__ == "__main__":
    asyncio.run(test_order_status()) 