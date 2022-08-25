from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerRangeField, BooleanField
from wtforms.validators import DataRequired

class MainForm(FlaskForm):
	user = StringField("...", validators = [DataRequired()])
	max_games = IntegerRangeField("", default = 250)
	classical = BooleanField()
	rapid = BooleanField()
	blitz = BooleanField()
	bullet = BooleanField()
	submit = SubmitField("RUN")