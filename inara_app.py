from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# =====================================================
#  APP INIT
# =====================================================

app = FastAPI(title="INARA Activities API")


# =====================================================
#  TRIANGLE DEMO (OLD EXAMPLE)
# =====================================================

class TriangleInput(BaseModel):
    message: str = "hello world"
    height: int = 4


def build_triangle(message: str, height: int) -> str:
    if not message.strip():
        raise ValueError("message must be non-empty")
    if height < 0:
        raise ValueError("height must be >= 0")
    lines = [message]
    for i in range(height):
        spaces = " " * (height - i - 1)
        lines.append(f"{spaces}/")
    return "\n".join(lines)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triangle")
def triangle(body: TriangleInput):
    try:
        result = build_triangle(body.message, body.height)
        return {"ok": True, "triangle": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/", include_in_schema=False)
def root():
    # Redirect to Swagger UI
    return RedirectResponse(url="/docs")


# =====================================================
#  ACTIVITY MODELS (WITH DEPARTMENT & OFFICE)
# =====================================================

class ActivityBase(BaseModel):
    title: str = Field(..., description="Short name of the activity")
    description: Optional[str] = Field(None, description="Details about the activity")

    # Who is responsible
    assignee_id: int = Field(..., description="Main responsible staff (user ID)")
    support_assignee_id: Optional[int] = Field(
        None, description="Supporting staff member (user ID)"
    )

    # Program / project / donor
    program_id: Optional[int] = Field(None, description="Program ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    main_donor_id: Optional[int] = Field(None, description="Main donor ID")

    # When
    start_datetime: datetime = Field(..., description="Planned start date/time")
    end_datetime: datetime = Field(..., description="Planned end date/time")

    # Priority / status
    priority: str = Field(
        "medium", description="Priority: low, medium, high"
    )
    status: str = Field(
        "planned",
        description="Status: planned, ongoing, completed, cancelled, late",
    )

    # Extra info
    notes: Optional[str] = Field(None, description="Notes or comments")

    # Office & department
    office_id: Optional[int] = Field(
        None, description="Office ID (country office, e.g. 1 = Turkey, 2 = Lebanon)"
    )
    department: Optional[str] = Field(
        None,
        description="Department name, e.g. Program, MEAL, Finance, HR, Operations…",
    )


class ActivityCreate(ActivityBase):
    weekly_plan_id: Optional[int] = Field(
        None, description="ID of the weekly plan this activity belongs to"
    )


class ActivityRead(ActivityBase):
    id: int
    weekly_plan_id: Optional[int]
    is_late: bool
    created_at: datetime
    updated_at: datetime


# =====================================================
#  FAKE IN-MEMORY "DATABASE"
# =====================================================

_fake_activities_db: List[ActivityRead] = []
_activity_id_counter: int = 1


# =====================================================
#  ACTIVITY ENDPOINTS
# =====================================================

@app.post("/activities", response_model=ActivityRead)
def create_activity(body: ActivityCreate):
    """
    Create a new activity (stored in memory for now).
    When you later add a real database, this logic will be replaced.
    """
    global _activity_id_counter

    now = datetime.utcnow()

    # For now, keep late-logic simple: always false.
    is_late = False

    activity = ActivityRead(
        id=_activity_id_counter,
        weekly_plan_id=body.weekly_plan_id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        support_assignee_id=body.support_assignee_id,
        program_id=body.program_id,
        project_id=body.project_id,
        main_donor_id=body.main_donor_id,
        start_datetime=body.start_datetime,
        end_datetime=body.end_datetime,
        priority=body.priority,
        status=body.status,
        notes=body.notes,
        office_id=body.office_id,
        department=body.department,
        is_late=is_late,
        created_at=now,
        updated_at=now,
    )

    _fake_activities_db.append(activity)
    _activity_id_counter += 1
    return activity


@app.get("/activities", response_model=List[ActivityRead])
def list_activities(
    office_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
):
    """
    List activities, with optional filtering by office, assignee, status, and department.
    """
    results = _fake_activities_db

    if office_id is not None:
        results = [a for a in results if a.office_id == office_id]

    if assignee_id is not None:
        results = [a for a in results if a.assignee_id == assignee_id]

    if status is not None:
        results = [a for a in results if a.status == status]

    if department is not None:
        results = [a for a in results if a.department == department]

    return results
