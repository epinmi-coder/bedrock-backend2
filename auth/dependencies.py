# Auth dependencies (currently disabled - for future implementation)
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    Currently disabled - returns anonymous user.
    """
    # TODO: Implement JWT token validation when authentication is enabled
    return {
        "sub": "anonymous",
        "email": "anonymous@example.com",
        "name": "Anonymous User"
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Optionally get current user. Returns None if not authenticated.
    """
    if not credentials:
        return None
    return await get_current_user(credentials)


def require_groups(*groups: str):
    """
    Dependency to require user to be in specific groups.
    Currently disabled - always allows access.
    """
    async def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        # TODO: Implement group checking when authentication is enabled
        user_groups = current_user.get("groups", [])
        if not any(group in user_groups for group in groups):
            # For now, just return the user (auth disabled)
            pass
        return current_user
    return dependency
