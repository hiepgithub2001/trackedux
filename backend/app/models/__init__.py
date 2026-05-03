"""All model imports for Alembic auto-detection."""

from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.center import Center  # noqa: F401
from app.models.class_ import Class  # noqa: F401
from app.models.class_enrollment import ClassEnrollment  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.lesson_kind import LessonKind  # noqa: F401
from app.models.lesson_occurrence import LessonOccurrence  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.student_status_history import StudentStatusHistory  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.teacher_availability import TeacherAvailability  # noqa: F401
from app.models.tuition_ledger_entry import TuitionLedgerEntry  # noqa: F401
from app.models.tuition_payment import TuitionPayment  # noqa: F401
from app.models.user import User  # noqa: F401
