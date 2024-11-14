from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from phonenumber_field.modelfields import PhoneNumberField


USER_TYPE = (
    ('Vendor', 'Vendor'),
    ('Customer', 'Customer'),
)


class User(AbstractUser):
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def clean(self):
        super().clean()
        if not self.username:
            self.username = self.email.split('@')[0]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username or self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile/images', default='default-user.jpg')
    full_name = models.CharField(max_length=200, null=True, blank=True)
    mobile = PhoneNumberField(null=True, blank=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE, default='Customer')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.user.username or str(self.user)