"""Employee CRUD router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Employee, Department, User
from routers.auth import get_current_user, require_manager_or_above, require_admin, hash_password
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeOut
from utils import get_subtree_dept_ids

router = APIRouter(prefix="/api/employees", tags=["employees"])


def _employee_to_out(emp: Employee) -> EmployeeOut:
    user = emp.user if hasattr(emp, 'user') and emp.user else None
    return EmployeeOut(
        id=emp.id,
        name=emp.name,
        employee_no=emp.employee_no,
        department_id=emp.department_id,
        department_name=emp.department.name if emp.department else "",
        position=emp.position,
        phone=emp.phone or "",
        email=emp.email or "",
        hire_date=emp.hire_date,
        created_at=emp.created_at,
        has_account=user is not None,
        username=user.username if user else None,
    )


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    department_id: int | None = Query(None, description="Filter by department"),
    keyword: str = Query("", description="Search name or employee_no"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List employees. Managers see only their department; admins see all."""
    q = db.query(Employee).options(joinedload(Employee.department))

    # Role-based filtering
    if current_user.role == "dept_manager":
        if current_user.department_id:
            dept_ids = get_subtree_dept_ids(current_user.department_id, db)
            q = q.filter(Employee.department_id.in_(dept_ids))
        else:
            return []
    elif current_user.role == "employee":
        # Regular employees can only see themselves
        if current_user.employee_id:
            q = q.filter(Employee.id == current_user.employee_id)
        else:
            return []

    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (Employee.name.ilike(like)) | (Employee.employee_no.ilike(like))
        )

    total = q.count()
    employees = q.order_by(Employee.id).offset((page - 1) * page_size).limit(page_size).all()
    return [_employee_to_out(e) for e in employees]


@router.get("/{emp_id}", response_model=EmployeeOut)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")

    # Permission check
    if current_user.role == "employee" and current_user.employee_id != emp_id:
        raise HTTPException(status_code=403, detail="只能查看自己的信息")
    if current_user.role == "dept_manager" and emp.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="只能查看本部门员工")

    return _employee_to_out(emp)


@router.post("", response_model=EmployeeOut)
def create_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    """Create an employee. Managers can only add to their own department."""
    # Managers restricted to their department
    if current_user.role == "dept_manager":
        if body.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="只能在本部门添加员工")

    # Check department exists
    dept = db.query(Department).filter(Department.id == body.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="部门不存在")

    # Check employee_no uniqueness
    existing = db.query(Employee).filter(Employee.employee_no == body.employee_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="工号已存在")

    emp = Employee(
        name=body.name,
        employee_no=body.employee_no,
        department_id=body.department_id,
        position=body.position,
        phone=body.phone,
        email=body.email,
        hire_date=body.hire_date,
    )
    db.add(emp)
    db.flush()

    # Create user account if username and password provided
    if body.username and body.password:
        existing_user = db.query(User).filter(User.username == body.username).first()
        if existing_user:
            db.rollback()
            raise HTTPException(status_code=400, detail="用户名已存在")
        user = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role="employee",
            employee_id=emp.id,
            department_id=None,
        )
        db.add(user)

    db.commit()
    db.refresh(emp)

    # Reload with department
    emp = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == emp.id).first()
    return _employee_to_out(emp)


@router.put("/{emp_id}", response_model=EmployeeOut)
def update_employee(
    emp_id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    emp = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")

    # Managers can only update their own department's employees
    if current_user.role == "dept_manager" and emp.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="只能修改本部门员工")

    if body.name is not None:
        emp.name = body.name
    if body.employee_no is not None:
        existing = db.query(Employee).filter(
            Employee.employee_no == body.employee_no, Employee.id != emp_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="工号已存在")
        emp.employee_no = body.employee_no
    if body.department_id is not None:
        if current_user.role == "dept_manager" and body.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="只能将员工归属到本部门")
        emp.department_id = body.department_id
    if body.position is not None:
        emp.position = body.position
    if body.phone is not None:
        emp.phone = body.phone
    if body.email is not None:
        emp.email = body.email
    if body.hire_date is not None:
        emp.hire_date = body.hire_date

    # Handle account update
    if body.username is not None or body.password is not None:
        user = db.query(User).filter(User.employee_id == emp_id).first()
        if user:
            # Update existing user
            if body.username is not None:
                dup = db.query(User).filter(User.username == body.username, User.id != user.id).first()
                if dup:
                    raise HTTPException(status_code=400, detail="用户名已存在")
                user.username = body.username
            if body.password is not None:
                user.password_hash = hash_password(body.password)
        else:
            # Create new user for this employee
            username = body.username or emp.employee_no
            password = body.password or "123456"
            dup = db.query(User).filter(User.username == username).first()
            if dup:
                raise HTTPException(status_code=400, detail=f"用户名 {username} 已存在")
            user = User(
                username=username,
                password_hash=hash_password(password),
                role="employee",
                employee_id=emp.id,
            )
            db.add(user)

    db.commit()
    db.refresh(emp)
    return _employee_to_out(emp)


@router.post("/{emp_id}/create-account")
def create_account(
    emp_id: int,
    username: str = Query(..., min_length=1),
    password: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a login account for an existing employee (admin only)."""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")

    existing = db.query(User).filter(User.employee_id == emp_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该员工已有账号")

    dup = db.query(User).filter(User.username == username).first()
    if dup:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="employee",
        employee_id=emp.id,
    )
    db.add(user)
    db.commit()
    return {"ok": True, "username": username}


@router.post("/{emp_id}/reset-password")
def reset_password(
    emp_id: int,
    password: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reset an employee's login password (admin only)."""
    user = db.query(User).filter(User.employee_id == emp_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="该员工没有账号，请先创建")

    user.password_hash = hash_password(password)
    db.commit()
    return {"ok": True}


@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete an employee (admin only)."""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")

    # Also delete associated user if exists
    user = db.query(User).filter(User.employee_id == emp_id).first()
    if user:
        db.delete(user)

    db.delete(emp)
    db.commit()
    return {"ok": True}
