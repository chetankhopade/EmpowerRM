import datetime
import uuid

from django.db import models

from cuser.middleware import CuserMiddleware


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # Django Multiple Databases Limitations (https://docs.djangoproject.com/en/2.1/topics/db/multi-db/)
    # Django doesn’t currently provide any support for foreign key or many-to-many relationships spanning multiple db_names
    created_by = models.CharField(max_length=100, blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True

    def get_id_str(self):
        return self.id.__str__()

    def save(self, *args, **kwargs):
        # middleware to get the authenticated user and then logic to update model fields with the username and datetime
        user = CuserMiddleware.get_user()
        if user:
            if not self.pk:
                self.created_by = user.username
            self.updated_by = user.username
            self.updated_at = datetime.datetime.now()
        super(BaseModel, self).save(*args, **kwargs)
