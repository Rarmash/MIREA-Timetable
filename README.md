# MIREA-Timetable

Webhook навыка Яндекс Алисы для расписания РТУ МИРЭА.

## Запуск через Docker

Production Compose использует готовые Docker-образы из GitHub Container Registry. Сборка выполняется автоматически GitHub Actions при push в `master`.
Навык обращается к API внутри Docker по адресу `http://schedule-api:8000`.

```bash
docker compose pull
docker compose up -d
```

Webhook будет доступен на `http://localhost:8080/post`. Для Яндекс Диалогов нужен публичный HTTPS-адрес, например через reverse proxy.

PostgreSQL запускается автоматически и хранит выбранную группу пользователя в volume `postgres_data`.

## Подключение нового API локально

Для локальной сборки из исходников:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Навык доступен на `http://localhost:8080/post`, новый API — на `http://localhost:8001`.

На VPS production-запуск не требует Docker build:

```bash
docker compose pull
docker compose up -d
```

Если GHCR-пакеты приватные, перед этим выполните `docker login ghcr.io` с GitHub Personal Access Token с правом `read:packages`.

Для проверки webhook можно отправить тестовый запрос:

```bash
curl -X POST http://localhost:8080/post \
  -H 'Content-Type: application/json' \
  -d '{"version":"1.0","request":{"type":"SimpleUtterance","command":"ЭПМО-01-26"},"session":{"user":{"user_id":"test-user"},"application":{"application_id":"test-app"}}}'
```
