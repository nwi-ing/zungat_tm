# zungat_tm

Интеграция между Bitrix24 и TaxiMaster (TM): учёт водителей, рассрочек, автосписаний по графику и списаний арестов. Работает как локальное приложение Bitrix24 (OAuth) и как набор фоновых Celery-задач.

## Архитектура

```
apps/
  core/                  # платформенный слой: логи, вкл/выкл автоматики, Celery-обвязка
    models/              # LogEntry, AutomationSetting
    services/log_run.py  # контекст-менеджер: одна LogEntry на запуск задачи/вебхука
    services/automation.py  # is_module_enabled(module_key)
    tasks/base.py        # automation_task(module_key) — декоратор для Celery-задач
    views/, templates/   # HTMX-интерфейс: /core/logs/, /core/settings/

  domain/
    recovery/            # списание ареста: сверяет пополнения TM с арестом рассрочки
    autopayment/         # автосписание по графику рассрочки
    writeoff/            # ручное списание (вебхук из Bitrix, кнопка "списать")
    cencel_payment/      # отмена платежа (вебхук из Bitrix, кнопка "отменить")
    _shared/              # НЕ Django-app: общий PaymentContextLoader (Payment→Deal→PaymentRule)
                          # для writeoff и cencel_payment

  integrations/
    bx24/                # типизированный клиент Bitrix24 (pydantic-схемы, CRM smart-process)
    tm_driver/            # типизированный клиент TaxiMaster
```

Каждый `Application`-класс (`RecoveryApplication`, `AutopaymentApplication`, `ManualWriteoffApplication`, `CencelPaymentApplication`) принимает `bx_client=None, tm_client=None` в конструкторе — по умолчанию создаёт реальных клиентов, но в тестах подставляются fake-клиенты (`apps/integrations/*/testing/fake_client.py`).

Gating (`AutomationSetting.enabled`) и запись `LogEntry` — ответственность декоратора `automation_task`/контекст-менеджера `log_run`, а не самих `Application`-классов.

## Планировщик

Celery + Celery Beat (`django_celery_beat`, DatabaseScheduler) + Redis. `recovery` и `autopayment` запускаются ежедневно в 22:00 (Europe/Moscow), настройка расписания — через `PeriodicTask`/`CrontabSchedule` в БД (не в коде).

`writeoff` и `cencel_payment` — не через Celery, а прямые вебхуки от Bitrix (`/apps/writeoff/accept/`, `/apps/writeoff/cencel/`), обрабатываются синхронно при запросе. У них **нет** тумблера в `AutomationSetting` — они всегда активны, раз Bitrix шлёт запрос.

## Ключевая бизнес-логика (не очевидна из кода)

### `PaymentRuleState` (поле `is_active` / `ufCrm15RuleState` в Bitrix)
- `SCHEDULED = 269` — обычный активный график автосписаний.
- `MID_RECOVERY = 271` — рассрочка ещё не закрыта, но временно не на графике (например, идёт списание арестов). Только `recovery` должен её видеть; `autopayment` — нет.
- Любое другое значение / отсутствие рассрочки — оба модуля её не трогают.

### Автосписание: баланс TM **намеренно** уходит в минус
`autopayment` всегда создаёт в TM `expense`-операцию на **полную** сумму по графику, независимо от текущего баланса водителя — баланс может и должен уходить в минус, это ожидаемое поведение, а не баг. Поле `FactPayment.opportunity`/`arest_sum` в Bitrix — это **только бухгалтерский split** одной и той же операции («сколько покрыто существующим балансом» / «сколько ушло в долг»), а не ограничение на само списание. `recovery` существует именно для того, чтобы потом «подчищать» этот накопленный минус по мере поступления новых пополнений.

### Recovery: сверка арестов с реальными пополнениями TM
Для каждого водителя берётся **самая ранняя** `arested_date` среди всех его рассроченных installments (не по каждой сделке отдельно!), запрашиваются TM-операции типа `receipt` за этот период, и сумма жадно распределяется по installments в порядке их появления, ограничиваясь `deal.total_arest_sum` каждой сделки. Дедупликация повторной обработки одних и тех же операций — через `DriverSyncState.last_processed_operation_id` (watermark на водителя).

**Важно**: поле `PaymentRule.arested_date` может **само измениться** после создания списания — похоже, это автоматика на стороне Bitrix (не в Django-коде), которая переустанавливает дату при изменении ареста. Значит для ретроспективного аудита («а правда ли списание было подтверждено реальным пополнением») нельзя доверять текущему значению `arested_date` — оно могло быть перезаписано уже после факта. Нужно смотреть на TM-операции в более широком окне.

### Bitrix авто-реконсиляция (не в Django-коде)
Bitrix24 сам, своей автоматикой на смарт-процессе, при создании `FactPayment` со stage `SUCCESS` **автоматически** добавляет `opportunity`/`arest_sum` в поля сделки `Deal.installment_pay_sum`/`Deal.total_arest_sum`, и автоматически закрывает рассрочку, когда она полностью выплачена. Это позволяет автосписанию и recovery всегда читать **актуальные** суммы напрямую из `Deal`, не считая накопленную историю платежей самим.

### `cencel_payment` vs `writeoff`
- `cencel_payment` (отмена платежа) — **намеренно** не проверяет баланс/перерасход. Отмена всегда проходит.
- `writeoff` (ручное списание) — **проверяет** баланс/перерасход (`PaymentCalculation`, `CalculateError`), это не дублирующая, а другая логика — не унифицировать.
- Общий код (парсинг вебхука Bitrix, загрузка Payment→Deal→PaymentRule) вынесен в `apps/integrations/bx24/lib/services/webhook.py` и `apps/domain/_shared/services/payment_loader.py`.

## Тестирование

```
pytest                    # весь репозиторий, никогда не обращается к реальным TM/Bitrix
```

Fake-клиенты — простой duck-typing (без `Protocol`/ABC, в проекте их нигде нет). `conftest.py` в корне даёт фикстуры `fake_bx_client()`, `fake_tm_client()`.

**Готча**: `Operation.cancelled_oper_id`/`cancelled_by_oper_id` по умолчанию `None` в pydantic-схеме, но `_checkOperation` сравнивает `!= 0` (что исключает `None`). Реальный TM API всегда возвращает явный `0` — при сидировании "валидных" операций в тестах нужно явно передавать `cancelled_oper_id=0, cancelled_by_oper_id=0`.

## Деплой

Продакшен — сервер `zungat` (алиас в `~/.ssh/config`, `10.0.0.24`, пользователь `nsa`, репозиторий в `~/projects/zungat_tm`). Docker Compose: `web` (Django/gunicorn) + `redis` + `celery_worker` + `celery_beat`, все на статических IP в bridge-сети `192.168.10.0/24` (`.10`/`.11`/`.12`/`.13`). Порт наружу **не пробрасывается** — nginx на хосте сервера проксирует `test.ntwrk.ing` напрямую на `192.168.10.10:8000` (это работает только на Linux-хосте; на Windows Docker Desktop контейнерные IP из host недоступны — для локальной разработки нужен `docker-compose.override.yml` с `ports: ["8000:8000"]`, он в `.gitignore`).

Деплой: `git push` в `origin/main` → на сервере `git pull` → `docker compose up -d --build` (мигрирует БД сервера **на месте**, без замены — `data/db.sqlite3` не в git, у сервера своя БД с реальными токенами `BitrixAuth`/`TaxiMasterAuth`).

**Готча**: `django-celery-beat` требует пину версии `>=2.9.0` для совместимости с Django 6.0.5 (`2.7.0` требует `Django<5.2`).

**Готча**: sqlite нужен `PRAGMA journal_mode=WAL` (`DATABASES["default"]["OPTIONS"]`) — иначе конкурентная запись Celery worker/beat/gunicorn ловит "database is locked".

**Готча (миграции)**: data-миграция, зависящая от `django_celery_beat`, должна указывать зависимость на **последнюю** миграцию этого приложения (`0019_alter_periodictasks_options`), а не на `0001_initial` — поля вроде `CrontabSchedule.timezone` появляются только в поздних миграциях, и на свежей тестовой БД порядок применения может отличаться от продакшен-БД.

## Полезные команды

```bash
docker compose up -d --build          # поднять/пересобрать весь стек
docker compose exec web python manage.py shell   # реальные (!) TM/Bitrix клиенты по умолчанию
pytest -q                             # тесты, только fake-клиенты
python manage.py makemigrations --check --dry-run
```
