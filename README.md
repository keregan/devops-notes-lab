# DevOps Notes Lab

Мини-проект с Docker-инфраструктурой и базовым CI/CD pipeline.

Проект представляет собой подготовленное DevOps-окружение для запуска контейнеризированных сервисов с использованием Docker Compose, environment variables и Redis.

---

# Возможности проекта

В проекте реализовано:

- запуск сервисов через Docker Compose
- работа с несколькими контейнерами
- подключение Redis
- использование environment variables
- автоматизация запуска сервисов
- базовый CI/CD pipeline
- работа с логами и контейнерами
- управление контейнерами через PowerShell

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
├── .env
└── README.md
