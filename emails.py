from fastapi import(BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status)
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import dotenv_values
from typing import List
from models import User
import jwt

config_credentials = dotenv_values(".env")

conf = ConnectionConfig(
    MAIL_USERNAME=config_credentials["EMAIL"],
    MAIL_PASSWORD=config_credentials["PASS"],
    MAIL_FROM=config_credentials["EMAIL"],
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)




async def send_email(email: List, instance: User):
    token_data = {
        "id": instance.id,
        "username": instance.username,
    }
    # 安全的令牌，可以携带用户信息，确保验证链接的唯一性和安全性。
    # 令牌会附在验证链接中，后续用户点击链接时，服务器可以解码并验证其合法性。
    token = jwt.encode(token_data, config_credentials["SECRET"], algorithm="HS256")
    template = f"""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <div style=" display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <h3> Account Verification </h3>
                <br>
                <p>Thanks for choosing Jiafei's Shops, please 
                click on the link below to verify your account</p> 

                <a style="margin-top:1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
                 href="http://localhost:8000/verification/?token={token}">
                    Verify your email
                <a>

                <p style="margin-top:1rem;">If you did not register for EasyShopas, 
                please kindly ignore this email and nothing will happen. Thanks<p>
            </div>
        </body>
        </html>
    """

    message = MessageSchema(
        subject="EasyShopas Account Verification Mail",
        recipients=email,  # List of recipients, as many as you can pass
        body=template,
        subtype="html"
        )

    fm = FastMail(conf)
    await fm.send_message(message)