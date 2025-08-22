"""
날짜 업데이트 스크립트
2025년 8월 22일 기준으로 모든 날짜 재조정
"""
import json
from datetime import datetime, timedelta
import random

# 기준 날짜
TODAY = datetime(2025, 8, 22)

def update_purchase_history():
    """구매 이력 날짜 업데이트"""
    with open('data/purchase_history.json', 'r', encoding='utf-8') as f:
        purchases = json.load(f)
    
    # 날짜를 거슬러 올라가며 재배치
    current_date = TODAY
    
    for i, purchase in enumerate(reversed(purchases)):
        # 랜덤하게 1-4일씩 과거로
        days_back = random.randint(1, 4)
        current_date -= timedelta(days=days_back)
        
        purchase_date = current_date
        purchase['purchase_date'] = purchase_date.strftime('%Y-%m-%d')
        
        # 배송 상태에 따른 배송일 설정
        if purchase['delivery_status'] == '배송완료':
            # 구매 후 2-4일 뒤 배송
            delivery_days = random.randint(2, 4)
            delivery_date = purchase_date + timedelta(days=delivery_days)
            purchase['delivery_date'] = delivery_date.strftime('%Y-%m-%d')
        elif purchase['delivery_status'] == '배송중':
            # 아직 배송 안됨
            purchase['delivery_date'] = None
        else:
            # 배송 전 상태
            purchase['delivery_date'] = None
            
        # 주문번호도 날짜에 맞게 업데이트
        order_date_str = purchase_date.strftime('%Y%m%d')
        purchase['order_id'] = f"ORD{order_date_str}{str(i+1).zfill(3)}"
    
    # 다시 원래 순서로 정렬 (최신순)
    purchases.reverse()
    
    with open('data/purchase_history.json', 'w', encoding='utf-8') as f:
        json.dump(purchases, f, ensure_ascii=False, indent=2)
    
    print(f"✅ purchase_history.json 업데이트 완료 ({len(purchases)}개 주문)")
    
    # 최근 주문 몇 개 출력
    print("\n최근 주문 5개:")
    for purchase in purchases[:5]:
        print(f"  - {purchase['order_id']}: {purchase['product_name']} ({purchase['purchase_date']})")


def update_evaluate_refund():
    """평가 데이터 날짜 업데이트"""
    with open('data/evaluate_refund.json', 'r', encoding='utf-8') as f:
        evaluations = json.load(f)
    
    # 구매 이력 읽기
    with open('data/purchase_history.json', 'r', encoding='utf-8') as f:
        purchases = json.load(f)
    
    # 주문번호 매핑 생성
    order_map = {p['product_name']: p for p in purchases}
    
    for eval_data in evaluations:
        order_info = eval_data.get('order_info', {})
        product_name = order_info.get('product_name')
        
        # 실제 구매 데이터에서 매칭되는 주문 찾기
        if product_name and product_name in order_map:
            real_order = order_map[product_name]
            order_info['order_id'] = real_order['order_id']
            order_info['purchase_date'] = real_order['purchase_date']
            order_info['delivery_date'] = real_order.get('delivery_date')
        else:
            # 매칭 안되면 최근 날짜로 임의 생성
            days_ago = random.randint(1, 30)
            purchase_date = TODAY - timedelta(days=days_ago)
            order_info['purchase_date'] = purchase_date.strftime('%Y-%m-%d')
            
            if order_info.get('delivery_status') == '배송완료':
                delivery_date = purchase_date + timedelta(days=3)
                order_info['delivery_date'] = delivery_date.strftime('%Y-%m-%d')
    
    with open('data/evaluate_refund.json', 'w', encoding='utf-8') as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ evaluate_refund.json 업데이트 완료 ({len(evaluations)}개 시나리오)")


def main():
    print("📅 날짜 업데이트 시작 (기준: 2025년 8월 22일)")
    print("="*50)
    
    update_purchase_history()
    update_evaluate_refund()
    
    print("\n✅ 모든 날짜 업데이트 완료!")


if __name__ == "__main__":
    main()
