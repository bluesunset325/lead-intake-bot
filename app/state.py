from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import time

class UserState(str, Enum):
    IDLE = "idle"
    LEAVING_REQUEST = "leaving_request"
    QUESTION = "question"
    AWAITING_NAME = "awaiting_name"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_CITY = "awaiting_city"
    AWAITING_WHAT_NEEDED = "awaiting_what_needed"
    AWAITING_BUDGET = "awaiting_budget"
    AWAITING_URGENCY = "awaiting_urgency"
    AWAITING_COMMENT = "awaiting_comment"
    CONFIRM = "confirm"


@dataclass
class LeadData:
    client_key: str = ""
    client_name: str = ""
    name: str = ""
    phone: str = ""
    city: str = ""
    what_needed: str = ""
    budget: str = ""
    urgency: str = ""
    comment: str = ""
    username: str = ""
    chat_id: int = 0


@dataclass
class UserSession:
    state: UserState = UserState.IDLE
    lead_data: LeadData = field(default_factory=LeadData)
    current_question_index: int = 0
    last_message_time: float = 0
    last_warning_time: float = 0
    spam_warning_sent: bool = False


user_sessions: Dict[int, UserSession] = {}


def get_user_session(chat_id: int) -> UserSession:
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()
    return user_sessions[chat_id]


def clear_user_session(chat_id: int) -> None:
    if chat_id in user_sessions:
        user_sessions[chat_id] = UserSession()


def update_user_state(chat_id: int, state: UserState) -> None:
    session = get_user_session(chat_id)
    session.state = state


def check_rate_limit(chat_id: int) -> tuple[bool, str]:
    """антиспам: не чаще одного сообщения в секунду"""
    current_time = time.time()
    session = get_user_session(chat_id)
    
    time_diff = current_time - session.last_message_time
    
    if time_diff < 1.0:
        # предупреждаем не чаще раза в 10 с
        if current_time - session.last_warning_time > 10:
            session.last_warning_time = current_time
            return False, "Пожалуйста, не отправляйте сообщения так быстро. Подождите секунду."
        return False, ""
    
    session.last_message_time = current_time
    return True, ""
