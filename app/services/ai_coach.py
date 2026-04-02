"""AI 教练服务"""
import logging
import json
import re
from typing import Optional, Dict, Any
from openai import OpenAI
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 OpenAI 客户端（兼容多厂商）
client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)


def parse_json_response(content: str) -> Dict[str, Any]:
    """解析 AI 返回的 JSON 响应，处理 Markdown 代码块包裹的情况"""
    # 去除 Markdown 代码块标记
    content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
    content = content.strip()
    return json.loads(content)


async def generate_goal_plan(
    title: str,
    description: Optional[str],
    duration_days: int,
    daily_time_available: str,
    experience_level: str,
) -> Dict[str, Any]:
    """AI 生成目标计划"""
    prompt = f"""
你是一个专业的目标教练。请为用户生成一个可执行的目标计划。

目标信息：
- 标题：{title}
- 描述：{description or '无'}
- 持续时间：{duration_days}天
- 每天可用时间：{daily_time_available}
- 经验水平：{experience_level}

请生成一个 JSON 格式的计划，包含：
1. weekly_plans: 每周计划数组，每周包含 week_number, title, description
2. daily_tasks: 每日任务数组，每天包含 day_number, title, description, estimated_minutes

只需要返回纯 JSON，不要其他内容。
"""

    logger.info("=" * 60)
    logger.info("【AI 生成目标计划】- 输入:")
    logger.info(f"  标题：{title}")
    logger.info(f"  描述：{description or '无'}")
    logger.info(f"  持续时间：{duration_days}天")
    logger.info(f"  每天可用时间：{daily_time_available}")
    logger.info(f"  经验水平：{experience_level}")
    logger.info("-" * 60)
    logger.info("Prompt:")
    logger.info(prompt)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的目标教练，擅长帮助用户制定可执行的计划。请始终返回纯 JSON 格式。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        logger.info("-" * 60)
        logger.info("【AI 生成目标计划】- 输出:")
        logger.info(f"  Model: {settings.OPENAI_MODEL}")
        logger.info(f"  Usage: {response.usage}")
        logger.info("  原始响应:")
        logger.info(content)

        plan = parse_json_response(content)
        logger.info("  解析后的计划:")
        logger.info(json.dumps(plan, indent=2, ensure_ascii=False))
        logger.info("=" * 60)

        return {
            "success": True,
            "plan": plan,
        }
    except Exception as e:
        logger.error("=" * 60)
        logger.error("【AI 生成目标计划】- 错误:")
        logger.error(f"  {str(e)}")
        logger.error("=" * 60)
        return {
            "success": False,
            "error": str(e),
        }


async def generate_checkin_feedback(
    notes: str,
    streak_count: int,
    goal_title: str,
) -> Dict[str, str]:
    """AI 生成打卡点评"""
    prompt = f"""
你是一个鼓励型的 AI 教练。用户刚刚完成了打卡，请给出简短的点评和建议。

目标：{goal_title}
连续打卡：{streak_count}天
用户心得：{notes}

请用 JSON 格式返回：
{{
  "feedback": "鼓励性的点评，1-2 句话",
  "suggestion": "具体的改进建议或提醒，1 句话"
}}

只需要返回纯 JSON，不要其他内容。语气要温暖、鼓励人心。
"""

    logger.info("=" * 60)
    logger.info("【AI 打卡点评】- 输入:")
    logger.info(f"  目标：{goal_title}")
    logger.info(f"  连续打卡：{streak_count}天")
    logger.info(f"  用户心得：{notes}")
    logger.info("-" * 60)
    logger.info("Prompt:")
    logger.info(prompt)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个温暖、鼓励型的 AI 教练。请始终返回纯 JSON 格式。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )

        content = response.choices[0].message.content
        logger.info("-" * 60)
        logger.info("【AI 打卡点评】- 输出:")
        logger.info(f"  Model: {settings.OPENAI_MODEL}")
        logger.info(f"  Usage: {response.usage}")
        logger.info("  原始响应:")
        logger.info(content)

        result = parse_json_response(content)
        logger.info("  解析后的响应:")
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        logger.info("=" * 60)

        return result
    except Exception as e:
        logger.error("=" * 60)
        logger.error("【AI 打卡点评】- 错误:")
        logger.error(f"  {str(e)}")
        logger.error("=" * 60)
        return {
            "feedback": f"太棒了！你已经连续打卡{streak_count}天了，继续保持！",
            "suggestion": "每天进步一点点，积累就是大改变。",
        }


async def adjust_plan(
    current_plan: Dict[str, Any],
    feedback: str,
) -> Dict[str, Any]:
    """AI 调整计划"""
    prompt = f"""
用户希望调整他们的目标计划。

当前计划：{json.dumps(current_plan, ensure_ascii=False)}
用户反馈：{feedback}

请根据用户反馈调整计划，返回更新后的 JSON 格式计划。
只需要返回纯 JSON，不要其他内容。
"""

    logger.info("=" * 60)
    logger.info("【AI 调整计划】- 输入:")
    logger.info(f"  当前计划：{json.dumps(current_plan, ensure_ascii=False)[:200]}...")
    logger.info(f"  用户反馈：{feedback}")
    logger.info("-" * 60)
    logger.info("Prompt:")
    logger.info(prompt)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个灵活的目标教练，擅长根据用户反馈调整计划。请始终返回纯 JSON 格式。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        logger.info("-" * 60)
        logger.info("【AI 调整计划】- 输出:")
        logger.info(f"  Model: {settings.OPENAI_MODEL}")
        logger.info(f"  Usage: {response.usage}")
        logger.info("  原始响应:")
        logger.info(content)

        plan = parse_json_response(content)
        logger.info("  解析后的计划:")
        logger.info(json.dumps(plan, indent=2, ensure_ascii=False))
        logger.info("=" * 60)

        return {
            "success": True,
            "plan": plan,
        }
    except Exception as e:
        logger.error("=" * 60)
        logger.error("【AI 调整计划】- 错误:")
        logger.error(f"  {str(e)}")
        logger.error("=" * 60)
        return {
            "success": False,
            "error": str(e),
        }
