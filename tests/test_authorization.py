from app.authorization import is_admin

def test_admin_authorized(): assert is_admin(123, 123)
def test_other_user_rejected(): assert not is_admin(124, 123)
def test_missing_user_rejected(): assert not is_admin(None, 123)
