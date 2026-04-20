# card_matcher.py
# Chicken Task - Card Matching Logic (조건 매칭 로직)
# 운동장 조건 카드와 메인 카드 매칭 검증

def check_match(condition, card):
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


