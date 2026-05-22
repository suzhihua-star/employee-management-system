"""Seed the database with sample data for demo purposes."""
from datetime import date

from database import SessionLocal, engine, Base
from models import Department, Employee, CheckIn, User, SystemSetting
from routers.auth import hash_password


def seed():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Skip if already seeded
    if db.query(Department).count() > 0:
        db.close()
        print("Database already seeded, skipping.")
        return

    # ── Departments ────────────────────────────────
    root = Department(name="XX科技有限公司", parent_id=None, description="公司总部")
    db.add(root)
    db.flush()

    tech = Department(name="技术部", parent_id=root.id, description="负责产品研发与技术管理")
    market = Department(name="市场部", parent_id=root.id, description="负责市场推广与销售")
    hr = Department(name="人事行政部", parent_id=root.id, description="负责人力资源与行政事务")
    finance = Department(name="财务部", parent_id=root.id, description="负责财务管理与会计核算")
    db.add_all([tech, market, hr, finance])
    db.flush()

    frontend = Department(name="前端开发组", parent_id=tech.id, description="Web前端与移动端开发")
    backend = Department(name="后端开发组", parent_id=tech.id, description="服务端与API开发")
    db.add_all([frontend, backend])
    db.flush()

    # ── Employees ──────────────────────────────────
    employees_data = [
        # 技术部
        {"name": "张伟", "employee_no": "EMP001", "department_id": tech.id, "position": "技术总监", "phone": "13800001001", "email": "zhangwei@example.com"},
        {"name": "李娜", "employee_no": "EMP002", "department_id": frontend.id, "position": "前端工程师", "phone": "13800001002", "email": "lina@example.com"},
        {"name": "王强", "employee_no": "EMP003", "department_id": backend.id, "position": "后端工程师", "phone": "13800001003", "email": "wangqiang@example.com"},
        {"name": "赵敏", "employee_no": "EMP004", "department_id": frontend.id, "position": "UI设计师", "phone": "13800001004", "email": "zhaomin@example.com"},
        # 市场部
        {"name": "陈明", "employee_no": "EMP005", "department_id": market.id, "position": "市场总监", "phone": "13800001005", "email": "chenming@example.com"},
        {"name": "刘芳", "employee_no": "EMP006", "department_id": market.id, "position": "市场专员", "phone": "13800001006", "email": "liufang@example.com"},
        # 人事行政部
        {"name": "周杰", "employee_no": "EMP007", "department_id": hr.id, "position": "HR经理", "phone": "13800001007", "email": "zhoujie@example.com"},
        # 财务部
        {"name": "吴婷", "employee_no": "EMP008", "department_id": finance.id, "position": "财务主管", "phone": "13800001008", "email": "wuting@example.com"},
    ]

    emp_objects = {}
    for e in employees_data:
        emp = Employee(
            name=e["name"],
            employee_no=e["employee_no"],
            department_id=e["department_id"],
            position=e["position"],
            phone=e["phone"],
            email=e["email"],
            hire_date=date.today(),
        )
        db.add(emp)
        db.flush()
        emp_objects[e["employee_no"]] = emp

    # ── Users ──────────────────────────────────────
    users_data = [
        {"username": "admin",   "password": "admin123",   "role": "super_admin",   "employee_id": None,                "department_id": None},
        {"username": "zhangwei","password": "123456",      "role": "dept_manager",  "employee_id": emp_objects["EMP001"].id, "department_id": tech.id},
        {"username": "chenming","password": "123456",      "role": "dept_manager",  "employee_id": emp_objects["EMP005"].id, "department_id": market.id},
        {"username": "lina",    "password": "123456",      "role": "employee",      "employee_id": emp_objects["EMP002"].id, "department_id": None},
        {"username": "wangqiang","password": "123456",     "role": "employee",      "employee_id": emp_objects["EMP003"].id, "department_id": None},
        {"username": "zhaomin", "password": "123456",      "role": "employee",      "employee_id": emp_objects["EMP004"].id, "department_id": None},
        {"username": "liufang", "password": "123456",      "role": "employee",      "employee_id": emp_objects["EMP006"].id, "department_id": None},
    ]

    for u in users_data:
        user = User(
            username=u["username"],
            password_hash=hash_password(u["password"]),
            role=u["role"],
            employee_id=u["employee_id"],
            department_id=u["department_id"],
        )
        db.add(user)

    # System settings
    if db.query(SystemSetting).count() == 0:
        db.add(SystemSetting(company_name="XX科技有限公司"))

    db.commit()
    db.close()
    print("Seed data created successfully!")
    print()
    print("── 测试账号 ──────────────")
    for u in users_data:
        print(f"  {u['role']:15s} | {u['username']:12s} | {u['password']}")


if __name__ == "__main__":
    seed()
