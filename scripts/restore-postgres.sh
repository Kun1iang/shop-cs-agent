#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/shop-YYYYMMDDTHHMMSSZ.sql" >&2
  exit 1
fi

backup_file="$1"
database="${POSTGRES_DB:-shop}"
user="${POSTGRES_USER:-shop}"

if [ ! -f "$backup_file" ]; then
  echo "Backup file not found: $backup_file" >&2
  exit 1
fi

printf "Restore %s into database %s? This modifies data. Type YES: " \
  "$backup_file" "$database"
read -r confirmation
if [ "$confirmation" != "YES" ]; then
  echo "Restore cancelled."
  exit 1
fi

docker compose exec -T db psql -U "$user" -d "$database" < "$backup_file"
echo "Restore completed: $backup_file"

