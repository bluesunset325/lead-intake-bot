# Lead Intake Bot

Быстрый MVP Telegram-бота для приёма заявок с интеграцией в Google Sheets и уведомлениями менеджера.

---

## 🚀 Быстрый старт в VS Code

### Шаг 1: Установка Python 3.11+
- Скачайте с [python.org](https://www.python.org/downloads/)
- **ВАЖНО**: При установке отметьте галочку "Add Python to PATH"
- Проверьте: `python --version` (должно показать 3.11+)

### Шаг 2: Открытие проекта
1. Откройте VS Code
2. `File` → `Open Folder...` → Выберите папку с проектом
3. VS Code предложит установить Python extension - установите

### Шаг 3: Создание виртуального окружения
В VS Code нажмите `Ctrl+Shift+` (или `Terminal` → `New Terminal`):

```bash
# Windows
python -m venv .venv

# macOS/Linux  
python3 -m venv .venv
```

**Выбор интерпретатора в VS Code:**
- Нажмите `Ctrl+Shift+P`
- Введите: `Python: Select Interpreter`
- Выберите: `./.venv/bin/python` (или `./.venv/Scripts/python.exe` на Windows)

### Шаг 4: Установка зависимостей
```bash
# Активируйте venv (если не активировано автоматически)
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Установка пакетов
pip install -r requirements.txt
```

### Шаг 5: Создание бота в BotFather
1. Откройте Telegram, найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Придумайте название и username (должен заканчиваться на `bot`)
4. **Сохраните полученный TOKEN** - он понадобится для .env

### Шаг 6: Настройка Google Sheets
1. Создайте новую Google таблицу: [sheets.new](https://sheets.new)
2. Первый лист должен называться "Sheet1" (по умолчанию)
3. Скопируйте ID таблицы из URL (между `/d/` и `/edit`)

**Создание Service Account:**
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или используйте существующий
3. Включите Google Sheets API: `APIs & Services` → `Library` → "Google Sheets API"
4. Создайте Service Account:
   - `IAM & Admin` → `Service Accounts`
   - `Create Service Account`
   - Дайте роль `Editor`
   - Создайте ключ JSON: `Keys` → `Add Key` → `JSON`
   - Файл скачается автоматически - переименуйте в `service_account.json`

**Доступ к таблице:**
- Откройте `service_account.json`, найдите поле `client_email`
- Откройте Google Sheets → `Share` → добавьте этот email с правами `Editor`

### Шаг 7: Заполнение .env
Скопируйте файл и заполните:
```bash
cp .env.example .env
```

Заполните переменные:
```
TELEGRAM_BOT_TOKEN=токен_из_BotFather
WEBHOOK_URL=пока_оставьте_пустым_или_введите_ngrok_после_шага_9
GOOGLE_SHEETS_ID=id_вашей_таблицы
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=./service_account.json
MANAGER_CHAT_ID=ваш_telegram_chat_id
ADMIN_CHAT_IDS=ваш_telegram_chat_id
WEBHOOK_SECRET=любая_случайная_строка_например_abc123def456
```

**Как получить MANAGER_CHAT_ID:**
- Напишите [@userinfobot](https://t.me/userinfobot) в Telegram
- Или временно оставьте пустым, запустите бота, посмотрите логи - там будет ваш chat_id

### Шаг 8: Локальный запуск
```bash
# В папке проекта с активированным venv
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Откройте в браузере: http://localhost:8000/health
Должно показать: `{"status": "ok"}`

### Шаг 9: Получение публичного URL
Для работы webhook нужен публичный HTTPS URL.

**Вариант A: ngrok (проще)**
1. Установите: [ngrok.com/download](https://ngrok.com/download)
2. Зарегистрируйтесь, получите authtoken
3. Запустите:
```bash
ngrok http 8000
```
4. Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)

**Вариант B: Cloudflare Tunnel**
```bash
# Установите cloudflared
cloudflared tunnel --url http://localhost:8000
```

**Обновите .env:**
```
WEBHOOK_URL=https://ваш-ngrok-url/webhook
```

### Шаг 10: Установка webhook
```bash
# В другом терминале (первый должен быть запущен с uvicorn)
python tools/set_webhook.py
```

Должно показать: ✅ Webhook успешно установлен!

### Шаг 11: Быстрая проверка
В Telegram:
1. Найдите своего бота по username
2. Отправьте `/start`
3. Должно показаться приветствие и 2 кнопки
4. Нажмите "Оставить заявку" и пройдите все шаги
5. Проверьте Google Sheets - там появилась строка с заявкой

---

## 📁 Структура проекта

```
lead-intake-bot/
├── app/
│   ├── __init__.py       # Инициализация пакета
│   ├── main.py           # FastAPI приложение, webhook endpoint
│   ├── bot.py            # Логика бота, обработчики
│   ├── state.py          # FSM состояния в памяти
│   ├── config.py         # Загрузка YAML конфигов
│   ├── validators.py     # Валидация телефонов
│   └── sheets.py         # Google Sheets интеграция
├── configs/
│   └── clients/
│       ├── default.yaml        # Конфиг по умолчанию
│       └── sample_agency.yaml  # Пример для агентства
├── tools/
│   └── set_webhook.py    # Скрипт установки webhook
├── .env.example          # Шаблон переменных окружения
├── requirements.txt      # Зависимости Python
└── README.md            # Эта документация
```

---

## 🎨 Добавление новых клиентов

Чтобы добавить клиента без изменения кода:

1. Скопируйте `configs/clients/sample_agency.yaml`
2. Переименуйте в `configs/clients/myclient.yaml`
3. Отредактируйте тексты и настройки
4. Ссылка для клиента: `t.me/your_bot?start=myclient`

---

## 🚀 Деплой на Render (бесплатно)

**Render** - простая платформа для хостинга.

### Шаги:
1. Зарегистрируйтесь на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите GitHub репозиторий или загрузите файлы
4. Настройки:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Добавьте переменные окружения (Environment Variables) - все из .env
6. Для `GOOGLE_SERVICE_ACCOUNT_JSON_PATH`: 
   - Загрузите JSON файл как Secret File
   - Или вставьте содержимое JSON в переменную
7. Deploy!

**После деплоя:**
- Ваш URL будет: `https://leadbot-xxx.onrender.com`
- Обновите `WEBHOOK_URL` в Environment Variables
- Зайдите в Shell на Render и выполните: `python tools/set_webhook.py`

---

## 🔧 Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather | `123456:ABC-DEF...` |
| `WEBHOOK_URL` | Публичный URL + /webhook | `https://domain.com/webhook` |
| `GOOGLE_SHEETS_ID` | ID Google таблицы | `1ABC...` |
| `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | Путь к JSON ключу | `./service.json` |
| `MANAGER_CHAT_ID` | ID для уведомлений | `123456789` |
| `ADMIN_CHAT_IDS` | Админы через запятую | `123,456` |
| `WEBHOOK_SECRET` | Секрет для безопасности | `random_string` |

---

## 🐛 Отладка

**Проблема**: Бот не отвечает
- Проверьте: `python tools/set_webhook.py` показывает успех?
- Проверьте логи: есть ли ошибки при обработке сообщений?
- Проверьте ngrok: работает ли туннель?

**Проблема**: Не сохраняется в Google Sheets
- Проверьте, что service_account.json имеет доступ к таблице
- Проверьте GOOGLE_SHEETS_ID
- Посмотрите логи ошибок

**Проблема**: Менеджер не получает уведомления
- Проверьте MANAGER_CHAT_ID
- Убедитесь что бот может писать менеджеру (менеджер должен написать боту первым)

---

## ✅ Чеклист для сдачи клиенту

- [ ] Бот создан в BotFather
- [ ] Google Sheets настроена и доступна
- [ ] .env заполнен корректно
- [ ] Бот отвечает на /start
- [ ] Заявка заполняется полностью
- [ ] Данные появляются в Google Sheets
- [ ] Менеджер получает уведомление в Telegram
- [ ] Deep link с client_key работает
- [ ] Команда /ping работает для администратора

---

## 📞 Поддержка

Если что-то не работает:
1. Проверьте логи в терминале
2. Проверьте .env файл
3. Убедитесь что webhook установлен
4. Проверьте права доступа к Google Sheets
