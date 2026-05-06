from app.models.enums import UserRole

ROLE_PERMISSIONS: dict[str, list[str]] = {
    UserRole.ADMIN: [
        "manage_users",
        "create_project",
        "delete_project",
        "manage_members",
        "create_task",
        "edit_task",
        "delete_task",
        "view_task",
    ],
    UserRole.USER: [
        "create_project",
        "create_task",
        "edit_task",
        "delete_task",
        "view_task",
    ],
}


def has_permission(role: UserRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])
