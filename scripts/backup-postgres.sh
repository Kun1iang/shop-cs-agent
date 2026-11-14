#!/usr/bin/env sh
set -eu

backup_dir="${BACKUP_DIR:-backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
database="${POSTGRES_DB:-shop}"
user="${POSTGRES_USER:-shop}"
output="${backup_dir}/shop-${timestamp}.sql"

mkdir -p "$backup_dir"
docker compose exec -T db pg_dump -U "$user" -d "$database" > "$output"

echo "Backup created: $output"

