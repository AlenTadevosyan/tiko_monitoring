from typing import List, Dict, Optional
import aiohttp
import logging
import asyncio
class HyperliquidClient:
    def __init__(self):
        self.base_url = "https://api.hyperliquid.xyz"
        self.logger = logging.getLogger(__name__)

    async def get_open_orders(self, address: str) -> List[Dict]:
        """
        Fetch open orders for an address using the Hyperliquid API
        
        Args:
            address: Wallet address in 42-character hexadecimal format
            
        Returns:
            List of open orders
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/info",
                    json={
                        "type": "frontendOpenOrders",
                        "user": address
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Log the raw response for debugging
                        self.logger.debug(f"Open orders response: {data}")
                        # Ensure we got a list
                        if not isinstance(data, list):
                            self.logger.error(f"Unexpected response format for open orders: {data}")
                            return []
                        return data
                    else:
                        self.logger.error(f"API request failed with status {response.status}")
                        return []
            except Exception as e:
                self.logger.error(f"Error fetching open orders: {e}")
                return []

    async def get_fills(self, address: str, start_time: Optional[int] = None) -> List[Dict]:
        """
        Fetch fills for an address using userFillsByTime for more detailed data
        
        Args:
            address: Wallet address in 42-character hexadecimal format
            start_time: Optional start time in milliseconds
            
        Returns:
            List of fills
        """
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "type": "userFillsByTime",
                    "user": address,
                    "startTime": start_time or 0,
                    "aggregateByTime": True
                }
                
                async with session.post(
                    f"{self.base_url}/info",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Log the raw response for debugging
                        self.logger.debug(f"Fills response: {data}")
                        # Ensure we got a list
                        if not isinstance(data, list):
                            self.logger.error(f"Unexpected response format for fills: {data}")
                            return []
                        return data
                    else:
                        self.logger.error(f"API request failed with status {response.status}")
                        return []
            except Exception as e:
                self.logger.error(f"Error fetching fills: {e}")
                return []

    async def get_transactions(self, address: str) -> List[Dict]:
        """
        Fetch transactions for an address
        To be implemented with actual API
        """
        pass 

    async def get_order_status(self, address: str, order_id: str, order_type: str = "orderStatus") -> Dict:
        """
        Get the status of a specific order
        
        Args:
            address (str): The 42-character hexadecimal wallet address
            order_id (str): The order ID to check
            order_type (str): The type of order status request (default: "orderStatus")
            
        Returns:
            Dict: The order status response
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Convert order_id to integer since API expects uint64
                oid = int(order_id)
                
                async with session.post(
                    f"{self.base_url}/info",
                    json={
                        "type": order_type,
                        "user": address,
                        "oid": oid  # Send as number, not string
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "order" and "order" in data:
                            # Return a simplified structure with the data we need
                            order_data = data["order"]
                            return {
                                "status": order_data.get("status"),
                                "statusTimestamp": order_data.get("statusTimestamp"),
                                "coin": order_data.get("order", {}).get("coin")
                            }
                    return None
            except ValueError as e:
                self.logger.error(f"Invalid order ID format: {order_id}")
                return None
            except Exception as e:
                self.logger.error(f"Error fetching order status: {e}")
                return None

if __name__ == "__main__":
    client = HyperliquidClient()
    open_orders = asyncio.run(client.get_open_orders("0xDd4c3d252c29da6F584a9b83D2b61AD82ac92FaB"))
    print(open_orders)