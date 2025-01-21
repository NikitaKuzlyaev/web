from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#     instance.profile.save()


@receiver(user_logged_in)
def create_profile_on_login(sender, request, user, **kwargs):
    # Проверяем, есть ли у пользователя профиль
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
