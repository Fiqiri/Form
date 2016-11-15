from flask import Flask,render_template,flash,redirect,url_for,request
from flask_wtf import Form
from celery import Celery
import pdfkit
from flask_mail import Mail, Message
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

app.config['CELERY_BROKER_URL'] = 'amqp://localhost//'
    


app.config['DEBUG'] = True

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'fiqiripoleshi@gmail.com'
app.config['MAIL_PASSWORD'] = 'Argenti2015'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.config['STATICFILES_DIRS'] = os.path.join(basedir, "static")
app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'you-will-never-guess'
db = SQLAlchemy(app)
manager = Manager(app)
Bootstrap = Bootstrap(app)
celery=Celery(app)

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

# classes for create form
class EasyForm(Form):
	name = TextField('* Name', validators=[
			Required('Please enter your name'),
			Length(max=20, message=(u'Name is too long'))
			])
	surname = TextField('* Surname', validators=[
			Required('Please enter your surname:'),
			Length(max=20, message=(u'Surname is too long'))
			])
	email = TextField('* Email address', validators=[
		   Required('Please enter your email:'),
           Length(min=6, message=(u'Email address too short')),
           Length(max=50, message=(u'Email address is too long')),
           Email(message=(u'That\'s not a valid email address.'))])
	department = SelectField('* Office / Department', choices=[('', 'Select your department'), ('Rectors Office', 'Rectors Office'), ('Rectors Cabinet', 'Rectors Cabinet'),
		('AEQI', 'AEQI'), ('Research and Projects Office', 'Research and Projects Office'), ('Internatonal Relations Office', 'Internatonal Relations Office'),
		('Office of the Secretary General', 'Office of the Secretary General'), ('Finance Office', 'Finance Office')], validators=[
			Required('Your answer is required')])
	title = TextField('* Title of the activity', validators=[
			Required('Your answer is required'),
			Length(max=70, message=(u'Title is too long, maximum is 70'))
			])
	type = TextField('* Type of the activity', validators=[
			Required('Your answer is required'),
			Length(max=70, message=(u'Type is too long, maximum is 70'))
			])
	date = StringField('* Date of the activity', validators=[Required()])
	venue = TextField('* Venue of the activity', validators=[
			Required('Your answer is required'),
			Length(max=70, message=(u'Venue is too long, maximum is 70'))
			])
	celebrities = TextField('Celebrities / public figures invited', validators=[
			Length(max=70, message=(u'Celebrities is too long, maximum is 70 letters'))
			])
	brief = TextAreaField('* Brief an activity', validators=[
			Required('Your answer is required')])
	agree = BooleanField('Send me a copy of my respones')
	string_of_files = ['Poster design,Leaflet Design,Publication on facebook,Publication on facebook']
	list_of_files = string_of_files[0].split(',')
	files = [(x, x) for x in list_of_files]
	request = MultiCheckboxField('* Requested Support', choices=files,validators=[
			Required('Please tick one or more option'),
			Length(max=80, message=(u'Type is too long, maximum is 80 leter'))
			])

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
    email = db.Column(db.String(50)) 

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
		# check if user excist and add user
		checkuser = User.query.filter_by(email=form.email.data).first()
		if checkuser is None:
			user = User(
				name=form.name.data,
				surname=form.surname.data,
				email=form.email.data)
			db.session.add(user)
			db.session.flush()
			checkuser = user

		# add more details
		lista = form.request.data
		string =  ''.join(lista)
		convdate = datetime.strptime(form.date.data,'%Y-%m-%d')
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
		db.session.flush()
		getkerkes = Kerkes.query.order_by(Kerkes.id.desc()).first()
		agree = form.agree.data
		if agree is True:
			css = ['static/css/stylepdf.css']
			rendered = render_template('pdf_template.html',
			name = checkuser.name,
			surname = checkuser.surname,
			email = checkuser.email,
			venue = getkerkes.venue,
			title = getkerkes.title,
			department = getkerkes.department,
			date = getkerkes.date,
			request = getkerkes.request,
			brief = getkerkes.brief,
			img='static/images/logo.png'
			)
			pdf = pdfkit.from_string(rendered, False, css=css)
			msg = Message(getkerkes.title, sender = 'fiqiripoleshi@gmail.com', recipients = [checkuser.email])
   			msg.body = "Hello"
   			msg.attach("result.pdf","application/pdf",pdf)
   			mail.send(msg)

		return redirect(url_for('.index'))
	return render_template('form.html', form=form)
@app.route('/fiqi')
def fiqi():
	return render_template('pdf_template.html')
		
if __name__ == "__main__":
	manager.run()