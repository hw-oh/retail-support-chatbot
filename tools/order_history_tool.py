"""
주문 이력 조회 툴
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .base import BaseTool
from agents.base import get_llm_client


class OrderHistoryTool(BaseTool):
    """주문 이력을 조회하는 툴"""
    
    def __init__(self, history_path: str = "data/purchase_history.json"):
        super().__init__(
            name="OrderHistoryTool",
            description="고객의 주문 이력을 조회합니다"
        )
        self.history_path = history_path
        self.orders = self._load_orders()
        self.llm = get_llm_client(use_mini=True)  # Use smaller model for cost efficiency
    
    def _load_orders(self) -> List[Dict[str, Any]]:
        """주문 이력 데이터 로드"""
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"경고: {self.history_path} 파일을 찾을 수 없습니다.")
            return []
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        주문 조회 실행 - LLM 기반
        
        Returns:
            조회 결과
        """
        # Get conversation context if available
        conversation_context = kwargs.get('conversation_context', {})
        previous_shown_orders = conversation_context.get('available_orders', [])
        
        # Prepare query context
        query_context = {
            "current_date": "2025-08-22",
            "request": kwargs,
            "all_orders": self.orders,
            "previous_shown_orders": previous_shown_orders
        }
        
        # Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": """You are an order history query assistant for a Korean e-commerce system.
                
Your task is to filter and return relevant orders based on the user's request.

Available request parameters:
- order_id: Specific order ID to find
- product_name: Product name to search for
- delivery_status: Delivery status to filter by
- time_reference: Time expressions like "최근", "일주일 이내", "한달 이내", "3일 이내", "다른" etc.
- quantity: Number of results to return
- start_date/end_date: Date range for filtering

Special handling for "다른" (other/different):
- Check previous_shown_orders to see what was already displayed
- Return orders that were NOT in previous_shown_orders
- This typically means the user wants to see different/additional items

Important rules:
1. For time_reference, calculate dates based on current_date (2025-08-22)
2. Sort results by purchase_date in descending order (newest first)
3. Apply quantity limit AFTER sorting
4. Return all matching orders if no quantity specified
5. For "최근" without specific period, return last 5-10 orders
6. For "다른" or additional orders:
   - Check previous_shown_orders field
   - Return orders that were NOT in previous_shown_orders
   - If no request context, return next batch of orders

Response format:
{
    "success": true/false,
    "orders": [array of matching orders],
    "count": number of orders returned,
    "message": "optional message in Korean"
}"""
            },
            {
                "role": "user",
                "content": f"""Query the orders based on this request:
{json.dumps(query_context, ensure_ascii=False, indent=2)}

Return the filtered orders in the specified JSON format."""
            }
        ]
        
        try:
            # Use LLM to process the query
            result = self.llm.generate_json(messages, temperature=0.1)
            
            # Ensure proper format
            if "orders" not in result:
                result["orders"] = []
            if "count" not in result:
                result["count"] = len(result.get("orders", []))
            if "success" not in result:
                result["success"] = True
                
            return result
            
        except Exception as e:
            print(f"LLM query processing error: {e}")
            # Fallback to simple recent orders
            recent_orders = sorted(self.orders, key=lambda x: x['purchase_date'], reverse=True)[:10]
            return {
                "success": True,
                "orders": recent_orders,
                "count": len(recent_orders),
                "message": "최근 주문 내역입니다."
            }
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문번호로 특정 주문 조회"""
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        return None
    
    def get_order_by_product_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """제품명으로 가장 최근 주문 조회"""
        matching_orders = []
        for order in self.orders:
            if order['product_name'] == product_name:
                matching_orders.append(order)
        
        if not matching_orders:
            return None
        
        # 가장 최근 주문 반환
        matching_orders.sort(key=lambda x: x['purchase_date'], reverse=True)
        return matching_orders[0]
    
    def calculate_days_since_delivery(self, order_id: str) -> Optional[int]:
        """배송 완료 후 경과 일수 계산"""
        order = self.get_order_by_id(order_id)
        if not order or order['delivery_status'] != '배송완료':
            return None
        
        if not order['delivery_date']:
            return None
        
        delivery_date = datetime.strptime(order['delivery_date'], '%Y-%m-%d')
        # 2025년 8월 22일 기준
        today = datetime(2025, 8, 22)
        days_passed = (today - delivery_date).days
        
        return days_passed
