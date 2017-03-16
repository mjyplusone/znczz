from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
from flask.ext.pagedown.fields import PageDownField

  
class PostForm(Form):
    body = PageDownField("What's on your mind?", validators=[Required()])
    submit = SubmitField('Submit')
    
class CommentForm(Form):
    body=StringField('Enter your comment', validators=[Required()])
    submit=SubmitField('Submit')
    
class SetModeratorForm(Form):
    setmoderator=SelectField('Set or change Moderator of this forum', coerce=int)  
    submit=SubmitField('Submit')   

    def __init__(self, *args, **kwargs):
        super(SetModeratorForm, self).__init__(*args, **kwargs)
        self.setmoderator.choices=[(0, 'none')]
        for user in User.query.order_by(User.id).all():
            if user.role.name=='User':
                self.setmoderator.choices.append((user.id, user.username))