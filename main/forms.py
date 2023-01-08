from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerRangeField, BooleanField, RadioField
from wtforms.validators import DataRequired

class MainForm(FlaskForm):
	user = StringField("...", validators = [DataRequired()])
	max_games = IntegerRangeField("", default = 200)
	classical = BooleanField()
	rapid = BooleanField()
	blitz = BooleanField()
	bullet = BooleanField()
	submit = SubmitField("RUN")
	source = RadioField("", choices = [(0,'Chess.com'),(1,'Lichess.org')], default = 0, validators = [DataRequired()])