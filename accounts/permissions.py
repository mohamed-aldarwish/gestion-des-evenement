def user_role(user):
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return 'admin'

    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None)


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def is_organizer(user):
    return user.is_authenticated and user_role(user) == 'organizer'


def can_reserve_events(user):
    return user.is_authenticated and user_role(user) == 'user'


def can_manage_event(user, event=None):
    if is_admin(user):
        return True

    if not is_organizer(user):
        return False

    return event is None or event.organizer_id == user.id
