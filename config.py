
import os


class Config(object):
    """
    Base class for application configuration details.
    """
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    pass

config = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'default': ProductionConfig
}
