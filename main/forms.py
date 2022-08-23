from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class MainForm(FlaskForm):
	user = StringField("...", validators = [DataRequired()])
	submit = SubmitField("RUN")