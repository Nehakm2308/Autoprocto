from flask import Flask, render_template, request, flash, redirect, url_for,session
from flask_mysqldb import MySQL
from flask_session import Session
from validate_email import validate_email

app= Flask(__name__)
app.config['SECRET_KEY']='finalyearproject'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PORT']=3306
app.config['MYSQL_PASSWORD']='Nehakm@1234'
app.config['MYSQL_DB']='autoproctodb'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql=MySQL(app)

app.config['SESSION_COOKIE_SAMESITE']="None"
app.config['SESSION_TYPE']='filesystem'
app.config["TEMPLATES_AUTO_RELOAD"]=True

sess=Session()
sess.init_app(app)

@app.route('/')
@app.route('/home)')
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

        isvalid=validate_email(email)
        if(isvalid):
            pass
        else:
            flash('Please enter a valid email address.',category='danger')
        if len(name)<=2 or len(name)>30:
            flash('Name must be a minimum of 2 characters and a maximum of 30 characters in length.',category='danger')
        elif len(password)<6:
            flash('Password must be a minimum of 6 characters in length.',category='danger')
        elif confirm_password != password:
            flash('Passwords do not match.',category='danger')
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

            cur=mysql.connection.cursor()
            ar=cur.execute('INSERT INTO users(name,email,password,user_type,user_image,user_login) values(%s,%s,%s,%s,%s,%s)',(dbName,dbEmail,dbPassword,dbUser_type,dbImgdata,0))
            mysql.connection.commit()
            if ar>0:
                return redirect(url_for('home_page'))
                flash("Thanks for registering! You are successfully registered!.",category='success')
            else:
                flash("Error occured!.",category='danger')
                return redirect(url_for('home_page'))
            cur.close()
            session.clear()
    return render_template('register.html')