from flask import Flask,render_template,flash,redirect,url_for,request
from flask_wtf import Form
from wtforms import widgets, StringField,TextField,SelectMultipleField, PasswordField, validators,\
HiddenField,TextAreaField, BooleanField, SelectField, SelectMultipleField
from wtforms_components import DateTimeField,DateRange
from datetime import datetime
import datetime as DT
from wtforms.validators import Required,EqualTo, Optional,Length, Email
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import os

# configuration
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'you-will-never-guess'
db = SQLAlchemy(app)
manager = Manager(app)
Bootstrap = Bootstrap(app)

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

# classes for create form
class EasyForm(Form):
	name = TextField('* Name', validators=[
			Required('Please enter your name')])
	surname = TextField('* Surname', validators=[
			Required('Please enter your surname:')])
	email = TextField('* Email address', validators=[
		   Required('Please enter your email:'),
           Length(min=6, message=(u'Email address too short')),
           Email(message=(u'That\'s not a valid email address.'))])
	department = SelectField('* Office / Department', choices=[('', 'Select your department'), ('Rectors Office', 'Rectors Office'), ('Rectors Cabinet', 'Rectors Cabinet'),
		('AEQI', 'AEQI'), ('Research and Projects Office', 'Research and Projects Office'), ('Internatonal Relations Office', 'Internatonal Relations Office'),
		('6', 'Office of the Secretary General'), ('7', 'Finance Office')], validators=[
			Required('Your answer is required')])
	title = TextField('* Title of the activity', validators=[
			Required('Your answer is required')])
	type = TextField('* Type of the activity', validators=[
			Required('Your answer is required')])
	date = StringField('* Date of the activity')
	venue = TextField('* Venue of the activity', validators=[
			Required('Your answer is required')])
	celebrities = TextField('Celebrities / public figures invited')
	brief = TextAreaField('* Brief an activity', validators=[
			Required('Your answer is required')])
	agree = BooleanField('Send me a copy of my respones')
	string_of_files = ['Poster design,Leaflet Design,Publication on facebook,Publication on facebook']
	list_of_files = string_of_files[0].split(',')
	files = [(x, x) for x in list_of_files]
	request = MultiCheckboxField('* Requested Support', choices=files,validators=[
			Required('Please tick one or more option')])

# classes for create table
class Kerkes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(80))
    title = db.Column(db.String(70))
    type = db.Column(db.String(70))
    venue = db.Column(db.String(60))
    date = db.Column(db.Date)
    celebrities = db.Column(db.String(80))
    brief = db.Column(db.Text())
    request = db.Column(db.String(80)) 


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
        backref=db.backref('kerkes', lazy='dynamic'))

    def __init__(self, department, title,request, type, venue, date, celebrities,brief,user_id):
        self.department = department
        self.title = title
        self.type = type
        self.venue = venue
        self.celebrities = celebrities
        self.brief = brief
        self.date = date
        self.user_id = user_id
        self.request = request
      

    def __repr__(self):
        return '<Post %r>' % self.title


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    surname = db.Column(db.String(20))
    email = db.Column(db.String(40)) 

    def __init__(self, name, surname, email):
        self.name = name
        self.surname=surname
        self.email=email

    def __repr__(self):
        return '<User %r>' % self.name
# endpoint
@app.route("/",methods=('GET', 'POST'))
def index():
	form = EasyForm()
	if form.validate_on_submit():
		checkuser = User.query.filter_by(email=form.email.data).first()
		if checkuser is None:
			user = User(
				name=form.name.data,
				surname=form.surname.data,
				email=form.email.data)
			db.session.add(user)
			db.session.flush()
			checkuser = user

		lista = form.request.data
		string =  ''.join(lista)
		convdate = datetime.strptime(form.date.data,'%Y-%d-%m')
		kerkes = Kerkes(
			department=form.department.data,
			title=form.title.data,
			type=form.type.data,
			venue=form.venue.data,
			celebrities=form.celebrities.data,
			brief=form.brief.data,
			user_id=checkuser.id,
			date=convdate,
			request=string)
		
		db.session.add(kerkes)
		return redirect(url_for('.index'))
	return render_template('form.html', form=form)

if __name__ == "__main__":
    manager.run()