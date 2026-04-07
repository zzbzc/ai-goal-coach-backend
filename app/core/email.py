"""邮件发送服务"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings


def send_verification_email(email: str, code: str) -> bool:
    """发送验证码邮件

    Args:
        email: 收件人邮箱
        code: 验证码（6 位数字）

    Returns:
        bool: 发送成功返回 True
    """
    if not settings.SMTP_HOST or not settings.SMTP_PORT:
        print(f"[模拟邮件] 验证码邮件已发送到：{email}, 验证码：{code}")
        return True

    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = f"🎯 欢迎加入 AI Goal Coach！这是您的验证码"

        # 邮件内容
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50; text-align: center;">🎉 欢迎加入 AI Goal Coach！</h1>

                <p style="font-size: 16px;">你好！👋</p>

                <p>感谢你选择 AI Goal Coach 作为你的目标达成伙伴！</p>
                <p>我们将陪你一起：</p>
                <ul style="color: #555;">
                    <li>✨ 设定清晰可行的目标</li>
                    <li>📊 追踪每日 progress</li>
                    <li>🏆 建立持久的习惯</li>
                    <li>💪 成为更好的自己</li>
                </ul>

                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border-radius: 10px; padding: 30px; margin: 30px 0; text-align: center;">
                    <p style="color: white; margin: 0 0 10px 0;">你的验证码是：</p>
                    <h1 style="color: white; font-size: 42px; letter-spacing: 8px; margin: 20px 0;">
                        {code}
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 0;">10 分钟内有效 ⏰</p>
                </div>

                <p style="color: #666; font-size: 14px;">
                    💡 <strong>小提示：</strong>验证码仅供本人使用，如果不是你本人操作，请忽略此邮件。
                </p>

                <div style="text-align: center; margin-top: 40px; padding-top: 20px;
                            border-top: 1px solid #eee; color: #888; font-size: 14px;">
                    <p>🚀 准备好了吗？让我们一起开启这段成长之旅！</p>
                    <p style="margin-top: 10px;">— AI Goal Coach 团队</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html', 'utf-8'))

        # 发送邮件
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, email, msg.as_string())
        server.quit()

        print(f"[邮件] 验证码邮件已发送到：{email}")
        return True

    except Exception as e:
        print(f"[邮件] 发送失败：{e}")
        return False
