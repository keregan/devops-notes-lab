# Эксплуатационный runbook

Практическая инструкция для одиночного Docker Compose-развёртывания
DevOps Notes Lab. Все команды PowerShell выполняются из корня проекта.

## Область применения

Runbook описывает:

- обновление приложения из Git;
- откат к известному Git-тегу или commit SHA;
- резервное копирование и восстановление именованного тома Redis;
- проверку `/health`, `/ready`, `/metrics`, логов и monitoring-стека.

Перед работой убедитесь, что установлены Git, Docker Engine и Docker Compose v2,
а локальный `.env` заполнен. Команда `docker compose up --wait` должна
поддерживаться установленной версией Compose.

## Быстрая проверка состояния

```powershell
docker compose ps
docker compose exec -T redis redis-cli ping
Invoke-RestMethod http://localhost:8084/health
Invoke-RestMethod http://localhost:8084/ready
Invoke-WebRequest http://localhost:8084/metrics
```

Ожидаемый результат: оба контейнера имеют состояние `healthy`, Redis отвечает
`PONG`, а `/health` и `/ready` возвращают HTTP 200. Если `APP_PORT` изменён,
замените `8084` во всех HTTP-командах.

## Резервное копирование Redis

Redis использует AOF и хранит данные в именованном томе `redis_data`. Начиная с
Redis 7 AOF состоит из нескольких файлов и manifest, поэтому backup сохраняет
всё содержимое `/data`, а не только `dump.rdb`.

Короткая остановка Redis нужна для согласованной копии. В это время `/ready`
будет возвращать HTTP 503, а операции со счётчиком не будут выполняться.

```powershell
$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path (Get-Location) "backups\$backupStamp"
New-Item -ItemType Directory -Force -Path $backupDir

$redisContainer = docker compose ps -q redis
if (-not $redisContainer) { throw "Контейнер Redis не запущен" }
$redisVolume = docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' $redisContainer
$redisImage = docker inspect --format '{{.Config.Image}}' $redisContainer
docker volume inspect $redisVolume
docker compose exec -T redis redis-cli INFO persistence

docker compose stop redis
docker run --rm --user 0:0 --volumes-from $redisContainer --mount "type=bind,source=$backupDir,target=/backup" $redisImage sh -c 'tar -czf /backup/redis-data.tar.gz -C /data .'
docker compose up -d --wait --wait-timeout 60
```

Проверьте, что архив читается, сохраните его хеш и повторно проверьте сервис:

```powershell
docker run --rm --mount "type=bind,source=$backupDir,target=/backup,readonly" $redisImage sh -c 'tar -tzf /backup/redis-data.tar.gz >/dev/null'
Get-FileHash (Join-Path $backupDir "redis-data.tar.gz") -Algorithm SHA256
docker compose exec -T redis redis-cli ping
Invoke-RestMethod http://localhost:8084/ready
```

Архив и его SHA256-хеш необходимо перенести за пределы Docker-хоста. Копия на
том же диске не защищает от отказа диска или потери сервера.

## Восстановление Redis

> **Внимание:** восстановление полностью удаляет текущее содержимое `/data` в
> томе Redis. Сначала проверьте выбранный архив и сделайте отдельный backup
> текущего состояния. Не выполняйте `docker compose down --volumes`.

Укажите каталог нужной резервной копии и сначала проверьте архив без изменения
тома:

```powershell
$backupDir = (Resolve-Path ".\backups\20260918-120000").Path
$redisContainer = docker compose ps -q redis
if (-not $redisContainer) { throw "Сначала запустите стек и повторите команду" }
$redisVolume = docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' $redisContainer
$redisImage = docker inspect --format '{{.Config.Image}}' $redisContainer
docker volume inspect $redisVolume
docker run --rm --mount "type=bind,source=$backupDir,target=/backup,readonly" $redisImage sh -c 'tar -tzf /backup/redis-data.tar.gz >/dev/null'
```

Только после успешной проверки остановите весь стек и восстановите содержимое:

```powershell
docker compose stop
docker run --rm --user 0:0 --volumes-from $redisContainer --mount "type=bind,source=$backupDir,target=/backup,readonly" $redisImage sh -c 'find /data -mindepth 1 -maxdepth 1 -exec rm -rf {} + && tar -xzf /backup/redis-data.tar.gz -C /data'
docker compose up -d --wait --wait-timeout 60
```

Проверьте загруженные данные и готовность приложения:

```powershell
docker compose exec -T redis redis-cli INFO persistence
docker compose exec -T redis redis-cli DBSIZE
docker compose exec -T redis redis-cli GET devops-notes-lab:visits
Invoke-RestMethod http://localhost:8084/ready
```

При ошибке запуска не повторяйте очистку тома. Сохраните логи командой
`docker compose logs --no-color redis app` и вернитесь к проверенной копии.

## Обновление

1. Зафиксируйте текущую ревизию и состояние контейнеров:

```powershell
git rev-parse HEAD
docker compose ps
Invoke-RestMethod http://localhost:8084/ready
```

2. Выполните резервное копирование Redis по разделу выше.
3. Получите изменения и выберите проверенный тег или ветку:

```powershell
git fetch --tags origin
$targetRef = "v1.3.0"
git switch --detach $targetRef
```

4. Проверьте конфигурацию, обновите внешний образ Redis, пересоберите приложение
   и дождитесь готовности:

```powershell
docker compose config --quiet
docker compose pull redis
docker compose build --pull app
docker compose up -d --wait --wait-timeout 60
```

5. Выполните smoke-проверку:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8084/health
Invoke-RestMethod http://localhost:8084/ready
Invoke-RestMethod http://localhost:8084/info
Invoke-WebRequest http://localhost:8084/metrics
docker compose logs --tail 100 app redis
```

Обновление успешно, если контейнеры healthy, `/ready` отвечает HTTP 200,
`/info` показывает ожидаемую версию, а в свежих логах нет повторяющихся ошибок.

## Откат

Используйте commit SHA, сохранённый перед обновлением, или ранее проверенный
релизный тег. Перед откатом создайте ещё одну резервную копию Redis.

```powershell
git fetch --tags origin
$rollbackRef = "v1.3.0"
git switch --detach $rollbackRef
docker compose config --quiet
docker compose build app
docker compose up -d --wait --wait-timeout 60
Invoke-RestMethod http://localhost:8084/ready
Invoke-RestMethod http://localhost:8084/info
```

Откат кода не требует отката данных для текущей версии проекта: приложение не
выполняет миграции Redis. Если будущая версия изменит формат данных, после
отката кода восстановите совместимую копию по отдельному разделу runbook.

После расследования верните deployment-копию на основную ветку командой
`git switch main`; не создавайте рабочие изменения в detached HEAD.

## Диагностика

### Контейнеры и ресурсы

```powershell
docker compose ps -a
docker compose logs --tail 200 app redis
docker compose top
docker compose stats --no-stream
docker system df
docker volume inspect $redisVolume
```

### Приложение и Redis

```powershell
Invoke-WebRequest http://localhost:8084/health
Invoke-WebRequest http://localhost:8084/ready
Invoke-WebRequest http://localhost:8084/metrics
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli INFO persistence
docker compose exec -T redis redis-cli INFO memory
docker compose exec -T redis redis-cli GET devops-notes-lab:visits
```

| Симптом | Что проверить | Следующее действие |
|---|---|---|
| `/health` не отвечает | `docker compose ps`, логи `app` | проверить сборку, порт и запуск Gunicorn |
| `/health` = 200, `/ready` = 503 | `redis-cli ping`, логи `redis` | проверить Redis, том и свободное место |
| `/metrics` показывает `redis_up 0` | `/ready`, сеть Compose | проверить имя сервиса `redis` и healthcheck |
| Redis не стартует | `INFO persistence`, логи, место на диске | не очищать том; проверить AOF и backup |
| Версия в `/info` неверна | Git ref и `APP_VERSION` | пересобрать `app`, проверить `.env` |

### Prometheus и Grafana

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml ps
Invoke-WebRequest http://localhost:9090/-/ready
Invoke-RestMethod http://localhost:9090/api/v1/targets
Invoke-RestMethod http://localhost:3000/api/health
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml logs --tail 200 prometheus grafana
```

Проверьте, что target `devops-notes-lab` имеет состояние `up`. Ошибка только в
Grafana обычно не влияет на приложение; ошибка target Prometheus требует
проверки `/metrics` и внутренней сети Compose.

## Критерии завершения операции

- контейнеры `app` и `redis` имеют состояние `healthy`;
- `/health` и `/ready` возвращают HTTP 200;
- `/info` показывает ожидаемые `version` и `environment`;
- Redis отвечает `PONG`, а нужные ключи доступны;
- `/metrics` открывается, target Prometheus имеет состояние `up`;
- backup проверен чтением архива, его SHA256 записан, копия вынесена с хоста;
- использованная Git-ревизия и результат операции записаны в журнал работ.

## Справочные материалы

- [Redis persistence и резервное копирование](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
- [Docker volumes: backup и restore](https://docs.docker.com/engine/storage/volumes/)
- [Docker Compose в production](https://docs.docker.com/compose/how-tos/production/)
- [Команда `docker compose up`](https://docs.docker.com/reference/cli/docker/compose/up/)
