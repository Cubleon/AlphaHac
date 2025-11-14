db_service

Реализация на PostgreSQL через asyncpg.

| Таблица         | Описание                              |
| --------------- | ------------------------------------- |
| `users`         | Пользователи Telegram                 |
| `projects`      | Рабочие проекты пользователя          |
| `conversations` | Чаты внутри проектов                  |
| `messages`      | Сообщения (user / assistant / system) |
| `notifications` | Уведомления пользователя              |
| `usage`         | Статистика использования              |
| `settings`      | Настройки пользователя                |
| `api_logs`      | Логи API-запросов                     |

Структура “матрёшки” (One-to-Many)

User → много Projects

Project → много Conversations

Conversation → много Messages

User → много Notifications

User → много Settings

User → много Usage записей

User → много API Logs

МЕТОДЫ

Users
| Метод                                                                          | Описание                                                   |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `create_user(telegram_id, username?, first_name?, last_name?, language_code?)` | Создаёт нового пользователя                                |
| `get_user_by_telegram(telegram_id)`                                            | Получить пользователя по Telegram ID                       |
| `ensure_user(tg_user: dict)`                                                   | Проверяет, есть ли пользователь, создаёт при необходимости |

Projects

| Метод                                             | Описание                            |
| ------------------------------------------------- | ----------------------------------- |
| `create_project(user_id, name, description?)`     | Создаёт новый проект                |
| `list_projects(user_id, limit=50)`                | Список проектов пользователя        |
| `get_project(project_id)`                         | Получить данные проекта             |
| `update_project(project_id, name?, description?)` | Изменить проект                     |
| `delete_project(project_id)`                      | Удалить проект                      |
| `touch_project(project_id)`                       | Обновить время последней активности |

Conversations

| Метод                                               | Описание                         |
| --------------------------------------------------- | -------------------------------- |
| `create_conversation(user_id, title?, project_id?)` | Создаёт новый чат                |
| `list_conversations(user_id, limit?, project_id?)`  | Список чатов пользователя        |
| `list_conversations_by_project(project_id, limit?)` | Список чатов конкретного проекта |
| `get_conversation(conv_id)`                         | Получить чат по ID               |
| `touch_conversation(conv_id)`                       | Обновить время активности чата   |


Messages

| Метод                                                                           | Описание                            |
| ------------------------------------------------------------------------------- | ----------------------------------- |
| `save_message(conversation_id, role, content, token_count?, meta?)`             | Сохраняет сообщение                 |
| `get_recent_messages(conversation_id, limit=20)`                                | Последние сообщения                 |
| `get_context_by_token_budget(conversation_id, token_budget, token_counter_fn?)` | Получить контекст под лимит токенов |


Notifications

| Метод                                                                  | Описание                                   |
| ---------------------------------------------------------------------- | ------------------------------------------ |
| `create_notification(user_id, title, body, payload?, due_at?, ntype?)` | Создаёт уведомление                        |
| `list_notifications(user_id, unread_only=False, limit=50)`             | Список уведомлений                         |
| `get_notification(notification_id)`                                    | Получить уведомление                       |
| `mark_notification_read(notification_id)`                              | Отметить как прочитанное                   |
| `mark_all_read(user_id)`                                               | Отметить все уведомления как прочитанные   |
| `get_unread_count(user_id)`                                            | Количество непрочитанных                   |
| `fetch_due_notifications(until, limit=100)`                            | Получить уведомления, срок которых подошёл |
| `mark_delivered(notification_id)`                                      | Отметить уведомление как доставленное      |

Usage & API Logs

| Метод                                                                                 | Описание                             |
| ------------------------------------------------------------------------------------- | ------------------------------------ |
| `increment_usage(user_id, tokens=0, reqs=1)`                                          | Увеличивает статистику использования |
| `get_usage(user_id, since_days=7)`                                                    | Получить статистику за последние дни |
| `log_api(user_id?, conversation_id?, request_payload, response_payload, status='ok')` | Логирует API-запрос                  |

Settings

| Метод                              | Описание                          |
| ---------------------------------- | --------------------------------- |
| `set_setting(user_id, key, value)` | Сохраняет или обновляет настройку |
| `get_setting(user_id, key)`        | Получает значение настройки       |

Utilities

| Метод                                 | Описание                              |
| ------------------------------------- | ------------------------------------- |
| `search_messages(query, limit=20)`    | Поиск сообщений по тексту             |
| `clear_conversation(conversation_id)` | Полное удаление чата и всех сообщений |

