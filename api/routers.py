from django.conf import settings

from PoleLuxe.mixins.routers import WithAnalytics


class APIRouter(WithAnalytics):
    """
    A router for analytics_db from django-albert.
    """
    ANALYTICS_DB_ALIAS = settings.ANALYTICS_DB_ALIAS

    def db_for_read(self, model, **hints):
        """
        Attempts to read from a `analytics` model go to the
        analytics database.
        """
        return self.use_analytics_db_or_default(model.__name__)

    def db_for_write(self, model, **hints):
        """
        Attempts to write analytics data go to analytics_db.
        """
        return self.use_analytics_db_or_default(model.__name__)

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if the objects belong to the same
        database alias.
        """
        return obj1._state.db == obj2._state.db or None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure an analytics model appears only in the 'analytics_db'
        """
        if db == APIRouter.ANALYTICS_DB_ALIAS:
            return self.is_analytics_model(model_name)
        elif self.is_analytics_model(model_name):
            # If we are working on a analytics model, and the db is not
            # analytics_db, return false
            return False
        return None

    def use_analytics_db_or_default(self, model_name):
        if self.is_analytics_model(model_name):
            return APIRouter.ANALYTICS_DB_ALIAS
        return None

    def is_analytics_model(self, model_name):
        if model_name is not None:
            return str(model_name).lower() in ['session', 'activity', 'analytics']
        return False


class AnalyticsQuizRouter(object):
    """
    A router for analytics_quiz_db from django-albert.
    """
    ANALYTICS_DB_ALIAS = settings.ANALYTICS_QUIZ_DB_ALIAS

    def db_for_read(self, model, **hints):
        """
        Attempts to read from a `analytics_quiz_db` model go to the
        analytics database.
        """
        return self.use_analytics_db_or_default(model.__name__)

    def db_for_write(self, model, **hints):
        """
        Attempts to write analytics data go to analytics_quiz_db.
        """
        return self.use_analytics_db_or_default(model.__name__)

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if the objects belong to the same
        database alias.
        """
        return obj1._state.db == obj2._state.db or None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure an analytics model appears only in the 'analytics_quiz_db'
        """
        if db == self.ANALYTICS_DB_ALIAS:
            return self.is_analytics_model(model_name)
        elif self.is_analytics_model(model_name):
            # If we are working on a analytics model, and the db is not
            # analytics_quiz_db, return false
            return False
        return None

    def use_analytics_db_or_default(self, model_name):
        if self.is_analytics_model(model_name):
            return self.ANALYTICS_DB_ALIAS
        return None

    def is_analytics_model(self, model_name):
        return model_name is not None and model_name.lower() in [
            'quizresult'
        ]
