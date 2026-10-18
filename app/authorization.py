def is_admin(user_id, admin_id: int) -> bool:
    return user_id is not None and int(user_id) == int(admin_id)
