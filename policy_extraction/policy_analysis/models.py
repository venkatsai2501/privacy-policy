from django.db import models
from django.contrib.auth.models import User

class TrackedSite(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    last_checked = models.DateTimeField(null=True, blank=True)
    
    privacy_policy_last_updated = models.DateField(null=True, blank=True)
    terms_of_service_last_updated = models.DateField(null=True, blank=True)
    # Privacy Policy
    privacy_policy_extracted = models.TextField(null=True, blank=True)
    privacy_policy_summary = models.TextField(null=True, blank=True)
    
    # Terms of Service
    terms_of_service_extracted = models.TextField(null=True, blank=True)
    terms_of_service_summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title