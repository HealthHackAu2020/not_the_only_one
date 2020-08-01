from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
    HiddenField,
    DecimalField,
    SelectField
)
from wtforms.fields.html5 import EmailField, DateTimeField, IntegerField, DateField
from wtforms.validators import (
    Email,
    EqualTo,
    InputRequired,
    Length,
    DataRequired,
    NumberRange
)
from app import db
from app.models import Role, User, Group, LookupValue, Category


class NewCategoryForm(FlaskForm):
  name = StringField('Name', validators=[InputRequired(), Length(1, 64)])
  submit = SubmitField('Create')
  

class EditCategoryForm(NewCategoryForm):
  submit = SubmitField('Update')


class EditStoryForm(FlaskForm):
  thread = QuerySelectField("Story is part of a thread?", allow_blank=True, query_factory=lambda: LookupValue.query.filter_by(group='bool'))
  visible = QuerySelectField("Allow collection to be seen by others?", allow_blank=True, query_factory=lambda: LookupValue.query.filter_by(group='bool'))
  categories = QuerySelectMultipleField('Categories', query_factory=lambda: db.session.query(Category).order_by('id'))
  submit = SubmitField('Update')


class ReviewStoryForm(EditStoryForm):
  submit = SubmitField('Review')


class NewGroupForm(FlaskForm):
  name = StringField('Name', validators=[InputRequired(), Length(1, 64)])
  users = QuerySelectMultipleField('Users', query_factory=lambda: db.session.query(User).order_by('first_name'))
  submit = SubmitField('Create')
  

class EditGroupForm(NewGroupForm):
  submit = SubmitField('Update')


class InviteUserForm(FlaskForm):
    role = QuerySelectField(
        'Account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    groups = QuerySelectMultipleField('Groups', get_label='name', query_factory=lambda: db.session.query(Group).order_by('name')) 
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Create')


class EditUserForm(InviteUserForm):
  id = HiddenField('id')
  submit = SubmitField('Edit')

  def validate_email(self, field):
    if User.query.filter_by(email=field.data).first():
      if User.query.filter_by(email=field.data).first().id != int(self.uid.data):
        raise ValidationError('Email already registered.')

