uv run celery -A core.celery_setup worker -E --loglevel=info --hostname=worker.basic --concurrency=3
