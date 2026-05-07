from fastapi import FastAPI

from routers.routers import router

app = FastAPI()


@app.get('/')
async def main_page():
    return {'message': 'Главная страница'}


app.include_router(router)
