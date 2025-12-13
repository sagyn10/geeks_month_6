from main.redis import redis_client


def confirmation_key(user_id: int) -> str:
    return f"confirmation_code:user:{user_id}"


def set_confirmation_code(user_id: int, code: str, ttl: int = 300) -> None:
    """Store confirmation code in Redis with TTL (seconds)."""
    key = confirmation_key(user_id)
    # set with expiration
    redis_client.set(key, code, ex=ttl)


def get_confirmation_code(user_id: int):
    """Return confirmation code from Redis without deleting it."""
    key = confirmation_key(user_id)
    return redis_client.get(key)


def pop_confirmation_code(user_id: int):
    """Atomically get and delete confirmation code from Redis.

    Returns the code (str) or None if not present.
    """
    key = confirmation_key(user_id)
    # Use GETDEL if available (Redis >=6.2). Fallback to GET + DEL.
    try:
        # redis-py exposes getdel if redis-server supports it
        code = redis_client.execute_command('GETDEL', key)
        return code
    except Exception:
        # Fallback
        code = redis_client.get(key)
        if code is not None:
            redis_client.delete(key)
        return code
