from fastapi import FastAPI, Request, HTTPException, status
from starlette.responses import HTMLResponse
from tortoise.contrib.fastapi import register_tortoise
from models import *
from tortoise import models

# Authentication
from authentication import *
from fastapi.security import (OAuth2PasswordBearer, OAuth2PasswordRequestForm)

# signals
from tortoise.signals import  post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

# self packages
from emails import *

# response classes
from fastapi.responses import HTMLResponse

# templates
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
app = FastAPI()


# process signals here

@post_save(User)
async def create_business(
        sender: "Type[User]",
        instance: User,
        created: bool,
        using_db: "Optional[BaseDBAsyncClient]",
        update_fields: List[str]) -> None:
    if created:
        business_obj = await Business.create(
            business_name=instance.username, owner=instance)
        await business_pydantic.from_tortoise_orm(business_obj)
        # send email functionality
        await send_email([instance.email], instance)

@app.get('/verification',  response_class=HTMLResponse)
# make sure to import request from fastapi and HTMLResponse
async def email_verification(request: Request, token: str):
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html",
                                {"request": request, "username": user.username}
                        )
    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post('/registration')
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info['password'] = get_password_hash(user_info['password'])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)

    return {"status": "ok",
            "data":
                f"Hello {new_user.username} thanks for choosing our services. Please check your email inbox and click on the link to confirm your registration."}
@app.get("/")
def index():
    return {"Message": "Hello World"}

register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# authorization configs
oath2_scheme = OAuth2PasswordBearer(tokenUrl = 'token')
# password helper functions
@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {'access_token' : token, 'token_type' : 'bearer'}

async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials['SECRET'], algorithms = ['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await user

@app.post('/user/me')
async def user_login(user: user_pydantic = Depends(get_current_user)):

    business = await Business.get(owner = user)
    logo = business.logo
    logo = "localhost:8000/static/images/"+logo

    return {"status" : "ok",
            "data" :
                {
                    "username" : user.username,
                    "email" : user.email,
                    "verified" : user.is_verified,
                    "join_date" : user.join_date.strftime("%b %d %Y"),
                    "logo" : logo
                }
            }