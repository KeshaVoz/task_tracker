from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router


app = FastAPI()

app.include_router(auth_router)
app.include_router(tasks_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_pages():
    with open('static/pages/login.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    with open('static/pages/register.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page():
    with open('static/pages/tasks.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())
    

@app.get("/css/{filename:path}")
async def css(filename: str):
    return FileResponse(f'static/css/{filename}')


@app.get("/js/{filename:path}")
async def js(filename: str):
    return FileResponse(f'static/js/{filename}')



