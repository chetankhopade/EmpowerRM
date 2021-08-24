
class APPRouter:

    def db_for_read(self, model, **hints):

        if model._meta.app_label == 'ermm':
            return 'default'

        elif model._meta.app_label == 'erms':
            return 'qa'

    db_for_write = db_for_read

    def allow_syncdb(self, db, model):

        if model._meta.app_label == 'ermm':
            return db == 'default'

        elif model._meta.app_label == 'erms':
            return db == 'qa'
