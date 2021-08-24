from django.db import router

from empowerb.routers.app import APPRouter


class MultiDBMixin:
    "A mixin to allow a TestCase to select the DB to use."

    multi_db = True

    def setUp(self, *args, **kwargs):
        super(MultiDBMixin, self).setUp(*args, **kwargs)
        self.original_routers = router.routers
        router.routers = [APPRouter()]

    def tearDown(self, *args, **kwargs):
        super(MultiDBMixin, self).tearDown(*args, **kwargs)
        # Reinstate the original routers
        router.routers = self.original_routers
