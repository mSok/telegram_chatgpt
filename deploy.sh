#!/bin/bash
set -e

echo "Starting deployment at $(date)"

# Переходим в директорию проекта
cd /root/opt/telegram_chatgpt

# Пуллим последние изменения из мастера
echo "Pulling latest changes from master..."
git pull origin main

# Пересобираем образ
echo "Building Docker image..."
docker-compose build

# Перезапускаем контейнер
echo "Restarting container..."
docker-compose up -d

# Удаляем неиспользуемые образы
echo "Cleaning up unused images..."
docker image prune -f

echo "Deployment completed successfully at $(date)"

# Показываем статус контейнера
echo "Container status:"
docker-compose ps
