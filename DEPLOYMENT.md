# Настройка CI/CD Pipeline для автоматического деплоя

## Обзор

Настроен автоматический pipeline для развертывания Telegram GPT бота при пуше в ветку `main`.

## Как работает pipeline

1. **При пуше в ветку `main`** автоматически запускается GitHub Actions
2. **Запускаются тесты** - проверка качества кода
3. **Собирается Docker образ** и публикуется в Docker Hub с тегом `latest`
4. **Происходит деплой на сервер** через SSH:
   - Пуллятся последние изменения из репозитория
   - Пересобирается Docker образ
   - Перезапускается контейнер
   - Очищаются неиспользуемые образы

## Настройка GitHub Secrets

Для работы pipeline нужно добавить следующие секреты в репозитории GitHub:

1. Перейдите в ваш репозиторий → Settings → Secrets and variables → Actions
2. Нажмите "New repository secret" и добавьте:

### Обязательные секреты:

- `DOCKERHUB_USERNAME` - ваш логин в Docker Hub (уже должен быть)
- `DOCKERHUB_TOKEN` - токен для доступа к Docker Hub (уже должен быть)
- `SSH_HOST` - IP адрес вашего сервера
- `SSH_PRIVATE_KEY` - содержимое приватного SSH ключа `~/.ssh/id_github`
- `SSH_PORT` - порт SSH (по умолчанию `22`)

### Как добавить SSH_PRIVATE_KEY:

1. На локальной машине выполните:
   ```bash
   cat ~/.ssh/id_github
   ```

2. Скопируйте весь вывод (включая `-----BEGIN OPENSSH PRIVATE KEY-----` и `-----END OPENSSH PRIVATE KEY-----`)

3. Вставьте в поле значения секрета `SSH_PRIVATE_KEY`

## Структура файлов

### GitHub Actions Workflow
- Файл: [`.github/workflows/push_docker_image.yml`](.github/workflows/push_docker_image.yml)
- Триггеры: пуш в `main`, PR в `main`, пуш тегов
- Содержит этапы тестирования, сборки и деплоя

### Скрипт деплоя на сервере
- Расположение: `/root/opt/telegram_chatgpt/deploy.sh`
- Выполняет:
  - `git pull origin main`
  - `docker-compose build`
  - `docker-compose up -d`
  - `docker image prune -f`

## Проверка работы

1. Сделайте любые изменения в коде
2. Запушьте их в ветку `main`:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```

3. Перейдите в раздел Actions вашего репозитория GitHub и наблюдайте за выполнением pipeline

## Решение проблем

### Если тесты не проходят
- Проверьте вывод в GitHub Actions
- Убедитесь, что все зависимости корректно установлены

### Если сборка Docker образа не удается
- Проверьте [`Dockerfile`](Dockerfile) на наличие ошибок
- Убедитесь, что все зависимости указаны правильно

### Если деплой не работает
- Проверьте правильность SSH ключей и секретов
- Убедитесь, что сервер доступен по SSH
- Проверьте логи выполнения скрипта деплоя

### Если не хватает места на сервере
- Выполните очистку Docker:
  ```bash
  ssh root@YOUR_SERVER_IP "docker system prune -a --volumes -f"
  ```

## Ручной деплой

Если нужно выполнить деплой вручную:

```bash
ssh -i ~/.ssh/id_github root@YOUR_SERVER_IP "cd /root/opt/telegram_chatgpt && ./deploy.sh"
```

## Мониторинг

Для мониторинга работы бота можно проверить статус контейнера:

```bash
ssh -i ~/.ssh/id_github root@YOUR_SERVER_IP "cd /root/opt/telegram_chatgpt && docker-compose ps"
```

И посмотреть логи:

```bash
ssh -i ~/.ssh/id_github root@YOUR_SERVER_IP "cd /root/opt/telegram_chatgpt && docker-compose logs -f"