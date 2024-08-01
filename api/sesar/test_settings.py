from sesar.settings import *
from django.test.runner import DiscoverRunner

class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

class UnManagedModelTestRunner(DiscoverRunner):

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps
        get_models = apps.get_models
        self.unmanaged_models = [m for m in get_models() if not m._meta.managed]
        for m in self.unmanaged_models:
            m._meta.managed = True

        super(UnManagedModelTestRunner, self).setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).teardown_test_environment(*args, **kwargs)
        for m in self.unmanaged_models:
            m._meta.managed = False


# Skip the migrations by setting "MIGRATION_MODULES"
# to the DisableMigrations class defined above
MIGRATION_MODULES = DisableMigrations()

# Set Django's test runner to the custom class defined above
TEST_RUNNER = 'sesar.test_settings.UnManagedModelTestRunner'