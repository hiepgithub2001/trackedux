"""API router registry — includes all route modules under /api/v1."""

from fastapi import APIRouter

from app.api.attendance import router as attendance_router
from app.api.auth import router as auth_router
from app.api.classes import router as classes_router
from app.api.dashboard import router as dashboard_router
from app.api.lesson_kinds import router as lesson_kinds_router
from app.api.lessons import router as lessons_router
from app.api.schedule import router as schedule_router
from app.api.students import router as students_router
from app.api.system.centers import router as system_router
from app.api.teachers import router as teachers_router
from app.api.tuition import router as tuition_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(classes_router)
api_router.include_router(lessons_router)
api_router.include_router(schedule_router)
api_router.include_router(attendance_router)
api_router.include_router(tuition_router)
api_router.include_router(lesson_kinds_router)
api_router.include_router(dashboard_router)
api_router.include_router(system_router)
