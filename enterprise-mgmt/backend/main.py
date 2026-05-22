"""FastAPI application entry point."""
import sys
from pathlib import Path

# Ensure backend/ is on the Python path so sibling imports work
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import auth, departments, employees, checkin, settings

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="企业管理系统 API",
    description="部门管理 · 人员管理 · 签到系统 · 组织架构",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(checkin.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
