import os
from dotenv import load_dotenv
import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()  # reads .env into environment variables — must run before reading any env var below

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [("Buy milk", False), ("Walk the dog", False), ("Finish assignment", True)]
        )
    conn.commit()
    cursor.close()
    conn.close()

init_db()  # runs once when the app starts


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


@app.exception_handler(RequestValidationError)
def validation_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "Invalid or missing required fields"})


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Task not found"})
    return {"id": row[0], "title": row[1], "done": row[2]}


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required"})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (task.title, False)
    )
    new_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return {"id": new_id, "title": task.title, "done": False}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required"})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (task.title, task.done, task_id)
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail={"error": "Task not found"})

    return {"id": task_id, "title": task.title, "done": task.done}


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail={"error": "Task not found"})
    return
class AuthCredentials(BaseModel):
    email: str
    password: str

@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})

    result = supabase.auth.sign_up({
        "email": credentials.email,
        "password": credentials.password
    })
    return {"user": result.user}

@app.post("/auth/login")
def login(credentials: AuthCredentials):
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})

    try:
        result = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def protected_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "Access token required"})

    token = auth_header.split(" ")[1]
    # Token verification comes in Stage 3 — for now, just confirming one was sent
    return {"message": "Token received (not yet verified)", "token_preview": token[:10] + "..."}