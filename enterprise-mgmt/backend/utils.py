"""Shared utility functions used across routers."""
from sqlalchemy.orm import Session

from database import get_db
from models import Department, SystemSetting


def get_subtree_dept_ids(root_id: int, db: Session) -> list[int]:
    """Return root department id and all descendant department ids recursively."""
    ids = [root_id]
    children = db.query(Department).filter(Department.parent_id == root_id).all()
    for child in children:
        ids.extend(get_subtree_dept_ids(child.id, db))
    return ids


def get_or_create_settings(db: Session) -> SystemSetting:
    """Get the singleton system settings row, creating it with defaults if needed."""
    s = db.query(SystemSetting).first()
    if not s:
        s = SystemSetting(
            company_name="企业管理系统",
            work_start_hour=9,
            work_start_minute=0,
            late_threshold_minutes=30,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def validate_checkin_time(hour: int | None, minute: int | None, threshold: int | None) -> None:
    """Validate check-in time parameters. Raises ValueError with Chinese message."""
    if hour is not None and not (0 <= hour <= 23):
        raise ValueError("小时必须在 0-23 之间")
    if minute is not None and not (0 <= minute <= 59):
        raise ValueError("分钟必须在 0-59 之间")
    if threshold is not None and threshold < 0:
        raise ValueError("迟到阈值不能为负数")
