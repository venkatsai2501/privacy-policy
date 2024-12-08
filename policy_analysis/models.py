from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TrackedSite(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    logourl = models.URLField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    last_checked = models.DateTimeField(null=True, blank=True)

    # Current Policy Details
    privacy_policy_last_updated = models.DateField(null=True, blank=True)
    terms_of_service_last_updated = models.DateField(null=True, blank=True)
    privacy_policy_extracted = models.TextField(null=True, blank=True)
    privacy_policy_summary = models.TextField(null=True, blank=True)
    terms_of_service_extracted = models.TextField(null=True, blank=True)
    terms_of_service_summary = models.TextField(null=True, blank=True)

    auto_scan_enabled = models.BooleanField(default=False)
    last_auto_scan_time = models.DateTimeField(null=True, blank=True)

    # History as JSON
    privacy_policy_history = models.JSONField(default=list)  # Stores policy history

    def add_policy_to_history(self, new_policy, new_summary, new_date):
        """
        Add the new policy to history only if the date or content has changed.
        """
        self.refresh_from_db()  # Ensure fresh model data
        if not self.privacy_policy_history:
            self.privacy_policy_history = []

        last_entry = self.privacy_policy_history[-1] if self.privacy_policy_history else {}
        last_date = last_entry.get("date")
        last_policy = last_entry.get("privacy_policy_extracted")

        # Convert new_date to ISO format string
        new_date_str = new_date.strftime('%Y-%m-%d') if new_date else ""

        if new_date_str != last_date or new_policy.strip() != (last_policy or "").strip():
            # Ensure only serializable types are saved
            history_entry = {
                "date": new_date_str,
                "privacy_policy_extracted": new_policy.strip(),
                "privacy_policy_summary": new_summary.strip(),
            }
            self.privacy_policy_history.append(history_entry)
            self.save()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
