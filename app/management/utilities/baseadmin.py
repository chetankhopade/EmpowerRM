from django.contrib import admin

from empowerb.middleware import db_ctx


class MultiDBModelAdminCommon(admin.ModelAdmin):

    @property
    def db_name(self):
        return db_ctx.get()

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.db_name)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.db_name)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(MultiDBModelAdminCommon, self).get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query on the 'other' database.
        return super(MultiDBModelAdminCommon, self).formfield_for_foreignkey(db_field, request,
                                                                             using=self.db_name, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query on the 'other' database.
        return super(MultiDBModelAdminCommon, self).formfield_for_manytomany(db_field, request,
                                                                             using=self.db_name, **kwargs)
