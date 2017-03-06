from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User, Post, Forum

class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')
    
class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')
    
class EditProfileAdminForm(Form):
    email=StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username=StringField('Username', validators=[Required(), Length(1, 64), 
                                                 Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    confirmed=BooleanField('Confirmed')
    role=SelectField('Role')
    name=StringField('Real name', validators=[Length(0 ,64)])
    location=StringField('Location', validators=[Length(0, 64)])
    about_me=TextAreaField('About me')
    submit=SubmitField('Submit')
    
    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices=[('User', 'User'),('Administrator', 'Administrator')]
        for forum in Forum.query.order_by(Forum.id).all():
            self.role.choices.append(('Moderator of '+forum.name, 'Moderator of '+forum.name))
        self.user=user
        
    def validate_email(self, field):
        if field.data!=self.user.email and \
                user.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
         
    def validate_username(self, field):
        if field.data!=self.user.username and \
                user.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
            
class AddSubforumForm(Form):
    name=StringField('Route Name', validators=[Required(), Length(1, 64)])
    forumname=StringField('SubForum Name', validators=[Required(), Length(1, 64)])
    color=SelectField('Title Color', validators=[Required()], choices=[('red', 'red'),('brown', 'brown'),('green', 'green'),('orange', 'orange')] )
    submit=SubmitField('Submit')
   
    
class DeleteSubforumForm(Form):
    forum=SelectField('Delete Name', coerce=int)
    submit=SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        super(DeleteSubforumForm, self).__init__(*args, **kwargs)
        self.forum.choices=[(forum.id, forum.forumname)
                            for forum in Forum.query.order_by(Forum.id).all()]
                            
                            
                            
                            