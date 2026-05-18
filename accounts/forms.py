from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from .models import Profile


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'profile-input',
            'placeholder': 'email@example.com',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'Username',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'Last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'profile-input',
                'placeholder': 'email@example.com',
            }),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Username is required.')

        exists = User.objects.filter(username__iexact=username).exclude(
            pk=self.instance.pk
        ).exists()

        if exists:
            raise forms.ValidationError('This username is already in use.')

        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not email:
            raise forms.ValidationError('Email address is required.')

        exists = User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists()

        if exists:
            raise forms.ValidationError('This email address is already in use.')

        return email


class ProfileUpdateForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False)

    class Meta:
        model = Profile
        fields = [
            'phone',
            'avatar',
            'bio',
            'website_url',
            'linkedin_url',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': '+212 600 000 000',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'profile-file-input',
                'accept': 'image/jpeg,image/png,image/webp',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'profile-input profile-textarea',
                'rows': 4,
                'placeholder': 'Short professional bio',
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'profile-input',
                'placeholder': 'https://example.com',
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'profile-input',
                'placeholder': 'https://www.linkedin.com/in/username',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone') or ''
        phone = phone.strip()

        if phone and len(phone) < 7:
            raise forms.ValidationError('Enter a valid phone number.')

        allowed = set('0123456789+-.() ')
        if phone and any(character not in allowed for character in phone):
            raise forms.ValidationError(
                'Phone number can only contain numbers, spaces, +, -, dots, and parentheses.'
            )

        return phone

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if not avatar or not hasattr(avatar, 'content_type'):
            return avatar

        max_size = getattr(settings, 'PROFILE_AVATAR_MAX_SIZE', 2 * 1024 * 1024)
        allowed_types = getattr(
            settings,
            'PROFILE_AVATAR_ALLOWED_CONTENT_TYPES',
            ('image/jpeg', 'image/png', 'image/webp'),
        )

        if avatar.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f'Profile image must be smaller than {max_size_mb:.0f} MB.'
            )

        if avatar.content_type not in allowed_types:
            raise forms.ValidationError(
                'Upload a JPG, PNG, or WebP image.'
            )

        return avatar

    def clean(self):
        cleaned_data = super().clean()
        avatar = cleaned_data.get('avatar')
        remove_avatar = cleaned_data.get('remove_avatar')

        if remove_avatar and avatar and hasattr(avatar, 'content_type'):
            raise forms.ValidationError(
                'Choose either a new image or remove the current image, not both.'
            )

        return cleaned_data
