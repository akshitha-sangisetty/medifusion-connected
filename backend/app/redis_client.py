import os
import redis

# Get host and port from environment if available, else use defaults
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # "redis" = docker-compose service name
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0
)
