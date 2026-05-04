from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.settings import settings

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

fastmail = FastMail(mail_config)


async def send_reset_email(email: str, otp: str) -> None:
    message = MessageSchema(
        subject="SmartTask — Password Reset OTP",
        recipients=[email],
        body=f"""
            <h3>Password Reset</h3>
            <p>Use the OTP below to reset your password.
            It expires in <strong>10 minutes</strong>.</p>
            <h1 style="letter-spacing: 8px;">{otp}</h1>
            <p>If you did not request this, ignore this email.</p>
        """,
        subtype=MessageType.html,
    )

    await fastmail.send_message(message)
