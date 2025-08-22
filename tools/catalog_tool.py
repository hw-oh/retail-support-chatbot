"""
제품 카탈로그 조회 툴
"""
import json
from typing import Any, Dict, List, Optional
from .base import BaseTool


class CatalogTool(BaseTool):
    """제품 카탈로그를 조회하는 툴"""
    
    def __init__(self, catalog_path: str = "data/catalog.json"):
        super().__init__(
            name="CatalogTool",
            description="제품 카탈로그에서 제품 정보를 조회합니다"
        )
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> List[Dict[str, Any]]:
        """카탈로그 데이터 로드"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"경고: {self.catalog_path} 파일을 찾을 수 없습니다.")
            return []
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        제품 조회 실행
        
        Args:
            product_name: 제품명 (부분 매칭)
            product_id: 제품 ID
            category: 카테고리
            min_price: 최소 가격
            max_price: 최대 가격
        
        Returns:
            조회 결과
        """
        product_name = kwargs.get('product_name')
        product_id = kwargs.get('product_id')
        category = kwargs.get('category')
        min_price = kwargs.get('min_price', 0)
        max_price = kwargs.get('max_price', float('inf'))
        
        results = []
        
        for product in self.catalog:
            # 제품 ID로 조회
            if product_id and product['product_id'] == product_id:
                return {
                    "success": True,
                    "products": [product],
                    "count": 1
                }
            
            # 조건에 맞는 제품 필터링
            if product_name and product_name.lower() not in product['product_name'].lower():
                continue
            
            if category and product['category'] != category:
                continue
            
            if not (min_price <= product['price'] <= max_price):
                continue
            
            results.append(product)
        
        return {
            "success": True,
            "products": results,
            "count": len(results)
        }
    
    def get_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """제품명으로 정확한 제품 조회"""
        for product in self.catalog:
            if product['product_name'] == product_name:
                return product
        return None
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록 반환"""
        categories = set()
        for product in self.catalog:
            categories.add(product['category'])
        return sorted(list(categories))
