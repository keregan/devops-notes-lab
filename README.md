# DevOps Notes Lab

Мини-проект с Docker-инфраструктурой и базовым CI/CD pipeline.

Проект представляет собой локальное DevOps-окружение для запуска и управления контейнеризированными сервисами с использованием Docker Compose, Redis и environment variables.

Текущая версия проекта завершила основную стадию разработки и используется как персональная среда для дальнейшего тестирования DevOps-инструментов, контейнеризации и CI/CD практик.

---

# Возможности проекта

В проекте реализовано:

- запуск сервисов через Docker Compose
- работа с несколькими контейнерами
- подключение Redis
- использование environment variables
- базовая Docker-инфраструктура
- автоматизация запуска сервисов
- базовый CI/CD pipeline
- работа с логами и контейнерами
- управление контейнерами через PowerShell
- работа с Docker networking
- подключение volumes для хранения данных

---

# Используемые технологии

- Docker
- Docker Compose
- Redis
- Git
- GitHub
- GitLab CI/CD
- PowerShell
- Nginx

---

# Структура проекта

```text
devops-notes-lab/
│
├── notes/
├── practice/
├── Dockerfile
├── docker-compose.yml
├── .gitlab-ci.yml
├── .gitignore
├── .env
└── README.md
```

---

# Реализованный функционал

## Docker Infrastructure

В проекте реализована базовая Docker-инфраструктура:

- сборка собственного Docker image
- запуск контейнеров
- управление контейнерами
- работа с портами
- подключение внутрь контейнеров
- просмотр Docker логов
- работа с Docker Compose
- запуск multi-container окружения

---

## Redis Integration

Реализовано подключение Redis:

- запуск Redis контейнера
- тестирование подключения
- взаимодействие через redis-cli
- проверка хранения данных
- работа с volumes

---

## Environment Configuration

В проекте используется `.env` конфигурация:

- хранение environment variables
- настройка портов
- конфигурация сервисов
- разделение конфигурации и инфраструктуры

---

## CI/CD

В проект добавлен базовый GitLab CI/CD pipeline.

Pipeline:
- запускается автоматически
- выполняет build stage
- проверяет Docker окружение
- подготавливает основу для дальнейшей автоматизации deployment процессов

---

# Запуск проекта

## Сборка и запуск контейнеров

```bash
docker compose up --build
```

---

## Запуск в фоновом режиме

```bash
docker compose up -d
```

---

## Остановка сервисов

```bash
docker compose down
```

---

# Полезные команды

## Docker

### Просмотр контейнеров

```bash
docker ps
docker ps -a
```

---

### Просмотр логов

```bash
docker logs <container>
```

---

### Подключение внутрь контейнера

```bash
docker exec -it <container> sh
```

---

### Сборка image

```bash
docker build -t my-devops-app .
```

---

## Git

### Проверка статуса

```bash
git status
```

---

### Commit изменений

```bash
git add .
git commit -m "message"
```

---

### Push изменений

```bash
git push
```

---

### Работа с ветками

```bash
git branch
git checkout
git merge
```

---

# Статус проекта

Текущая версия проекта завершила основную стадию разработки.

Проект используется как локальное DevOps-окружение для:
- тестирования Docker инфраструктуры
- практики CI/CD
- изучения контейнеризации
- дальнейшего расширения DevOps tooling
