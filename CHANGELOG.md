# История изменений

Все заметные изменения проекта фиксируются в этом файле. Версии следуют формату Semantic Versioning.

## [Unreleased]

## [1.3.0] - 2026-08-18

### Добавлено

- реальное Flask-приложение со счётчиком посещений в Redis;
- endpoints `/health`, `/ready`, `/info` и `/metrics`;
- структурированные JSON-логи и идентификаторы запросов;
- единый JSON-формат ошибок 404 и 500;
- unit- и интеграционные проверки с контролем покрытия;
- GitHub Actions, GitLab CI и Dependabot;
- аудит Python-зависимостей через `pip-audit`;
- локальный стек Prometheus + Grafana с готовым dashboard;
- автоматическое создание GitHub Release после отправки тега `vX.Y.Z`.

### Изменено

- Docker-образы закреплены по версии и SHA256 digest;
- Redis доступен только внутри сети Docker Compose;
- стили вынесены в отдельный файл, из CSP удалён `'unsafe-inline'`.

### Безопасность

- добавлены CSP, `X-Content-Type-Options`, `X-Frame-Options` и `Referrer-Policy`;
- внутренние детали необработанных исключений больше не возвращаются клиенту.

[Unreleased]: https://github.com/keregan/devops-notes-lab/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/keregan/devops-notes-lab/releases/tag/v1.3.0
