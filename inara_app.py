from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="Hello FastAPI App")

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
    return RedirectResponse(url="/docs")
# =======================
#  ACTIVITY MODELS
# =======================

class ActivityBase(BaseModel):
    title: str = Field(..., description="Short name of the activity")
    description: Optional[str] = Field(None, description="Details about the activity")
    assignee_id: int = Field(..., description="Main responsible staff (user ID)")
    support_assignee_id: Optional[int] = Field(
        None, description="Supporting staff member (user ID)"
    )
    program_id: Optional[int] = Field(None, description="Program ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    main_donor_id: Optional[int] = Field(None, description="Main donor ID")
    start_datetime: datetime = Field(..., description="Planned start date/time")
    end_datetime: datetime = Field(..., description="Planned end date/time")
    priority: str = Field(
        "medium", description="Priority: low, medium, high"
    )
    status: str = Field(
        "planned", description="Status: planned, ongoing, completed, cancelled, late"
    )
    notes: Optional[str] = Field(None, description="Notes or comments")
    office_id: Optional[int] = Field(None, description="Office ID")


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


# Fake in-memory "database"
_fake_activities_db: List[ActivityRead] = []
_activity_id_counter: int = 1

# =======================
#  ACTIVITY ENDPOINTS
# =======================

@app.post("/activities", response_model=ActivityRead)
def create_activity(body: ActivityCreate):
    """
    Create a new activity.
    For now this stores it in memory only (will reset if server restarts).
    Later we will connect this to a real database.
    """
    global _activity_id_counter

    now = datetime.utcnow()
    is_late = body.end_datetime < now if body.status != "completed" else False

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
):
    """
    List activities, with optional filtering by office, assignee, and status.
    """
    results = _fake_activities_db

    if office_id is not None:
        results = [a for a in results if a.office_id == office_id]

    if assignee_id is not None:
        results = [a for a in results if a.assignee_id == assignee_id]

    if status is not None:
        results = [a for a in results if a.status == status]

    return results

