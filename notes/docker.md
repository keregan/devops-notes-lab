# Docker

## Что я делал

В рамках изучения Docker я:

- установил Docker и проверил его работу через консоль;
- запустил первый контейнер Nginx;
- изучил разницу между образом (image) и контейнером (container);
- научился запускать, останавливать и удалять контейнеры;
- создал собственный `Dockerfile` и собрал образ;
- запустил контейнер из собственного образа;
- создал `docker-compose.yml` для нескольких сервисов;
- подключил переменные окружения из файла `.env`;
- добавил Redis и проверил его через `redis-cli`;
- изучил порты, тома и сохранение данных.

## Что я понял

Docker позволяет запускать приложения в одинаковом изолированном окружении. Образ содержит приложение и его зависимости, а контейнер является запущенным экземпляром образа.

Docker Compose описывает несколько связанных сервисов в одном YAML-файле и позволяет управлять ими одной командой.

## Основные команды

### Контейнеры

```bash
docker ps
docker ps -a
docker stop <container>
docker start <container>
docker rm <container>
docker logs <container>
docker exec -it <container> sh
```

### Образы

```bash
docker images
docker build -t devops-notes-lab .
docker rmi <image>
```

### Запуск приложения

```bash
docker run --name devops-notes-lab -d -p 8084:80 devops-notes-lab
```

После запуска приложение доступно по адресу `http://localhost:8084`.

### Docker Compose

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose down
```

Команда `docker compose config` помогает заранее проверить структуру файла и подстановку переменных окружения.

### Redis

```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli set test "hello"
docker compose exec redis redis-cli get test
```

На команду `ping` исправный Redis отвечает `PONG`.

## Полезные правила

- Не добавлять `.env` с секретами в Git.
- Хранить пример настроек в `.env.example`.
- Перед сборкой проверять изменения командой `git diff`.
- Не удалять тома с данными без необходимости.
