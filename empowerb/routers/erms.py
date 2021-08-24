from empowerb.middleware import db_ctx

from empowerb.settings import DATABASES


class ERMSRouter:
    """
    A router to control all database operations on models in the ermm application.
    """
    @staticmethod
    def db_for_read(model, **hints):
        """
        Attempts to read auth models go to auth_db.
        """
        try:
            db = db_ctx.get()
        except:
            db = None

        if db and db != 'NoOP' and db != 'default' and model._meta.app_label == 'erms':
            return db
        return None

    @staticmethod
    def db_for_write(model, **hints):
        """
        Attempts to write auth models go to auth_db.
        """
        try:
            db = db_ctx.get()
        except:
            db = None

        if db and db != 'NoOP' and db != 'default' and model._meta.app_label == 'erms':
            return db
        return None

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        """
        Allow relations if a model in the auth app is involved.
        """
        if obj1._meta.app_label == 'erms' or obj2._meta.app_label == 'erms':
            return True
        return None

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'auth_db' database.
        """
        if app_label == 'erms':
            return db in [k for k in DATABASES.keys() if k != 'default']
        return None
