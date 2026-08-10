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
- заголовок `X-Request-ID` для сопоставления запросов и логов;
- unit-тесты без внешнего Redis;
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
├── .github/workflows/ci.yml
├── notes/
├── practice/
├── templates/index.html
├── tests/test_app.py
├── .dockerignore
├── .env.example
├── .gitignore
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
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

## Тесты

Локальный запуск unit-тестов:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## GitHub Actions

Workflow `.github/workflows/ci.yml` выполняет:

1. установку Python-зависимостей;
2. запуск unit-тестов;
3. проверку `docker compose config`;
4. сборку образа и запуск Compose-стека;
5. ожидание `/ready`;
6. проверку `/health`, `/ready` и главной страницы;
7. вывод логов при ошибке и удаление тестовых контейнеров.

## GitLab CI

Pipeline `.gitlab-ci.yml` состоит из двух этапов:

1. `unit_tests` устанавливает Python-зависимости и запускает unit-тесты;
2. `docker_compose_test` собирает и запускает Compose-стек через Docker-in-Docker, ждёт готовности приложения и проверяет `/health`, `/ready` и главную страницу.

После выполнения pipeline контейнеры и тестовые volumes удаляются, а файл `compose.log` сохраняется как artifact. Для Docker-in-Docker GitLab Runner должен поддерживать privileged mode.

## Логи и остановка

```powershell
docker compose ps
docker compose logs -f
docker compose down
```

Чтобы также удалить сохранённый счётчик Redis:

```powershell
docker compose down --volumes
```

> Команда с `--volumes` удаляет данные Redis без возможности восстановления.
