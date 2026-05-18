import uuid

from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def profile_avatar_upload_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower()
    return f'profile_avatars/user_{instance.user_id}/{uuid.uuid4().hex}.{extension}'


class Profile(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('organizer', 'Organizer'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(
        upload_to=profile_avatar_upload_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
    )
    bio = models.TextField(max_length=500, blank=True, default='')
    website_url = models.URLField(max_length=255, blank=True, default='')
    linkedin_url = models.URLField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def display_role(self):
        if self.user.is_superuser:
            return 'Admin'
        return self.get_role_display()


@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            role='admin' if instance.is_superuser else 'user'
        )
    else:
        profile, _ = Profile.objects.get_or_create(user=instance)
        if instance.is_superuser and profile.role != 'admin':
            profile.role = 'admin'
        profile.save()
