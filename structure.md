├─ config.py             # Конфигурация: токены, API-ключи
├─ handlers/
│   ├─ __init__.py
│   ├─ commands.py       # Обработчики команд (/start, /help)
│   └─ messages.py       # Обработчики обычных сообщений
├─ services/
│   ├─ __init__.py
│   └─ llm_service.py    # Взаимодействие с OpenAI или другой LLM
├─ utils/
│   ├─ __init__.py
│   └─ helpers.py        # Вспомогательные функции
├─ data/                 # Для хранения истории, базы знаний и т.п.
└─ requirements.txt      # Зависимости проекта