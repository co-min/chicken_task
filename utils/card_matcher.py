def check_match(condition, card):
    if not condition or not card:
        return False

    condition_type = condition.get('type')
    condition_value = condition.get('value')

    if condition_type == 'color':
        return card.get('color') == condition_value
    elif condition_type == 'shape':
        return card.get('shape') == condition_value
    elif condition_type == 'number':
        return card.get('number') == condition_value

    return False


def get_card_text(card):
    if not card:
        return "알 수 없음"

    color_kr = {'red': '빨간색', 'blue': '파란색', 'green': '초록색'}
    shape_kr = {'square': '사각형', 'triangle': '삼각형', 'circle': '원'}

    color_name = color_kr.get(card.get('color'), card.get('color'))
    shape_name = shape_kr.get(card.get('shape'), card.get('shape'))

    return f"{color_name} {shape_name} {card.get('number')}개"
