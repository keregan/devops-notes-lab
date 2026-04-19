# Practice Commands

## День 1
```bash
git init
git add .
git commit -m "init: create devops notes lab structure"
git status
git log

## Git практика

### Инициализация
git init

### Коммит
git add .
git commit -m "init: create project"

### Подключение remote
git remote add origin https://github.com/keregan/devops-notes-lab.git

### Отправка
git push -u origin main

## Docker практика

### Запуск контейнера
docker run -d -p 8082:80 nginx

### Сборка образа
docker build -t my-devops-app .

### Запуск контейнера из образа
docker run -d -p 8083:80 my-devops-app

### Docker Compose
docker compose up -d --build
docker compose down