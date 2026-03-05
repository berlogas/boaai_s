#!/bin/bashBACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 Начало резервного копирования..."

mkdir -p $BACKUP_DIR

# 1. Бэкап томов Docker
echo "📦 Бэкап томов..."
docker run --rm \
  -v berezhinskii_backend_data:/data:ro \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/data_$DATE.tar.gz /data

docker run --rm \
  -v berezhinskii_global_index:/data:ro \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/global_index_$DATE.tar.gz /data

# 2. Бэкап конфигурации
echo "📄 Бэкап конфигурации..."
cp .env $BACKUP_DIR/env_$DATE.backup
cp docker-compose.yml $BACKUP_DIR/compose_$DATE.backup

# 3. Очистка старых бэкапов (>30 дней)
echo "🧹 Очистка старых бэкапов..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "✅ Резервное копирование завершено: $BACKUP_DIR"
