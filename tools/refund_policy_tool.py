"""
환불 정책 조회 툴
"""
from typing import Any, Dict, List
from .base import BaseTool


class RefundPolicyTool(BaseTool):
    """환불 정책을 조회하는 툴"""
    
    def __init__(self, policy_path: str = "data/refund_policy.txt"):
        super().__init__(
            name="RefundPolicyTool",
            description="환불 정책 정보를 조회합니다"
        )
        self.policy_path = policy_path
        self.policy_data = self._load_policy()
    
    def _load_policy(self) -> Dict[str, Any]:
        """환불 정책 데이터 로드 및 구조화"""
        try:
            with open(self.policy_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 정책을 구조화된 데이터로 변환
            return {
                "basic_rules": {
                    "refund_period": 7,  # 일
                    "refund_fee_rate": 0.1,  # 10%
                    "minimum_fee": 2000,  # 원
                    "shipping_fee": "고객 부담"
                },
                "status_policies": {
                    "주문접수": {"cancellable": True, "fee": False, "immediate": True},
                    "결제완료": {"cancellable": True, "fee": False, "immediate": True},
                    "상품준비중": {"cancellable": True, "fee": False, "immediate": True},
                    "배송중": {"cancellable": True, "fee": True, "immediate": False},
                    "배송완료": {"cancellable": True, "fee": True, "immediate": False}
                },
                "non_refundable_categories": [
                    "칫솔", "치약", "샴푸", "린스", "비누", "세안제", "화장품", 
                    "마스크팩", "크림", "로션", "향수", "데오드란트", "면도기", 
                    "콘택트렌즈", "속옷", "양말", "마스크", "생리용품"
                ],
                "special_cases": {
                    "defective_product": True,  # 불량품은 위생용품도 환불 가능
                    "damaged_delivery": True,   # 배송 중 파손도 환불 가능
                },
                "full_text": content
            }
        except FileNotFoundError:
            print(f"경고: {self.policy_path} 파일을 찾을 수 없습니다.")
            return {}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        환불 정책 조회 실행
        
        Args:
            query_type: 조회 유형 (basic_rules, status_policy, category_check, full_text)
            delivery_status: 배송 상태 (status_policy 조회 시)
            product_name: 제품명 (category_check 시)
            category: 카테고리 (category_check 시)
        
        Returns:
            정책 조회 결과
        """
        query_type = kwargs.get('query_type', 'basic_rules')
        
        if query_type == 'basic_rules':
            return {
                "success": True,
                "policy": self.policy_data.get('basic_rules', {})
            }
        
        elif query_type == 'status_policy':
            delivery_status = kwargs.get('delivery_status')
            if delivery_status:
                policy = self.policy_data.get('status_policies', {}).get(delivery_status)
                return {
                    "success": True if policy else False,
                    "policy": policy if policy else {},
                    "message": f"{delivery_status} 상태의 정책을 찾을 수 없습니다." if not policy else ""
                }
            return {
                "success": False,
                "message": "배송 상태를 지정해주세요."
            }
        
        elif query_type == 'category_check':
            product_name = kwargs.get('product_name', '').lower()
            category = kwargs.get('category', '').lower()
            
            # 개인위생용품 체크
            is_hygiene = self.is_hygiene_product(product_name, category)
            
            return {
                "success": True,
                "is_hygiene_product": is_hygiene,
                "refundable": not is_hygiene,
                "message": "개인위생용품은 불량품이 아닌 경우 환불이 불가능합니다." if is_hygiene else ""
            }
        
        elif query_type == 'full_text':
            return {
                "success": True,
                "policy_text": self.policy_data.get('full_text', '')
            }
        
        return {
            "success": False,
            "message": "올바른 query_type을 지정해주세요."
        }
    
    def is_hygiene_product(self, product_name: str, category: str = '') -> bool:
        """개인위생용품 여부 확인"""
        non_refundable = self.policy_data.get('non_refundable_categories', [])
        
        # 제품명을 소문자로 변환하여 체크
        product_name_lower = product_name.lower()
        
        # 제품명에 포함된 키워드 체크
        for item in non_refundable:
            if item.lower() in product_name_lower:
                return True
        
        # 화장품 카테고리는 기본적으로 개인위생용품
        # 알로에젤, 클렌징폼, BB크림, 쿠션, 세럼, 토너, 크림, 립스틱, 마스카라, 립밤, 마스크팩, 선크림, 향수, 샴푸 등
        if category == '화장품':
            return True
        
        # 특정 제품명 패턴 체크
        hygiene_keywords = ['젤', '크림', '로션', '세럼', '토너', '클렌징', '샴푸', '린스', '비누', '향수']
        for keyword in hygiene_keywords:
            if keyword in product_name_lower:
                return True
        
        return False
    
    def calculate_refund_fee(self, price: int) -> int:
        """환불 수수료 계산"""
        basic_rules = self.policy_data.get('basic_rules', {})
        fee_rate = basic_rules.get('refund_fee_rate', 0.1)
        minimum_fee = basic_rules.get('minimum_fee', 2000)
        
        calculated_fee = int(price * fee_rate)
        return max(calculated_fee, minimum_fee)
