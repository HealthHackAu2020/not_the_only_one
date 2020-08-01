from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
)
from wtforms.validators import (
    InputRequired,
    Length,
)

class SearchForm(FlaskForm):
    terms = StringField('Search', validators=[InputRequired(), Length(1, 128)])
