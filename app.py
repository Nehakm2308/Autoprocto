from flask import Flask, render_template, request, flash, redirect, url_for,session
from flask_mysqldb import MySQL
'''from flask_session import Session
from flask_cors import CORS, cross_origin'''
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DateTimeField, SubmitField, BooleanField, IntegerField, DecimalField, HiddenField, SelectField, RadioField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from functools import wraps
from validate_email import validate_email
from flask_mail import Mail, Message
from deepface import DeepFace
from datetime import timedelta, datetime
from wtforms_components import TimeField
from wtforms.fields import DateField
from wtforms.validators import ValidationError, NumberRange
import numpy as np
import base64
import cv2
import math,random

app= Flask(__name__)
app.config["SECRET_KEY"]='O6vJwUAjrgAMB8Nm5v1KMg'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PORT']=3306
app.config['MYSQL_PASSWORD']='Nehakm@1234'
app.config['MYSQL_DB']='autoproctodb'
app.config['MYSQL_CURSORCLASS']='DictCursor'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='autoprocto11@gmail.com'
app.config['MAIL_PASSWORD']='xeumuwxpjagiwsdt'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True


mysql=MySQL(app)
mail=Mail(app)

sender='autoprocto11@gmail.com'

'''app.config['SESSION_COOKIE_SAMESITE']="None"
app.config['SESSION_TYPE']='filesystem'
app.config["TEMPLATES_AUTO_RELOAD"]=True

app.permanent_session_lifetime = timedelta(days=365)

sess=Session()
sess.init_app(app)

cors=CORS(app, supports_credentials=True)
app.config['CORS_HEADERS']='Content-Type'

sesOTPfp=1
seslpemail=''

@app.before_request
def make_session_permanent():
    session.permanent=True'''

def user_role_professor(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			if session['user_role']=="teacher":
				return f(*args, **kwargs)
			else:
				flash('You dont have privilege to access this page!','danger')
				return render_template("404.html") 
		else:
			flash('Unauthorized, Please login!','danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['confirm_password']
        user_type=request.form['user_type']
        imgdata=request.form['image_hidden']

        cur=mysql.connection.cursor()

        isvalid=validate_email(email)
        if(not isvalid):
            flash('Please enter a valid email address.',category='danger')   
        elif len(name)<=2 or len(name)>30:
            flash('Name must be a minimum of 2 characters and a maximum of 30 characters in length.',category='danger')
        elif len(password)<6:
            flash('Password must be a minimum of 6 characters in length.',category='danger')
        elif confirm_password != password:
            flash('Passwords do not match.',category='danger')
        elif(cur.execute('SELECT email from users where  email=%s',(email,))):
            flash('User with this email already exists!.',category='danger')
        else:
            session['tempName']=name
            session['tempEmail']=email
            session['tempPassword']=password
            session['tempUT']=user_type
            session['tempImage']=imgdata

            dbName=session['tempName']
            dbEmail=session['tempEmail']
            dbPassword=session['tempPassword']
            dbUser_type=session['tempUT']
            dbImgdata=session['tempImage']

            ar=cur.execute('INSERT INTO users(name,email,password,user_type,user_image,user_login) values(%s,%s,%s,%s,%s,%s)',(dbName,dbEmail,dbPassword,dbUser_type,dbImgdata,0))
            mysql.connection.commit()
            if ar > 0:
                flash("Thanks for registering! You are successfully registered!.",category='success')
                return render_template('home.html')
            else:
                flash("Error occured!.",category='danger')
                return redirect(url_for('home_page'))
            cur.close()
            session.clear()
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password_candidate=request.form['password']
        user_type=request.form['user_type']
        imgdata1=request.form['image_hidden']
        cur=mysql.connection.cursor()
        results1=cur.execute('SELECT uid,name,email,password,user_type,user_image from users where email=%s and user_type=%s and user_login=0',(email,user_type))
        if results1>0:
            cresults=cur.fetchone()
            imgdata2=cresults['user_image']
            password=cresults['password']
            name=cresults['name']
            uid=cresults['uid']
            nparr1=np.frombuffer(base64.b64decode(imgdata1),np.uint8)
            nparr2=np.frombuffer(base64.b64decode(imgdata2),np.uint8)
            image1=cv2.imdecode(nparr1, cv2.COLOR_BGR2GRAY)
            image2=cv2.imdecode(nparr2, cv2.COLOR_BGR2GRAY)
            img_result=DeepFace.verify(image1,image2,enforce_detection=False)
            if img_result["verified"]==True and password==password_candidate:
                results2=cur.execute('UPDATE users set user_login=1 where email = %s',(email,))
                mysql.connection.commit()
                if results2>0:
                    session['logged_in']=True
                    session['email']=email
                    session['name']=name
                    session['user_role']=user_type
                    session['uid']=uid
                    if user_type=="student":
                        flash('Logged in successfully as student',category='success')
                        return redirect(url_for('home_page'))
                    else:
                        flash('Logged in successfully as professor',category='success')
                        return redirect(url_for('professor_dashboard'))
                else:
                    flash('Error occured',category='danger')
            else:
                flash('Either image not verified or invalid password!,',category='danger')
            cur.close()
        else:
            flash('Already login or email was not found!.',category='danger')
    return render_template('login.html')

def generateOTP():
    digits="0123456789"
    OTP=""
    for i in range(5):
        OTP+=digits[math.floor(random.random()*10)]
    return OTP

@app.route('/lostpassword',methods=['GET','POST'])
def lostpassword():
    if request.method=='POST':
        lpemail=request.form['lpemail']
        cur=mysql.connection.cursor()
        results=cur.execute('SELECT * from users where email =%s',(lpemail,))
        if results>0:
            sesOTPfp=generateOTP()
            session['tempOTPfp']=sesOTPfp
            session['seslpemail']=lpemail
            msg1=Message('Autoprocto - OTP Verification for Lost password',sender=sender, recipients=[lpemail])
            msg1.body="Your OTP Verification code for reset password is "+sesOTPfp+"."
            mail.send(msg1)
            flash('Please check your email for OTP!',category="info")
            return redirect(url_for('verifyOTPfp'))
        else:
            flash("Account not found!",category='danger')
    return render_template('lostpassword.html')

@app.route('/verifyOTPfp',methods=['GET','POST'])
def verifyOTPfp():
    if request.method=='POST':
        fpOTP=request.form['fpotp']
        fpsOTP=session['tempOTPfp']
        if(fpOTP==fpsOTP):
            return redirect(url_for('lpnewpwd'))
        else:
            flash('The OTP entered does not match!',category='danger')
    return render_template('verifyOTPfp.html')

@app.route('/lpnewpwd',methods=['GET','POST'])
def lpnewpwd():
    if request.method=='POST':
        npwd=request.form['npwd']
        cpwd=request.form['cpwd']
        slpemail=session['seslpemail']
        if(npwd==cpwd ):
            cur=mysql.connection.cursor()
            cur.execute('UPDATE users set password = %s where email = %s', (npwd, slpemail))
            mysql.connection.commit()
            cur.close()
            session.clear()
            flash('Your password was successfully reset',category='success')
            return render_template('login.html')
        else:
            flash("Passwords do not match",category='danger')
    return render_template('lpnewpwd.html')

@app.route('/professor_dashboard')
def professor_dashboard():
    return render_template('professor_dashboard.html')

@app.route('/logout', methods=["GET", "POST"])
def logout():
    print(session)
    cur=mysql.connection.cursor()
    #lbr = cur.execute('UPDATE users set user_login = 0 where email = %s and uid = %s',(session['email'],session['uid']))
    lbr=cur.execute('UPDATE users set user_login =0 where email = "nehakm619@gmail.com"')
    mysql.connection.commit()
    print(lbr)
    if lbr > 0:
        session.pop("user",None)
        return redirect(url_for('home_page'))
    else:
        return "error"

@app.route('/subjective')
def subjective():
    form=UploadForm()
    return render_template('subjective.html',form=form)

class UploadForm(FlaskForm):
	subject = StringField('Subject :')
	topic = StringField('Topic :')
	doc = FileField('PDF Upload :', validators=[FileRequired()])
	start_date = DateField('Start Date :')
	start_time = TimeField('Start Time :', default=datetime.utcnow()+timedelta(hours=5.5))
	end_date = DateField('End Date :')
	end_time = TimeField('End Time :', default=datetime.utcnow()+timedelta(hours=5.5))
	duration = IntegerField('Duration(in min) :')
	examid = IntegerField('Exam ID :',default=generateOTP())
	submit = SubmitField('Create Exam ')

    
