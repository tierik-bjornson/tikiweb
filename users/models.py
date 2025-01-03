from cloudinary_storage.storage import RawMediaCloudinaryStorage # type: ignore
from django.contrib.auth.models import AbstractUser # type: ignore
from django.db import models # type: ignore

# Create your models here.

class User(AbstractUser):
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    purchase_address = models.TextField(null=True, blank=True)
    delivery_address = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, storage=RawMediaCloudinaryStorage())
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'firs_name': self.first_name,
            'last_name': self.last_name,
        }