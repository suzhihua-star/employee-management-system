"""System settings router — company name, checkin time, etc."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SystemSetting, User
from routers.auth import get_current_user, require_admin
from schemas import SystemSettingsOut, SystemSettingsUpdate
from utils import get_or_create_settings, validate_checkin_time

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsOut)
def get_settings(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_or_create_settings(db)


@router.put("", response_model=SystemSettingsOut)
def update_settings(
    body: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        validate_checkin_time(body.work_start_hour, body.work_start_minute, body.late_threshold_minutes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    s = get_or_create_settings(db)

    if body.company_name is not None:
        if not body.company_name.strip():
            raise HTTPException(status_code=400, detail="企业名称不能为空")
        s.company_name = body.company_name.strip()
    if body.work_start_hour is not None:
        s.work_start_hour = body.work_start_hour
    if body.work_start_minute is not None:
        s.work_start_minute = body.work_start_minute
    if body.late_threshold_minutes is not None:
        s.late_threshold_minutes = body.late_threshold_minutes

    db.commit()
    db.refresh(s)
    return s
