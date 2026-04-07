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
    import re

    # 尝试从代码块中提取 JSON
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1)
    else:
        # 如果没有代码块，尝试找最后一个 { 开始的内容
        # 因为 AI 可能先输出思考过程，最后输出 JSON
        brace_start = content.rfind('{')
        if brace_start != -1:
            content = content[brace_start:]

    content = content.strip()

    # 尝试解析 JSON
    try:
        return json.loads(content, strict=False)
    except json.JSONDecodeError as e:
        # 如果解析失败，尝试修复一些常见问题
        # 1. 移除重复的字段（如 "day_number": 21, "day_number": 21,）
        content = re.sub(r'(\s*)"(\w+)":\s*([^,}]+),\s*\1*"\2":\s*\3,', r'\1"\2": \3,', content)

        # 2. 移除行尾多余的逗号
        content = re.sub(r',(\s*})', r'\1', content)

        # 3. 移除行尾多余的逗号（数组）
        content = re.sub(r',(\s*])', r'\1', content)

        return json.loads(content, strict=False)


async def generate_goal_plan(
    title: str,
    description: Optional[str],
    duration_days: int,
    daily_time_available: str,
    experience_level: str,
) -> Dict[str, Any]:
    """AI 生成目标计划 - 使用思考链方式"""
    prompt = f"""
你是一个专业的目标教练。请为用户生成一个**可执行、具体、有质量**的目标计划。

## 目标信息
- 标题：{title}
- 描述：{description or '无'}
- 持续时间：{duration_days}天
- 每天可用时间：{daily_time_available}
- 经验水平：{experience_level}

## 请按照以下步骤思考

### 第 1 步：识别目标类型

首先判断这个目标属于哪种类型：

| 类型 | 特征 | 前置任务策略 |
|------|------|-------------|
| **习惯养成型** | 每天重复相同/相似动作（如早起、冥想、喝水） | 前 1-2 天完成所有环境准备，后面专注练习核心动作 |
| **技能学习型** | 学习新知识/技能（如编程、外语、乐器） | 前置准备环境/工具，然后按难度递进安排学习内容 |
| **项目完成型** | 有明确产出物（如写一本书、做一个 APP） | 前置拆解任务，然后按模块/里程碑推进 |
| **健康运动型** | 健身、跑步、瑜伽等 | 前置学习动作要领/安全事项，然后强度递进 |

### 第 2 步：分析用户和目标

用 1-2 句话回答：
- 这个目标的核心难点是什么？（用户最可能卡在哪里）
- 用户最可能在第几天放弃？为什么？
- 前 3 天必须建立什么"最小可行习惯"？（简单到不可能失败的行动）

### 第 3 步：设计周节奏

用表格或简短描述说明：
- 每周的主题是什么？
- 哪几天应该轻松，哪几天应该挑战？

**重要原则**：
- 环境准备类任务（买装备、布置场地、安装工具）应该**集中在前 1-2 天完成**，不要分散
- 真正需要分散的是**难度递进的练习**，而不是准备工作
- 第 1 周应该以"建立信心"为主，任务要简单到不可能失败

### 第 4 步：生成每日任务

为每一天生成具体任务，每条任务必须包含：
- **动作**：用户具体要做什么（动词开头）
- **对象**：对什么做（具体的工具/材料/内容）
- **完成标准**：做到什么程度算完成（可衡量）

❌ 禁止生成："早睡"、"早起"、"了解 XX"、"学习 XX"、"继续努力"
✅ 应该生成："晚上 9:30 把手机放到卧室外充电"、"写下 3 个今天学到的观点"

**前置任务检查**：
- 如果这是习惯养成型目标，环境准备是否在 1-2 天内完成？
- 如果这是技能学习型目标，是否先易后难循序渐进？
- 有没有为了"分散"而把本可一天完成的事拆成多天？

### 第 5 步：自我检查

检查你生成的任务：
- 用户看完知道具体要做什么吗？
- 用户能判断自己"做完了"还是"没做完"吗？
- 如果用户说"这个太难了"，你有更简单的替代方案吗？

## 输出格式

请先输出你的思考过程（第 1-5 步），然后在最后输出纯 JSON 格式的计划：

```json
{{
  "weekly_plans": [
    {{"week_number": 1, "title": "...", "description": "..."}}
  ],
  "daily_tasks": [
    {{"day_number": 1, "title": "...", "description": "...", "estimated_minutes": 30}}
  ]
}}
```

注意：思考过程要用自然语言，像真人教练一样讲解。JSON 放在最后。
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
                {"role": "system", "content": "你是一个专业的目标教练，擅长帮助用户制定可执行的计划。你需要先输出思考过程，最后输出 JSON 格式的计划。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=8000,  # 增加 token 以容纳思考过程和完整的 30 天计划
        )

        content = response.choices[0].message.content
        logger.info("-" * 60)
        logger.info("【AI 生成目标计划】- 输出:")
        logger.info(f"  Model: {settings.OPENAI_MODEL}")
        logger.info(f"  Usage: {response.usage}")
        logger.info("  原始响应:")
        logger.info(content)

        # 保存原始响应到文件以便调试
        with open("/tmp/ai-last-response.txt", "w") as f:
            f.write(content)

        # 提取 JSON 部分
        try:
            plan = parse_json_response(content)
        except Exception as parse_err:
            logger.error(f"JSON 解析失败：{parse_err}")
            logger.error(f"原始内容前 500 字符：{content[:500]}")
            logger.error(f"原始内容后 500 字符：{content[-500:]}")
            raise

        # 提取思考过程（JSON 之前的内容）
        reasoning = None
        json_match = re.search(r'```json\s*', content, re.DOTALL)
        if json_match:
            reasoning = content[:json_match.start()].strip()
        else:
            # 尝试找最后一个 { 之前的内容
            brace_start = content.rfind('{')
            if brace_start != -1:
                reasoning = content[:brace_start].strip()

        logger.info("  解析后的计划:")
        logger.info(json.dumps(plan, indent=2, ensure_ascii=False))
        logger.info("=" * 60)

        return {
            "success": True,
            "plan": plan,
            "reasoning": reasoning,
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
