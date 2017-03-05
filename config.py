import os
basedir=os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY='hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True
    FLASKY_MAIL_SUBJECT_PREFIX='[Flasky]'
    FLASKY_MAIL_SENDER='Flasky Admin <1546331221@qq.com>'
    FLASKY_ADMIN='1546331221@qq.com'
    FLASKY_POSTS_PER_PAGE=20
    FLASKY_FOLLOWERS_PER_PAGE=50
    FLASKY_COMMENTS_PER_PAGE=30
    
    @staticmethod
    def init_app(app):
        pass
        
class DevelopmentConfig(Config):
    DEBUG=True
    MAIL_SERVER='smtp.qq.com'
    MAIL_PORT=465
    MAIL_USE_SSL=True
    MAIL_USERNAME='1546331221'
    MAIL_PASSWORD='kdvzfsillnlghgah'
    SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(basedir,'data-dev.sqlite')
    
class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(basedir,'data-test.sqlite')
    
class ProdictionConfig(Config):
    SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(basedir,'data.sqlite')
 
config={
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProdictionConfig,
    'default': DevelopmentConfig
}
    