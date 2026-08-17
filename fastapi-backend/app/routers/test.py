from fastapi import APIRouter, Depends

from app.models.user import User
from app.dependencies.rbac import require_role

router = APIRouter(
    prefix="/test",
    tags=["RBAC Test"]
)


@router.get("/admin")
def admin_test(
    current_user: User = Depends(require_role("admin"))
):
    return {
        "message": "Welcome Admin",
        "user": current_user.email,
        "role": current_user.role
    }


@router.get("/staff")
def staff_test(
    current_user: User = Depends(require_role("admin", "staff"))
):
    return {
        "message": "Welcome Staff/Admin",
        "user": current_user.email,
        "role": current_user.role
    }


@router.get("/customer")
def customer_test(
    current_user: User = Depends(require_role("customer"))
):
    return {
        "message": "Welcome Customer",
        "user": current_user.email,
        "role": current_user.role
    }