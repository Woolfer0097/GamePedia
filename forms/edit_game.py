from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, SelectField
from wtforms.validators import DataRequired


class EditGameForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    game_author = StringField('Автор', validators=[DataRequired()])
    genre = SelectField('Жанр', coerce=int)
    submit = SubmitField('Сохранить')
