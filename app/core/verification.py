"""验证码存储和管理"""
import redis
import random
from typing import Optional
from datetime import timedelta
from app.config import settings
from app.core.email import send_verification_email

# Redis 连接
redis_client = redis.Redis(
    host=settings.REDIS_HOST or "localhost",
    port=settings.REDIS_PORT or 6379,
    db=settings.REDIS_DB or 0,
    decode_responses=True
)


def generate_code(length: int = 6) -> str:
    """生成随机验证码"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def send_verification_code(email: str) -> str:
    """生成并发送验证码

    Args:
        email: 用户邮箱

    Returns:
        str: 生成的验证码
    """
    code = generate_code()

    # 存储验证码到 Redis
    store_verification_code(email, code)

    # 发送邮件
    send_verification_email(email, code)

    return code


def store_verification_code(email: str, code: str, expire_minutes: int = 10) -> bool:
    """存储验证码到 Redis

    Args:
        email: 用户邮箱
        code: 验证码
        expire_minutes: 过期时间（分钟）

    Returns:
        bool: 存储成功返回 True
    """
    try:
        key = f"verification_code:{email}"
        redis_client.setex(key, timedelta(minutes=expire_minutes), code)
        return True
    except Exception as e:
        print(f"[Redis] 存储验证码失败：{e}")
        return False


def get_verification_code(email: str) -> Optional[str]:
    """从 Redis 获取验证码

    Args:
        email: 用户邮箱

    Returns:
        Optional[str]: 验证码，不存在返回 None
    """
    try:
        key = f"verification_code:{email}"
        return redis_client.get(key)
    except Exception as e:
        print(f"[Redis] 获取验证码失败：{e}")
        return None


def delete_verification_code(email: str) -> bool:
    """删除验证码

    Args:
        email: 用户邮箱

    Returns:
        bool: 删除成功返回 True
    """
    try:
        key = f"verification_code:{email}"
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"[Redis] 删除验证码失败：{e}")
        return False


def verify_code(email: str, code: str) -> bool:
    """验证验证码

    Args:
        email: 用户邮箱
        code: 验证码

    Returns:
        bool: 验证成功返回 True
    """
    stored_code = get_verification_code(email)
    if stored_code and stored_code == code:
        # 验证成功后删除验证码，防止重复使用
        delete_verification_code(email)
        return True
    return False
