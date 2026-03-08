# card_matcher.py
# Chicken Task - Card Matching Logic (조건 매칭 로직)
# 운동장 조건 카드와 메인 카드 매칭 검증

def check_match(condition, card):
    """
    메인 카드가 운동장 조건과 일치하는지 확인
    
    Args:
        condition (dict): 운동장 조건
                         {'type': 'color'|'shape'|'number', 'value': ...}
        card (dict): 메인 카드
                    {'color': ..., 'shape': ..., 'number': ...}
    
    Returns:
        bool: True=일치, False=불일치
    """
    if not condition or not card:
        return False
    
    condition_type = condition.get('type')
    condition_value = condition.get('value')
    
    # 조건 타입에 따라 매칭
    if condition_type == 'color':
        return card.get('color') == condition_value
    
    elif condition_type == 'shape':
        return card.get('shape') == condition_value
    
    elif condition_type == 'number':
        return card.get('number') == condition_value
    
    return False


def get_condition_text(condition):
    """
    조건을 텍스트로 변환 (화면 표시용)
    
    Args:
        condition (dict): 운동장 조건
    
    Returns:
        str: 한글 텍스트 (예: "색상: 빨강", "모양: 사각형", "개수: 2")
    """
    if not condition:
        return "알 수 없음"
    
    condition_type = condition.get('type')
    condition_value = condition.get('value')
    
    # 한글 변환표
    type_kr = {
        'color': '색상',
        'shape': '모양',
        'number': '개수'
    }
    
    color_kr = {
        'red': '빨강',
        'blue': '파랑',
        'green': '초록'
    }
    
    shape_kr = {
        'square': '사각형',
        'triangle': '삼각형',
        'circle': '원'
    }
    
    type_name = type_kr.get(condition_type, condition_type)
    
    if condition_type == 'color':
        value_name = color_kr.get(condition_value, condition_value)
    elif condition_type == 'shape':
        value_name = shape_kr.get(condition_value, condition_value)
    elif condition_type == 'number':
        value_name = str(condition_value)
    else:
        value_name = str(condition_value)
    
    return f"{type_name}: {value_name}"


def get_card_text(card):
    """
    카드를 텍스트로 변환 (화면 표시용)
    
    Args:
        card (dict): 메인 카드
    
    Returns:
        str: 한글 텍스트 (예: "빨간색 사각형 2개")
    """
    if not card:
        return "알 수 없음"
    
    color = card.get('color')
    shape = card.get('shape')
    number = card.get('number')
    
    # 한글 변환표
    color_kr = {
        'red': '빨간색',
        'blue': '파란색',
        'green': '초록색'
    }
    
    shape_kr = {
        'square': '사각형',
        'triangle': '삼각형',
        'circle': '원'
    }
    
    color_name = color_kr.get(color, color)
    shape_name = shape_kr.get(shape, shape)
    
    return f"{color_name} {shape_name} {number}개"


# ==================== 테스트 코드 ====================
if __name__ == "__main__":
    print("\n### 조건 매칭 테스트 ###\n")
    
    # 테스트 케이스
    test_cases = [
        # (condition, card, expected_result, description)
        (
            {'type': 'color', 'value': 'red'},
            {'color': 'red', 'shape': 'square', 'number': 2},
            True,
            "색상 일치"
        ),
        (
            {'type': 'color', 'value': 'red'},
            {'color': 'blue', 'shape': 'square', 'number': 2},
            False,
            "색상 불일치"
        ),
        (
            {'type': 'shape', 'value': 'triangle'},
            {'color': 'blue', 'shape': 'triangle', 'number': 1},
            True,
            "모양 일치"
        ),
        (
            {'type': 'shape', 'value': 'triangle'},
            {'color': 'blue', 'shape': 'circle', 'number': 1},
            False,
            "모양 불일치"
        ),
        (
            {'type': 'number', 'value': 3},
            {'color': 'green', 'shape': 'square', 'number': 3},
            True,
            "숫자 일치"
        ),
        (
            {'type': 'number', 'value': 3},
            {'color': 'green', 'shape': 'square', 'number': 2},
            False,
            "숫자 불일치"
        ),
    ]
    
    for i, (condition, card, expected, desc) in enumerate(test_cases, 1):
        result = check_match(condition, card)
        status = "[OK]" if result == expected else "[FAIL]"
        
        cond_text = get_condition_text(condition)
        card_text = get_card_text(card)
        
        print(f"테스트 {i}: {status} {desc}")
        print(f"  조건: {cond_text}")
        print(f"  카드: {card_text}")
        print(f"  예상: {expected}, 결과: {result}")
        print()
    
    print("[OK] card_matcher 테스트 완료!")
