from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime
from markdown import markdown
import bleach

class Role(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(64), unique=True)
    users=db.relationship('User', backref='role', lazy='dynamic')
    default=db.Column(db.Boolean, default=False, index=True)
    permissions=db.Column(db.Integer)
    
    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.DELETE, True),
            'Moderator_12':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.DELETE | Permission.MODERATE_COMMENTS |Permission.MODERATE_DELETE | Permission.MODERATE_12, False),
            'Moderator_11':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.DELETE | Permission.MODERATE_COMMENTS |Permission.MODERATE_DELETE | Permission.MODERATE_11, False),
            'Administrator': (0xffff, False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()
    
    def __repr__(self):
        return '<Role %r>' % self.name
        
class Permission:
    FOLLOW=0x0001
    COMMENT=0x0002
    WRITE_ARTICLES=0x0004
    DELETE=0x0008
    MODERATE_COMMENTS=0x0010  
    MODERATE_DELETE=0x0020
    MODERATE_12=0x0040
    MODERATE_11=0x0080
    ADMINISTER=0x8000
        
class User(db.Model, UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(64), unique=True, index=True)
    role_id=db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash=db.Column(db.String(128))
    email=db.Column(db.String(64), unique=True, index=True)
    confirmed=db.Column(db.Boolean, default=False)
    name=db.Column(db.String(64))
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(), default=datetime.utcnow())
    last_seen=db.Column(db.DateTime(), default=datetime.utcnow())
    posts=db.relationship('Post', backref='author', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['FLASKY_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xffff).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()
                
    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)
        
    def is_moderator_12(self):
        return self.can(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.DELETE | Permission.MODERATE_COMMENTS |Permission.MODERATE_DELETE | Permission.MODERATE_12)
        
    def is_moderator_11(self):
        return self.can(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.DELETE | Permission.MODERATE_COMMENTS |Permission.MODERATE_DELETE | Permission.MODERATE_11)
        
    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash=generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return '<User %r>' % self.username
        
    def generate_confirmation_token(self, expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
        
    def confirm(self, token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        return True
    
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True
        
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True
    
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        
        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
                   username=forgery_py.internet.user_name(True),
                   password=forgery_py.lorem_ipsum.word(),
                   confirmed=True,
                   name=forgery_py.name.full_name(),
                   location=forgery_py.address.city(),
                   about_me=forgery_py.lorem_ipsum.sentence(),
                   member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    
    def is_administrator(self):
        return False
        
login_manager.anonymous_user=AnonymousUser

 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
class Post(db.Model):
    __tablename__='posts'
    id=db.Column(db.Integer, primary_key=True)
    body=db.Column(db.Text)
    timestamp=db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html=db.Column(db.Text)
    forum_id=db.Column(db.Integer, db.ForeignKey('forums.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            f = Forum.query.offset(randint(0, 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u,
                     subforum=f)
            db.session.add(p)
            db.session.commit()
    
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)  

class Forum(db.Model):
    __tablename__='forums'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(64), unique=True)
    posts=db.relationship('Post', backref='subforum', lazy='dynamic')
    
    @staticmethod
    def insert_forums():
        forums={'twelve', 'eleven'}
        for r in forums:
            forum=Forum.query.filter_by(name=r).first()
            if forum is None:
                forum=Forum(name=r)
            db.session.add(forum)
        db.session.commit()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    