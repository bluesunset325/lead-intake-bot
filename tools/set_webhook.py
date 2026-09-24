#!/usr/bin/env python3
# запускать после того, как ngrok выдал публичный URL

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()


async def set_webhook():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    
    if not token:
        print("ОШИБКА: TELEGRAM_BOT_TOKEN не задан в .env")
        sys.exit(1)
    
    if not webhook_url:
        print("ОШИБКА: WEBHOOK_URL не задан в .env")
        sys.exit(1)
    
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    params = {
        "url": webhook_url,
        "drop_pending_updates": True  # Очищаем накопившиеся обновления
    }
    
    # если задан секрет, Telegram будет присылать его в заголовке
    headers = {}
    if webhook_secret:
        params["secret_token"] = webhook_secret
        headers["X-Webhook-Secret"] = webhook_secret
    
    print(f"Установка webhook URL: {webhook_url}")
    print(f"Bot token: {token[:10]}...{token[-5:]}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=params)
            data = response.json()
            
            if data.get("ok"):
                print("✅ Webhook успешно установлен!")
                print(f"Описание: {data.get('description', 'OK')}")
                
                info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
                info_response = await client.get(info_url)
                info_data = info_response.json()
                
                if info_data.get("ok"):
                    webhook_info = info_data.get("result", {})
                    print(f"\nТекущий URL: {webhook_info.get('url')}")
                    print(f"Ожидает подтверждения: {webhook_info.get('has_custom_certificate')}")
                    print(f"Очередь обновлений: {webhook_info.get('pending_update_count', 0)}")
                
            else:
                print(f"❌ Ошибка: {data.get('description')}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            sys.exit(1)


if __name__ == "__main__":
    print("Инструмент установки webhook для Telegram бота\n")
    asyncio.run(set_webhook())
