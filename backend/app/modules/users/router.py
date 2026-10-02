"""HTTP routes for the current user's own profile."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """Returns the profile of whoever owns the bearer token sent in the request."""
    return UserRead.model_validate(current_user)
