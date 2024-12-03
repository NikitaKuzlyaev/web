from .models import Profile, Contest

def have_access(user, contest_id):
    # Проверка, что пользователь является администратором
    if user.is_staff:
        return True

    # Получаем соревнование
    contest = Contest.objects.filter(id=contest_id).first()
    if not contest:
        return False  # Если соревнования нет, доступ запрещен

    # Проверка, что соревнование открыто
    if contest.is_open:
        return True

    # Проверка, что у пользователя есть доступ к этому соревнованию
    try:
        # Проверяем, есть ли у пользователя профиль с доступом к текущему соревнованию
        profile = Profile.objects.get(user=user)
        if profile.contest_access == contest:
            return True
    except Profile.DoesNotExist:
        return False  # У пользователя нет профиля или доступа к этому соревнованию

    return False  # Если ни одно условие не выполнено, доступ запрещен