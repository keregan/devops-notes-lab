# Practice Commands

## Git практика

### Инициализация проекта

```bash
git init
git status
```

---

### Добавление файлов

```bash
git add .
```

---

### Commit

```bash
git commit -m "init: create project"
```

---

### Подключение GitHub

```bash
git remote add origin https://github.com/keregan/devops-notes-lab.git
```

---

### Push проекта

```bash
git push -u origin main
```

---

### История commit

```bash
git log
```

---

### Работа с ветками

#### Список веток

```bash
git branch
```

#### Создание ветки

```bash
git checkout -b feature/git-notes-update
```

#### Переключение ветки

```bash
git checkout main
```

#### Push новой ветки

```bash
git push --set-upstream origin feature/git-notes-update
```

#### Merge веток

```bash
git merge feature/git-notes-update
```

---

## Docker практика

### Проверка Docker

```bash
docker ps
docker ps -a
```

---

### Запуск nginx контейнера

```bash
docker run -d -p 8082:80 nginx
```

---

### Остановка контейнера

```bash
docker stop <container>
```

---

### Удаление контейнера

```bash
docker rm <container>
```

---

### Dockerfile

### Сборка image

```bash
docker build -t my-devops-app .
```

---

### Запуск контейнера из image

```bash
docker run -d -p 8083:80 my-devops-app
```

---

## Docker Compose

### Запуск compose

```bash
docker compose up
```

---

### Запуск compose в фоне

```bash
docker compose up -d
```

---

### Пересборка compose

```bash
docker compose up --build
```

---

### Остановка compose

```bash
docker compose down
```

---

## Работа с контейнером

### Подключение внутрь контейнера

```bash
docker exec -it <container> sh
```

---

### Проверка сети контейнера

```bash
ping redis
```

---

## Redis практика

### Подключение к Redis

```bash
redis-cli
```

---

### Добавление данных

```bash
set test hello
```

---

### Получение данных

```bash
get test
```

---

## Environment Variables

### .env файл

```env
APP_PORT=8084
REDIS_PORT=6379
```

---

## Полезные команды

### Просмотр image

```bash
docker images
```

---

### Просмотр логов

```bash
docker logs <container>
```

---

### Удаление image

```bash
docker rmi <image>
```

---

## Что я практиковал

- работа через PowerShell
- работа через Docker Desktop
- работа с ветками Git
- push изменений
- Docker Compose
- Docker networking
- Redis контейнер
- environment variables
- volumes
- исправление ошибок compose и Dockerfile