"""Check-in / attendance router."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import CheckIn, Employee, Department, User, SystemSetting
from routers.auth import get_current_user, require_manager_or_above
from schemas import (
    CheckInOut, CheckInStats, CheckinSettingsOut,
    CheckinSettingsUpdate, CheckinStatusUpdate,
)
from utils import get_subtree_dept_ids, get_or_create_settings

router = APIRouter(prefix="/api/checkin", tags=["checkin"])


# ── Helpers ────────────────────────────────────────────

def _is_late(check_in: datetime, db: Session) -> bool:
    """Check if check-in time is late based on current settings."""
    s = get_or_create_settings(db)
    on_time = check_in.replace(
        hour=s.work_start_hour, minute=s.work_start_minute, second=0, microsecond=0,
    )
    return check_in > on_time + timedelta(minutes=s.late_threshold_minutes)


def _checkin_to_out(c: CheckIn) -> CheckInOut:
    return CheckInOut(
        id=c.id, employee_id=c.employee_id,
        employee_name=c.employee.name if c.employee else "",
        employee_no=c.employee.employee_no if c.employee else "",
        department_name=c.employee.department.name if c.employee and c.employee.department else "",
        check_date=c.check_date, check_in_time=c.check_in_time,
        check_out_time=c.check_out_time, status=c.status,
    )


# ── Routes ────────────────────────────────────────────

@router.post("/in")
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工")

    today = date.today()
    now = datetime.utcnow()

    existing = db.query(CheckIn).filter(
        CheckIn.employee_id == current_user.employee_id, CheckIn.check_date == today,
    ).first()

    if existing:
        if existing.check_in_time:
            raise HTTPException(status_code=400, detail="今天已经签到过了")
        existing.check_in_time = now
        existing.status = "late" if _is_late(now, db) else "normal"
        db.commit(); db.refresh(existing)
        record = existing
    else:
        record = CheckIn(
            employee_id=current_user.employee_id, check_date=today,
            check_in_time=now,
            status="late" if _is_late(now, db) else "normal",
        )
        db.add(record); db.commit(); db.refresh(record)

    record = db.query(CheckIn).options(
        joinedload(CheckIn.employee).joinedload(Employee.department)
    ).filter(CheckIn.id == record.id).first()
    return _checkin_to_out(record)


@router.post("/out")
def check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工")

    today = date.today()
    record = db.query(CheckIn).filter(
        CheckIn.employee_id == current_user.employee_id, CheckIn.check_date == today,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="今天还没有签到，请先签到")
    if record.check_out_time:
        raise HTTPException(status_code=400, detail="今天已经签退过了")

    record.check_out_time = datetime.utcnow()
    db.commit(); db.refresh(record)

    record = db.query(CheckIn).options(
        joinedload(CheckIn.employee).joinedload(Employee.department)
    ).filter(CheckIn.id == record.id).first()
    return _checkin_to_out(record)


@router.get("/today", response_model=CheckInOut | None)
def get_today_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.employee_id:
        return None

    today = date.today()
    record = db.query(CheckIn).options(
        joinedload(CheckIn.employee).joinedload(Employee.department)
    ).filter(
        CheckIn.employee_id == current_user.employee_id, CheckIn.check_date == today,
    ).first()
    return _checkin_to_out(record) if record else None


@router.get("/records", response_model=list[CheckInOut])
def get_records(
    check_date: date | None = Query(None),
    department_id: int | None = Query(None),
    employee_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(CheckIn).options(
        joinedload(CheckIn.employee).joinedload(Employee.department)
    )

    if current_user.role == "employee":
        if current_user.employee_id:
            q = q.filter(CheckIn.employee_id == current_user.employee_id)
        else:
            return []
    elif current_user.role == "dept_manager":
        if current_user.department_id:
            dept_ids = get_subtree_dept_ids(current_user.department_id, db)
            q = q.join(CheckIn.employee).filter(Employee.department_id.in_(dept_ids))
        else:
            return []

    if check_date:
        q = q.filter(CheckIn.check_date == check_date)
    if department_id and current_user.role == "super_admin":
        q = q.join(CheckIn.employee).filter(Employee.department_id == department_id)
    if employee_id and current_user.role in ("super_admin", "dept_manager"):
        q = q.filter(CheckIn.employee_id == employee_id)

    total = q.count()
    records = q.order_by(CheckIn.check_date.desc(), CheckIn.check_in_time.desc()) \
              .offset((page - 1) * page_size).limit(page_size).all()
    # Attach total for frontend
    result = [_checkin_to_out(r) for r in records]
    return result


@router.get("/stats", response_model=CheckInStats)
def get_today_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    today = date.today()
    total_q = db.query(Employee)
    if current_user.role == "dept_manager":
        if current_user.department_id:
            dept_ids = get_subtree_dept_ids(current_user.department_id, db)
            total_q = total_q.filter(Employee.department_id.in_(dept_ids))
        else:
            return CheckInStats(total_employees=0, checked_in_today=0,
                                not_checked_in=0, late_count=0, check_in_rate=0.0)

    total = total_q.count()
    if total == 0:
        return CheckInStats(total_employees=0, checked_in_today=0,
                            not_checked_in=0, late_count=0, check_in_rate=0.0)

    checked_q = db.query(CheckIn).filter(CheckIn.check_date == today)
    if current_user.role == "dept_manager" and current_user.department_id:
        dept_ids2 = get_subtree_dept_ids(current_user.department_id, db)
        checked_q = checked_q.join(CheckIn.employee).filter(Employee.department_id.in_(dept_ids2))

    checked_in = checked_q.filter(CheckIn.check_in_time.isnot(None)).count()
    late_count = checked_q.filter(CheckIn.status == "late").count()

    return CheckInStats(
        total_employees=total, checked_in_today=checked_in,
        not_checked_in=total - checked_in,
        late_count=late_count,
        check_in_rate=round(checked_in / total * 100, 1),
    )


# ── Settings (manager+) ───────────────────────────────

@router.get("/settings", response_model=CheckinSettingsOut)
def get_checkin_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    return get_or_create_settings(db)


@router.put("/settings", response_model=CheckinSettingsOut)
def update_checkin_settings(
    body: CheckinSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    from utils import validate_checkin_time
    try:
        validate_checkin_time(body.work_start_hour, body.work_start_minute, body.late_threshold_minutes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    s = get_or_create_settings(db)
    if body.work_start_hour is not None: s.work_start_hour = body.work_start_hour
    if body.work_start_minute is not None: s.work_start_minute = body.work_start_minute
    if body.late_threshold_minutes is not None: s.late_threshold_minutes = body.late_threshold_minutes
    db.commit(); db.refresh(s)
    return s


# ── Status modification ───────────────────────────────

@router.put("/{record_id}/status", response_model=CheckInOut)
def update_checkin_status(
    record_id: int, body: CheckinStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    if body.status not in ("normal", "late", "early", "absent"):
        raise HTTPException(status_code=400, detail="无效的状态值")

    record = db.query(CheckIn).options(
        joinedload(CheckIn.employee).joinedload(Employee.department)
    ).filter(CheckIn.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="签到记录不存在")

    if current_user.role == "dept_manager":
        if current_user.department_id:
            dept_ids = get_subtree_dept_ids(current_user.department_id, db)
            if record.employee.department_id not in dept_ids:
                raise HTTPException(status_code=403, detail="只能修改本部门的签到记录")

    record.status = body.status
    db.commit(); db.refresh(record)
    return _checkin_to_out(record)
