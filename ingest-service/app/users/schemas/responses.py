from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class UserResponse(BaseModel):
    """User response schema."""
    user_id: str
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    roles: List[str]
    permissions: List[str]
    created_at: Optional[datetime]
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}