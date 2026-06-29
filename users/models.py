from django.db import models
from django.contrib.auth.models import User






class Profile(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Adminstrator'),
    )


    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    