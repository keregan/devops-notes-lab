# DevOps Notes Lab

Учебное Flask-приложение с Redis, Docker Compose и проверками в GitHub Actions.

При каждом открытии главной страницы приложение увеличивает счётчик в Redis. Благодаря volume значение сохраняется между перезапусками контейнеров.

## Что реализовано

- Python-приложение на Flask;
- реальное подключение приложения к Redis;
- хранение счётчика посещений в Redis;
- закрепление runtime-образов Python и Redis по версии и SHA256 digest;
- запуск всего стека через Docker Compose;
- healthcheck контейнеров и ожидание готовности Redis;
- endpoints `/health` и `/ready`;
- endpoint `/info` с версией, окружением и hostname контейнера;
- endpoint `/metrics` в формате Prometheus;
- валидируемый заголовок `X-Request-ID` для сопоставления запросов и логов;
- защитные HTTP-заголовки CSP без `'unsafe-inline'`, `nosniff`, `DENY` и `no-referrer`;
- единый безопасный JSON-формат ошибок 404, 500 и 503;
- структурированные JSON-логи HTTP-запросов и ошибок Redis;
- unit-тесты без внешнего Redis;
- проверка Python-кода через Ruff;
- контроль покрытия тестами с минимальным порогом 85%;
- еженедельное обновление Python-зависимостей и GitHub Actions через Dependabot;
- обязательный аудит Python-зависимостей через `pip-audit` в обоих CI;
- локальный стек Prometheus + Grafana с автоматически настроенным dashboard;
- changelog и автоматическое создание GitHub Release по тегу версии;
- интеграционная HTTP-проверка полного Compose-стека;
- CI для push в `main`, pull request и ручного запуска.

## Архитектура

```text
Браузер -> Flask :8000 -> Redis :6379 -> volume redis_data
```

Порт Redis указан через `expose`, но не публикуется на компьютере через `ports`: приложение обращается к нему по имени сервиса `redis` во внутренней сети Docker Compose. Оба CI дополнительно проверяют, что публичное сопоставление для порта `6379` отсутствует.

## Структура проекта

```text
devops-notes-lab/
├── .github/dependabot.yml
├── .github/workflows/ci.yml
├── .github/workflows/release.yml
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/
├── notes/
├── practice/
├── static/styles.css
├── templates/index.html
├── tests/test_app.py
├── .dockerignore
├── .env.example
├── .gitignore
├── app.py
├── CHANGELOG.md
├── docker-compose.monitoring.yml
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
├── ROADMAP.md
├── VERSION
└── README.md
```

## Запуск

1. Создать локальный файл конфигурации:

```powershell
Copy-Item .env.example .env
```

2. Проверить итоговую конфигурацию Compose:

```powershell
docker compose config
```

3. Собрать и запустить сервисы:

```powershell
docker compose up -d --build --wait --wait-timeout 60
```

4. Открыть `http://localhost:8084`.

Compose сначала ждёт успешный healthcheck Redis, затем запускает приложение и завершает команду только после успешного `/ready`.

Порт можно изменить в локальном `.env`:

```dotenv
APP_PORT=8084
```

## Проверка работоспособности

| Endpoint | Назначение | Успешный ответ |
|---|---|---|
| `/health` | Проверяет, что Flask-приложение запущено | HTTP 200, `status: ok` |
| `/ready` | Проверяет соединение приложения с Redis | HTTP 200, `status: ready` |
| `/info` | Показывает метаданные развёрнутой версии | HTTP 200, `version`, `environment`, `hostname` |
| `/metrics` | Отдаёт метрики приложения, Redis и посещений | Prometheus text format |

Ошибки 404, 500 и 503 возвращаются в едином базовом формате и содержат
идентификатор запроса для поиска события в логах:

```json
{
  "status": "error",
  "code": 404,
  "message": "Resource not found",
  "request_id": "7ac6e5a7-1fd4-45f5-8dcb-45d0d932a90c"
}
```

Клиентский `X-Request-ID` сохраняется, если содержит от 1 до 128 латинских
букв, цифр или символов `.`, `_`, `-`. Некорректное значение заменяется UUID.

Проверка из PowerShell:

```powershell
Invoke-RestMethod http://localhost:8084/health
Invoke-RestMethod http://localhost:8084/ready
Invoke-RestMethod http://localhost:8084/info
Invoke-WebRequest http://localhost:8084/metrics
```

Проверка Redis внутри контейнера:

```powershell
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli get devops-notes-lab:visits
```

## Prometheus и Grafana

Стек мониторинга запускается отдельным Compose overlay, поэтому обычный запуск приложения не загружает дополнительные сервисы:

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d --build --wait --wait-timeout 120
```

После запуска доступны:

- приложение: `http://localhost:8084`;
- Prometheus: `http://localhost:9090`;
- Grafana: `http://localhost:3000`;
- готовый dashboard: папка `DevOps Notes Lab`, dashboard `DevOps Notes Lab`.

Учётные данные Grafana берутся из `.env`. В `.env.example` указаны учебные значения `admin` / `change-me`; перед использованием вне локального компьютера пароль необходимо заменить.

Чтобы на графике появились данные о посещениях, несколько раз откройте главную страницу приложения. Prometheus забирает `/metrics` каждые 5 секунд, а datasource и dashboard создаются в Grafana автоматически.

Остановка мониторинга и приложения:

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml down
```

## Тесты

Локальный запуск всех проверок качества:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip_audit --strict --progress-spinner off -r requirements.txt
python -m ruff check .
python -m coverage run -m unittest discover -s tests -v
python -m coverage report
```

Параметры Ruff и coverage.py, включая обязательный порог 85%, находятся в `pyproject.toml`. Очерёдность следующих обновлений проекта записана в [ROADMAP.md](ROADMAP.md).

## GitHub Actions

Workflow `.github/workflows/ci.yml` выполняет:

1. установку Python-зависимостей;
2. аудит Python-зависимостей на известные уязвимости;
3. проверку кода через Ruff;
4. запуск unit-тестов и проверку покрытия не ниже 85%;
5. проверку основной и monitoring-конфигураций Docker Compose;
6. сборку образа и запуск Compose-стека;
7. ожидание `/ready`;
8. проверку `/health`, `/ready` и главной страницы;
9. вывод логов при ошибке и удаление тестовых контейнеров.

## Dependabot

Конфигурация `.github/dependabot.yml` каждый понедельник проверяет обновления Python-зависимостей и GitHub Actions. Minor- и patch-версии группируются в отдельные pull requests, а major-обновления остаются отдельными для более внимательной проверки. Каждый созданный pull request проходит обычный GitHub Actions workflow.

## GitLab CI

Pipeline `.gitlab-ci.yml` состоит из двух этапов:

1. `unit_tests` устанавливает Python-зависимости, запускает `pip-audit`, Ruff, unit-тесты и проверяет покрытие;
2. `docker_compose_test` собирает и запускает Compose-стек через Docker-in-Docker, ждёт готовности приложения и проверяет `/health`, `/ready` и главную страницу.

После выполнения pipeline контейнеры и тестовые volumes удаляются, а файл `compose.log` сохраняется как artifact. Для Docker-in-Docker GitLab Runner должен поддерживать privileged mode.

## Выпуск новой версии

Текущая версия хранится в `VERSION`, а заметные изменения — в `CHANGELOG.md`. Workflow `.github/workflows/release.yml` запускается после отправки тега формата `vX.Y.Z`, проверяет совпадение тега с `VERSION` и автоматически создаёт GitHub Release.

Перед релизом:

1. обновите `VERSION`, версию в `.env.example`, Compose и CI;
2. перенесите готовые пункты из секции `Unreleased` в новую версию `CHANGELOG.md`;
3. убедитесь, что обычный CI в `main` завершился успешно;
4. создайте и отправьте тег соответствующей версии.

Пример для версии `1.3.0`:

```powershell
git tag -a v1.3.0 -m "Релиз 1.3.0"
git push origin v1.3.0
```

GitHub CLI создаёт release только для уже существующего тега и автоматически формирует release notes.

## Логи и остановка

Каждый завершённый HTTP-запрос записывается одной JSON-строкой с `request_id`, методом, путём, HTTP-статусом и длительностью в миллисекундах:

```json
{"timestamp":"2026-08-15T12:00:00+00:00","level":"INFO","logger":"app","message":"HTTP request completed","event":"http_request_completed","request_id":"7ac6e5a7-1fd4-45f5-8dcb-45d0d932a90c","method":"GET","path":"/health","status_code":200,"duration_ms":0.321}
```

```powershell
docker compose ps
docker compose logs -f app
docker compose down
```

Чтобы также удалить сохранённый счётчик Redis:

```powershell
docker compose down --volumes
```

> Команда с `--volumes` удаляет данные Redis без возможности восстановления.
