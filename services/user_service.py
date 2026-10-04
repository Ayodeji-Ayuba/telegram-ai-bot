from models.models import User


def get_or_create_user(db, tg_user):
    """Return the User row for a Telegram user, creating it on first contact.

    db is an open database session; the caller stays responsible for closing it.
    """
    user = db.query(User).filter(User.telegram_id == tg_user.id).first()
    if not user:
        user = User(telegram_id=tg_user.id, username=tg_user.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
