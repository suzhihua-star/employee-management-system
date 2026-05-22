"""SQLAlchemy ORM models."""
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(
        SAEnum("super_admin", "dept_manager", "employee", name="user_role"),
        nullable=False,
        default="employee",
    )
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
    department = relationship("Department", back_populates="managers", foreign_keys=[department_id])


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    description = Column(String(255), nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Self-referential relationship for tree structure
    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent", cascade="all, delete-orphan")

    # Employees in this department
    employees = relationship("Employee", back_populates="department")

    # Managers (users with dept_manager role assigned to this department)
    managers = relationship(
        "User",
        back_populates="department",
        foreign_keys="User.department_id",
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    employee_no = Column(String(20), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position = Column(String(50), nullable=False, default="员工")
    phone = Column(String(20), nullable=True, default="")
    email = Column(String(100), nullable=True, default="")
    hire_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False)
    checkins = relationship("CheckIn", back_populates="employee", cascade="all, delete-orphan")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    check_date = Column(Date, nullable=False, default=date.today, index=True)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(
        SAEnum("normal", "late", "early", "absent", name="checkin_status"),
        nullable=False,
        default="normal",
    )

    # Relationship
    employee = relationship("Employee", back_populates="checkins")


class SystemSetting(Base):
    """Key-value store for system-wide settings (singleton pattern)."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    # Company info
    company_name = Column(String(100), nullable=False, default="企业管理系统")
    # Check-in time config
    work_start_hour = Column(Integer, nullable=False, default=9)
    work_start_minute = Column(Integer, nullable=False, default=0)
    late_threshold_minutes = Column(Integer, nullable=False, default=30)
