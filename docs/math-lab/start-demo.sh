#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/../.." && pwd)
compose_file="$script_dir/docker-compose.demo.yml"
env_file="$repo_root/data_storage/.env"
volumes=(
  eduvision-mathlab-nats-data
  eduvision-mathlab-postgres-data
  eduvision-mathlab-redis-data
  eduvision-mathlab-minio-data
  eduvision-mathlab-qdrant-data
)

if [[ "${1:-}" == "--bootstrap" ]]; then
  for volume in "${volumes[@]}"; do
    docker volume inspect "$volume" >/dev/null 2>&1 || docker volume create "$volume" >/dev/null
  done
else
  for volume in "${volumes[@]}"; do
    if ! docker volume inspect "$volume" >/dev/null 2>&1; then
      echo "Missing protected volume: $volume" >&2
      echo "For a genuinely new installation, run $0 --bootstrap once." >&2
      exit 1
    fi
  done
fi

exec docker compose \
  --env-file "$env_file" \
  -f "$compose_file" \
  up -d --build
