from fastapi import Header, HTTPException, Depends

def require_role(role: str):
    async def _require_role(x_user_role: str = Header(default="patient")):
        # Simple demo role-check via header X-User-Role.
        if x_user_role != role and x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden: role required -> " + role)
        return x_user_role
    return _require_role
