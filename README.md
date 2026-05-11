# DevOps Notes Lab

Проек Devops-notes-lab

---

# Что находится в проекте

В проекте я:
- практикую Git и GitHub
- работаю с Docker контейнерами
- использую docker-compose
- подключаю Redis
- тестирую environment variables
- учусь работать через PowerShell
- собираю заметки и команды
- изучаю основы CI/CD

---

# Структура проекта

- `notes/` — мои заметки по темам
- `practice/` — команды и небольшая практика
- `Dockerfile` — сборка контейнера
- `docker-compose.yml` — запуск сервисов
- `.env` — переменные окружения

---

# Что уже реализовано

## Git

- создание репозитория
- commits
- push в GitHub
- работа с ветками
- merge веток
- работа через feature branch

---

## Docker

- запуск nginx контейнера
- создание Dockerfile
- сборка собственного image
- запуск контейнеров
- работа с портами
- docker-compose
- подключение внутрь контейнера
- просмотр логов

---

## Redis

- запуск Redis контейнера
- проверка подключения
- работа через redis-cli
- тестирование сохранения данных

---

## Environment Variables

- работа с `.env`
- подключение переменных окружения
- использование переменных в docker-compose

---

# Запуск проекта

## Запуск контейнеров

```bash
docker compose up --build
```

---

## Остановка контейнеров

```bash
docker compose down
```

---

# Что я понял во время проекта

Во время работы над проектом я начал лучше понимать:
- как устроены контейнеры
- зачем нужен Docker
- как работает docker-compose
- как DevOps использует автоматизацию
- зачем нужны CI/CD процессы
- как читать ошибки и логи
- как работать через терминал и PowerShell

Также начал привыкать работать с проектом как с чем-то более "живым", а не просто набором команд из курса.

---

# Что хочу добавить дальше

- полноценный CI/CD pipeline
- Jenkins
- Linux practice
- monitoring
- networking basics
- автоматизацию через Python

---

# Быстрые команды

## Git

```bash
git status
git add .
git commit -m "message"
git push
```

---

## Docker

```bash
docker ps
docker build
docker compose up
docker compose down
```

---

# Статус проекта

Проект продолжает постепенно обновляться по мере изучения новых DevOps тем.
