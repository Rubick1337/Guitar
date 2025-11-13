from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.dependencies import init_database
from server.routes import auth, chats

app = FastAPI(title="GuitarPro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_database()


app.include_router(auth.router)
app.include_router(chats.router)


__all__ = ["app"]
