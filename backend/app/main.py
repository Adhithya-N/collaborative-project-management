"""Entry point for the FastAPI backend application."""

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.activity.router import router as activity_router
from app.modules.auth.router import router as auth_router
from app.modules.comments.router import comments_router, task_comments_router
from app.modules.organizations.router import router as organizations_router
from app.modules.projects.router import org_projects_router, projects_router
from app.modules.tasks.router import project_tasks_router, tasks_router
from app.modules.users.router import router as users_router

# The FastAPI() instance is the core of the app - every route is registered on it.
app = FastAPI(title="Collaborative System API")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(organizations_router)
app.include_router(org_projects_router)
app.include_router(projects_router)
app.include_router(project_tasks_router)
app.include_router(tasks_router)
app.include_router(task_comments_router)
app.include_router(comments_router)
app.include_router(activity_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple endpoint to confirm the server is running (used for monitoring later)."""
    return {"status": "ok"}


@app.get("/health/db")
def health_check_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Confirms the backend can actually reach and query Postgres."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
