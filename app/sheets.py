import os
import json
from datetime import datetime
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

# только запись в таблицы
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    
    if not json_path:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON_PATH не задан в переменных окружения")
    
    # можно передать не путь, а сам JSON строкой
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            info = json.load(f)
    else:
        info = json.loads(json_path)
    
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=credentials)
    return service


def append_lead_to_sheet(
    timestamp_iso: str,
    client_key: str,
    client_name: str,
    name: str,
    phone: str,
    city: str,
    budget: str,
    urgency: str,
    what_needed: str,
    comment: str,
    username: str,
    chat_id: int
) -> bool:
    try:
        spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
        if not spreadsheet_id:
            print("ОШИБКА: GOOGLE_SHEETS_ID не задан")
            return False
        
        service = get_sheets_service()
        
        values = [[
            timestamp_iso,
            client_key,
            client_name,
            name,
            phone,
            city,
            budget,
            urgency,
            what_needed,
            comment,
            username,
            str(chat_id)
        ]]
        
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:L',  # 12 колонок (A-L)
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"Заявка добавлена в таблицу: {result.get('updates', {}).get('updatedRows', 0)} строк")
        return True
        
    except Exception as e:
        print(f"ОШИБКА при добавлении в таблицу: {e}")
        return False
