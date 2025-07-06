#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Variables
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "📦 Backing up database..."
docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U postgres dantarowallet > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Pull latest images
echo "🔄 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Deploy with rolling update
echo "🔄 Starting rolling update..."
docker-compose -f $COMPOSE_FILE up -d --no-deps --scale app=2 app
sleep 30
docker-compose -f $COMPOSE_FILE up -d --no-deps app

# Run migrations
echo "🔧 Running migrations..."
docker-compose -f $COMPOSE_FILE exec -T app alembic upgrade head

# Cleanup
echo "🧹 Cleaning up..."
docker system prune -f

# Health check
echo "🏥 Running health check..."
sleep 10
curl -f http://localhost/health || exit 1

echo "✅ Deployment completed successfully!"
