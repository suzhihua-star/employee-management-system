"""Department CRUD router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Department, Employee, User
from routers.auth import get_current_user, require_admin
from schemas import DepartmentCreate, DepartmentUpdate, DepartmentOut

router = APIRouter(prefix="/api/departments", tags=["departments"])


def _build_tree(departments: list[Department], db: Session) -> list[dict]:
    """Build a nested tree from a flat department list, with employee counts."""
    dept_map = {}
    roots = []

    for d in departments:
        count = db.query(Employee).filter(Employee.department_id == d.id).count()
        node = {
            "id": d.id,
            "name": d.name,
            "parent_id": d.parent_id,
            "description": d.description or "",
            "created_at": d.created_at,
            "employee_count": count,
            "children": [],
        }
        dept_map[d.id] = node

    for d in departments:
        node = dept_map[d.id]
        if d.parent_id and d.parent_id in dept_map:
            dept_map[d.parent_id]["children"].append(node)
        else:
            roots.append(node)

    # Recursively sum child counts into parents
    def sum_counts(node):
        total = node["employee_count"]
        for child in node["children"]:
            total += sum_counts(child)
        node["employee_count"] = total
        return total

    for root in roots:
        sum_counts(root)

    return roots


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Get all departments as a tree."""
    depts = db.query(Department).order_by(Department.id).all()
    return _build_tree(depts, db)


@router.post("", response_model=DepartmentOut)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Create a new department (admin only)."""
    if body.parent_id:
        parent = db.query(Department).filter(Department.id == body.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="父级部门不存在")

    dept = Department(
        name=body.name,
        parent_id=body.parent_id,
        description=body.description,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        parent_id=dept.parent_id,
        description=dept.description or "",
        created_at=dept.created_at,
        employee_count=0,
        children=[],
    )


@router.put("/{dept_id}", response_model=DepartmentOut)
def update_department(
    dept_id: int,
    body: DepartmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Update a department (admin only)."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    if body.name is not None:
        dept.name = body.name
    if body.parent_id is not None:
        if body.parent_id == dept_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父级部门")
        dept.parent_id = body.parent_id
    if body.description is not None:
        dept.description = body.description

    db.commit()
    db.refresh(dept)
    count = db.query(Employee).filter(Employee.department_id == dept.id).count()
    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        parent_id=dept.parent_id,
        description=dept.description or "",
        created_at=dept.created_at,
        employee_count=count,
        children=[],
    )


@router.delete("/{dept_id}")
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Delete a department (admin only). Refuses if it has employees or children."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # Check children
    child_count = db.query(Department).filter(Department.parent_id == dept_id).count()
    if child_count > 0:
        raise HTTPException(status_code=400, detail="该部门下有子部门，请先删除子部门")

    # Check employees
    emp_count = db.query(Employee).filter(Employee.department_id == dept_id).count()
    if emp_count > 0:
        raise HTTPException(status_code=400, detail="该部门下还有员工，请先转移或删除员工")

    db.delete(dept)
    db.commit()
    return {"ok": True}
