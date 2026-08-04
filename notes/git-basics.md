# Git Basics

## Что я делал

Во время изучения Git я:

- создал локальный репозиторий;
- подключил удалённый репозиторий GitHub;
- создавал коммиты и отправлял их на GitHub;
- проверял состояние проекта и историю изменений;
- создавал ветки и переключался между ними;
- объединял изменения через merge;
- обновлял README и заметки из консоли.

## Что я понял

Git хранит историю проекта и позволяет безопасно работать с изменениями. Ветки дают возможность разрабатывать отдельные задачи, не затрагивая стабильную версию проекта.

GitHub хранит удалённую копию репозитория и подходит для портфолио, совместной работы и проверки кода.

## Как проверить, что открыта правильная папка

Перед выполнением команд полезно проверить корень репозитория, текущую ветку и адрес GitHub:

```bash
git rev-parse --show-toplevel
git branch --show-current
git remote -v
git status
```

## Клонирование существующего репозитория

Если репозиторий уже существует на GitHub, нужно использовать `git clone`, а не `git init`:

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
```

## Создание нового репозитория

Команда `git init` нужна только для нового локального проекта, который ещё не является Git-репозиторием:

```bash
git init
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
```

## Ежедневный рабочий процесс

Сначала проверить изменения:

```bash
git status
git diff
```

Затем добавить нужные файлы и создать коммит:

```bash
git add Dockerfile .env.example notes/docker.md notes/git-basics.md
git add -u .env
git commit -m "fix: исправил конфигурацию и заметки"
```

После этого отправить изменения на GitHub:

```bash
git push origin main
```

## Работа с ветками

```bash
git switch -c feature/my-change
git branch
git switch main
git merge feature/my-change
```

## Просмотр истории

```bash
git log --oneline --graph --decorate --all
git show <commit>
```

## Полезные правила

- Всегда проверять папку и ветку перед коммитом.
- Просматривать `git diff` перед `git add`.
- Делать небольшие коммиты с понятными сообщениями.
- Не добавлять в Git пароли, токены и файлы `.env`.
- Перед началом новой работы получать изменения командой `git pull --ff-only`.
