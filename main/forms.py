from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerRangeField, BooleanField
from wtforms.validators import DataRequired
from main import local_settings

class MainForm(FlaskForm):
	user = StringField("...", validators = [DataRequired()])
	max_games = IntegerRangeField("", default = local_settings.max_games / 2)
	classical = BooleanField()
	rapid = BooleanField()
	blitz = BooleanField()
	bullet = BooleanField()
	submit = SubmitField("RUN")