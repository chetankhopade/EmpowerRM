from _contextvars import ContextVar

from django.utils.deprecation import MiddlewareMixin

from empowerb.settings import DATABASES

db_ctx = ContextVar('var')


class WhichDatabaseIsTOUseMIddleware(MiddlewareMixin):
    """
        Middleware to update the context var with the db alias
    """
    @staticmethod
    def process_request(request):
        try:
            db_name_path = request.path.split('/')[1]
            db_name = db_name_path.split('_')[0] if '_' in db_name_path else db_name_path
            # set contextvar with the database name if dbname exist in DATABASES dict
            db_ctx.set(db_name) if db_name in DATABASES.keys() else db_ctx.set('NoOP')
        except Exception as ex:
            print(ex.__str__())
            db_ctx.reset('NoOP')
