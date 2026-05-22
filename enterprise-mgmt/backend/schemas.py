"""Pydantic schemas for request/response validation."""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    employee_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Department ────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[int] = None
    description: str = ""


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    description: str
    created_at: datetime
    employee_count: int = 0
    children: List["DepartmentOut"] = []

    model_config = {"from_attributes": True}


# ── Employee ──────────────────────────────────────────

class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    employee_no: str = Field(..., min_length=1, max_length=20)
    department_id: int
    position: str = "员工"
    phone: str = ""
    email: str = ""
    hire_date: date = Field(default_factory=date.today)
    # Optional: create a login account for this employee
    username: Optional[str] = None
    password: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    employee_no: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[date] = None
    # Optional: update or create login account
    username: Optional[str] = None
    password: Optional[str] = None


class EmployeeOut(BaseModel):
    id: int
    name: str
    employee_no: str
    department_id: int
    department_name: str = ""
    position: str
    phone: str
    email: str
    hire_date: date
    created_at: datetime
    has_account: bool = False
    username: Optional[str] = None

    model_config = {"from_attributes": True}


# ── CheckIn ───────────────────────────────────────────

class CheckInOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    employee_no: str = ""
    department_name: str = ""
    check_date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: str

    model_config = {"from_attributes": True}


class CheckInStats(BaseModel):
    total_employees: int
    checked_in_today: int
    not_checked_in: int
    late_count: int
    check_in_rate: float


class DashboardStats(BaseModel):
    department_count: int
    employee_count: int
    today_checkin: CheckInStats


# ── CheckIn Settings ─────────────────────────────────

class CheckinSettingsOut(BaseModel):
    work_start_hour: int
    work_start_minute: int
    late_threshold_minutes: int

    model_config = {"from_attributes": True}


class CheckinSettingsUpdate(BaseModel):
    work_start_hour: Optional[int] = None
    work_start_minute: Optional[int] = None
    late_threshold_minutes: Optional[int] = None


class CheckinStatusUpdate(BaseModel):
    status: str  # normal, late, early, absent


# ── System Settings ───────────────────────────────────

class SystemSettingsOut(BaseModel):
    company_name: str
    work_start_hour: int
    work_start_minute: int
    late_threshold_minutes: int

    model_config = {"from_attributes": True}


class SystemSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    work_start_hour: Optional[int] = None
    work_start_minute: Optional[int] = None
    late_threshold_minutes: Optional[int] = None
