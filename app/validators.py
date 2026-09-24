import re
from typing import Optional

# +79..., 89..., 79..., 9... — 10 цифр после кода
RU_PHONE_PATTERN = re.compile(r'^[\+]?7?(\d{10})$')


def normalize_phone(phone: str) -> Optional[str]:
    """-> +7XXXXXXXXXX"""
    if not phone:
        return None
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and (digits.startswith('7') or digits.startswith('8')):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    else:
        return None
    
    # только мобильные: вторая цифра 9
    if digits[1] != '9':
        return None
    
    return f"+{digits}"


def validate_phone(phone: str) -> tuple[bool, Optional[str], str]:
    """(is_valid, normalized_or_error)"""
    normalized = normalize_phone(phone)
    
    if not normalized:
        return False, None, "Пожалуйста, введите корректный российский номер телефона"
    
    return True, normalized, ""


def validate_name(name: str) -> tuple[bool, str]:
    if not name or len(name.strip()) < 2:
        return False, "Пожалуйста, введите имя (минимум 2 символа)"
    
    return True, ""


def validate_text(text: str, field_name: str = "Поле") -> tuple[bool, str]:
    if not text or len(text.strip()) < 2:
        return False, f"Пожалуйста, заполните {field_name}"
    
    return True, ""
