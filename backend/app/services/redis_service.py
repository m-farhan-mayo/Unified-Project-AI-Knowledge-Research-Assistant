import json
import os

import redis
from dotenv import load_dotenv

load_dotenv()


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)


def set_json(key: str, value):
    return redis_client.set(key, json.dumps(value))


def get_json(key: str):
    try:
        value = redis_client.get(key)

        if value is None:
            return None

        return json.loads(value)

    except redis.exceptions.ConnectionError:
        return None

def save_history(session_id: str, history: list):
    try:
        return set_json(f"chat:{session_id}", history)

    except redis.exceptions.ConnectionError:
        return False


def load_history(session_id: str):
    return get_json(f"chat:{session_id}")