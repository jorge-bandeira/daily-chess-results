from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerRangeField
from wtforms.validators import DataRequired

class MainForm(FlaskForm):
	user = StringField("...", validators = [DataRequired()])
	max_games = IntegerRangeField("", default = 100)
	submit = SubmitField("RUN")