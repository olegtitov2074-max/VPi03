# Памятка: VK-бот сообщества на vkbottle (Long Poll)

Краткая шпаргалка по официальной документации vkbottle для бота **сообщества**, работающего
через **Long Poll**. Все формулировки и примеры взяты из документации
<https://vkbottle.readthedocs.io/ru/latest/> (ссылки в разделе 7).

---

## 1. Назначение vkbottle

- Фреймворк для работы с VK API: high-level инструменты для ботов, low-level (API, Polling,
  Callback, HTTP-клиент, обработка исключений), дополнительные инструменты (клавиатуры,
  шаблоны, storage, форматирование) и кастомизация зависимостей.
- **Асинхронный по умолчанию**: все обращения к API — корутины, вызываются через `await`.
- Полная типизация методов, ответов и ошибок (генерируется пакетом `vkbottle-types`),
  поэтому подсказки IDE показывают структуру ответа.
- `Bot` — класс исключительно для **групп**; для юзербота используется отдельный интерфейс `User`.
- Имена методов — в `snake_case` вместо `camelCase`, сигнатуры совпадают с документацией VK.

## 2. Установка

- Отдельной страницы про установку на сайте документации нет; команда установки приведена в
  официальном README репозитория (ссылка «Go to repository» в шапке docs):
  ```console
  pip install vkbottle
  ```
- Зависимости: `aiohttp` идёт вместе с vkbottle — его не нужно ставить отдельно
  (FAQ → «Asyncio»).
- Типы обновляются отдельной командой (нужно, если ловите `Pydantic ValidationError`):
  ```console
  pip install git+https://github.com/vkbottle/types -U
  ```
- Python: `await` допустим только внутри `async`-функций; корутину без `await` не выполнится.
- **В этом проекте** `vkbottle==4.11.0` и `vkbottle-types` уже зафиксированы в
  `requirements.txt` и стоят в `venv` — ничего доустанавливать не нужно.

## 3. Bot, Labeler и Message

### `Bot`

```python
from vkbottle.bot import Bot

bot = Bot(token="token")   # или Bot(api=api)
```

Обязателен `token` **или** `api`. Атрибуты инстанса:

| Атрибут | Назначение |
| --- | --- |
| `bot.api` | работа с VK API (типизированные методы + `request`/`request_many`) |
| `bot.router` | роутер — конечная точка обработки событий |
| `bot.labeler` / `bot.on` | лейблер (`.on` — синоним для краткости) |
| `bot.polling` | Long Poll |
| `bot.callback` | Callback API |
| `bot.error_handler` | хендлер исключений |
| `bot.loop_wrapper` | управление ивент-лупом, `startup`/`shutdown`/таски |

### Labeler

- «Удобная оболочка над роутерами»; хендлеры создаются декораторами лейблера.
- Три декоратора сообщений: `.message` (беседы + личные), `.chat_message` (только беседы),
  `.private_message` (только личные диалоги). Они лишь предустанавливают `PeerRule`
  (`message` — не предустанавливает, `chat_message` — `PeerRule(True)`,
  `private_message` — `PeerRule(False)`).
- `bl = BotLabeler()` + `bot.labeler.load(bl)` — разбиение хендлеров по файлам/модулям.
- `auto_rules` — правила, накладываемые на все хендлеры сообщений лейблера
  (для сырых событий — `raw_event_auto_rules`).
- `custom_rules` — свои правила под короткие шорткаты; правило может вернуть `dict`,
  который распаковывается в аргументы хендлера.
- Хендлеры по умолчанию **блокирующие**: нашёл подходящий — остальные не проверяются.

### `Message`

- Объект события; полезные поля: `text`, `from_id`, `peer_id`, `chat_id`, `mention`,
  `reply_message`, `fwd_messages`.
- `await message.answer("текст")` — шорткат к `messages.send`: не требует `peer_id`
  и `random_id`.
- `message.ctx_api` — доступ к API из хендлера (тот же `API`, что у бота).
- `message_view.replace_mention = True` — автоудаление упоминания бота с записью
  данных в `Message.mention` (нужно для `MentionRule`).

## 4. Приём новых сообщений

```python
from vkbottle.bot import Bot, Message

bot = Bot(token="token")


@bot.on.message(text="Привет")
async def hi_handler(message: Message):
    user = (await bot.api.users.get(message.from_id))[0]
    await message.answer(f"Привет, {user.first_name}")


@bot.on.message(command=("ping", 0))
async def ping_handler(message: Message):
    await message.answer("pong")
```

- Декоратор = правило отбора: если событие подходит под правило, сработает хендлер.
- Правила (`ABCRule`) реализуют один асинхронный метод `check`: `False` — не подошло,
  `True`/словарь — подошло (словарь распаковывается в `**kwargs` хендлера).
- Способы задать правило: инстанс правила напрямую (`@bot.on.message(CommandRule(...))`)
  или шорткат по имени из `custom_rules` (`@bot.on.message(command=("say", 1))`).
- Частые правила: `text` (`VBMLRule`), `command` (`CommandRule`), `from_chat`, `from_user`,
  `peer_ids`, `mention`, `regexp`/`regex`, `payload*`, `func`, `coro`, `state`, `fuzzy`,
  `length`, `sticker`, `attachment`, `action`, `lev` (deprecation → `fuzzy`).
- Все встроенные правила работают только с `Message`/`MessageEvent`; для сырых событий
  нужна своя реализация правила.
- **Обязательные настройки в VK:** у сообщества включён Long Poll, отмечено событие
  «Новые сообщения», и стабильная версия лонгполла — `5.131`. Без этого бот молчит.
- Не блокируйте луп: `await asyncio.sleep(...)` вместо `time.sleep(...)`, а для HTTP —
  `AiohttpClient`/aiohttp вместо `requests` (FAQ → «Asyncio»).

## 5. Запуск Long Poll

```python
bot.run_forever()   # синхронный запуск (из обычного скрипта)
await bot.run_polling()  # асинхронный запуск (внутри async-кода)
```

- `bot.run_forever()` добавляет `run_polling` в таски `bot.loop_wrapper` и вызывает
  `bot.loop_wrapper.run()`; `bot.run_polling()` — асинхронный запуск лонгполла.
- `LoopWrapper` управляет ивент-лупом и хранит корутины `on_startup` (до старта лупа)
  и `on_shutdown` (при остановке), а также шаблоны `@lw.interval(seconds=...)`
  (повтор) и `@lw.timer(seconds=...)` (отложенный запуск).
- У `Bot` свой `LoopWrapper` (`bot.loop_wrapper`), он запускается при `bot.run_forever()`.
- Низкоуровневый `Polling` (`ABCPolling`): методы `get_server`, `get_event`, `listen`,
  `construct`; параметры `BotPolling` — `api`, `group_id`/`user_id`, `wait`, `rps_delay`.
  Свой поллинг можно написать, унаследовав `ABCPolling`.
- Минимальный шаблон бота: `Bot(token=...)` → хендлеры через `@bot.on.*` → `bot.run_forever()`.

## 6. Обработка ошибок

### `try ... except VKAPIError`

```python
from vkbottle import VKAPIError

try:
    await api.messages.send(peer_id=1, message="привет!", random_id=0)
except VKAPIError[902] as e:   # конкретный код — ловится первым
    print("не могу отправить из-за настроек приватности")
except VKAPIError as e:        # все остальные ошибки VK
    print("не могу отправить:", e.code, e.error_msg)
```

- `VKAPIError` — подтип `CodeException`; поля: `code: int`, `error_msg: str`.
- Список кодов ошибок VK: <https://dev.vk.ru/reference/errors>.
- Спецошибка `CaptchaError`: поля `captcha_sid`, `captcha_img`.

### `ErrorHandler` (в т.ч. `bot.error_handler`)

```python
from vkbottle import VKAPIError

@bot.error_handler.register_error_handler(VKAPIError[902])
async def unable_to_write_handler(e: VKAPIError):
    print("человек не разрешил отправлять сообщения", e)

@bot.error_handler.register_undefined_error_handler
async def undefined_error_handler(e: Exception):
    print("неизвестная ошибка", e)
```

- Методы `ErrorHandler`: `register_error_handler` (по типам ошибок, можно сразу несколько),
  `register_undefined_error_handler`, `handle`, `catch`.
- `handle` передаёт исключение зарегистрированному хендлеру, а если его нет — пробрасывает
  исключение дальше; `catch` — декоратор, ловящий ошибки функции.
- Параметры конструктора: `redirect_arguments` (передаёт аргументы функции в хендлер ошибки,
  вместе с ботом — контекст из правил и мидлварей) и `raise_exceptions` (необработанные
  исключения пробрасываются).
- `VKAPIError[6, 9]` — сразу несколько кодов одной ошибки (например, превышение лимитов).

## 7. Источники

- Хаб / оглавление: <https://vkbottle.readthedocs.io/ru/latest/>
- Туториал: <https://vkbottle.readthedocs.io/ru/latest/tutorial/>
- Первый бот: <https://vkbottle.readthedocs.io/ru/latest/tutorial/first-bot/>
- Правила: <https://vkbottle.readthedocs.io/ru/latest/tutorial/rules/> и
  <https://vkbottle.readthedocs.io/ru/latest/high-level/builtin-rules/>
- Handler: <https://vkbottle.readthedocs.io/ru/latest/high-level/handling/handler/>
- Bot: <https://vkbottle.readthedocs.io/ru/latest/high-level/bot/>
- Labeler: <https://vkbottle.readthedocs.io/ru/latest/high-level/bot/labeler/>
- Разделение кода: <https://vkbottle.readthedocs.io/ru/latest/tutorial/code-separation/>
- Polling: <https://vkbottle.readthedocs.io/ru/latest/low-level/polling/>
- Loop Wrapper: <https://vkbottle.readthedocs.io/ru/latest/tools/loop-wrapper/>
- Обработка ошибок: <https://vkbottle.readthedocs.io/ru/latest/tutorial/error-handling/> и
  <https://vkbottle.readthedocs.io/ru/latest/low-level/exception_handling/error-handler/>
- FAQ (asyncio, токены, типы): <https://vkbottle.readthedocs.io/ru/latest/tutorial/faq/>
- Коды ошибок VK: <https://dev.vk.ru/reference/errors>
- Установка (README официального репозитория, ссылка «Go to repository» в шапке docs):
  <https://github.com/vkbottle/vkbottle>
