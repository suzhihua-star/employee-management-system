"""Authentication router — login and permission helpers."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Security config ───────────────────────────────────

SECRET_KEY = "enterprise-mgmt-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return the current User, or raise 401."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise HTTPException(status_code=401, detail="无效的登录凭证")
        user_id: int = int(user_id_raw)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only super_admin can proceed."""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    """super_admin or dept_manager can proceed."""
    if current_user.role not in ("super_admin", "dept_manager"):
        raise HTTPException(status_code=403, detail="需要主管及以上权限")
    return current_user


# ── Routes ────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT token."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    employee_name = None
    if user.employee_id and user.employee:
        employee_name = user.employee.name

    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            username=user.username,
            role=user.role,
            employee_id=user.employee_id,
            department_id=user.department_id,
            employee_name=employee_name,
        ),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return current logged-in user info."""
    employee_name = None
    if current_user.employee_id and current_user.employee:
        employee_name = current_user.employee.name
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        employee_id=current_user.employee_id,
        department_id=current_user.department_id,
        employee_name=employee_name,
    )


@router.post("/change-password")
def change_password(
    old_password: str = Query(...),
    new_password: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Self-service password change for any logged-in user."""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {"ok": True}
