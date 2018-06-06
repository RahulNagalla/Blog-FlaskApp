from flask import Flask,render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL

from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from wtforms.validators import DataRequired,Regexp,Length,Email,EqualTo
from passlib.hash import sha256_crypt
from functools import wraps
app = Flask(__name__)

#Configure MySQL
app.config['MYSQL_HOST']= 'localhost'
app.config['MYSQL_USER']= 'root'
app.config['MYSQL_PASSWORD']= ''
app.config['MYSQL_DB']= 'myflaskapp'
app.config['MYSQL_CURSORCLASS']= 'DictCursor'

#init MYSQL
mysql = MySQL(app)





#Index

@app.route('/')
def home():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')


#Articles
@app.route('/articles')
def articles():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles");
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html',articles=articles)
    else:
        msg="No Articles Found"
        return render_template('articles.html',msg=msg)
    cur.close()



#Single Article
@app.route('/article/<string:id>/')
def article(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id]);
    article = cur.fetchone()
    cur.close()
    return render_template('article.html',article=article)


#RegisteForm Class
class RegisterForm(Form):
    name=StringField('Name', validators=[validators.DataRequired(),validators.Length(min=1,max=50)])
    username=StringField('Username',validators=[validators.DataRequired(),validators.Length(min=4,max=50)])
    email=StringField('Email',validators=[validators.DataRequired(),validators.Length(min=6,max=50)])
    password = PasswordField('Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password',validators=[validators.DataRequired()])


#Register

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method== 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username= form.username.data
        password= sha256_crypt.encrypt(str(form.password.data))

        #create Cursor
        cur =mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)",(name,email,username,password))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are registered successfully and you can login now', 'success')

        return redirect(url_for('home'))
        return render_template('register.html')
    return render_template('register.html',form=form)


#Login

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']


        cur=mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username =%s",[username])

        if result>0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate,password):
                #sessions
                session['logged_in']=True
                session['username']=username

                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                # app.logger.info('PASSWORD NOT MATCHED')
                error='Invalid Login'
                return render_template('login.html',error=error)
            cur.close()
        else:
            # app.logger.info('No User')
            error='Username not found'
            return render_template('login.html',error=error)

    return render_template('login.html')

#Check if user loggedin
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized,Please Login','danger')
            return redirect(url_for('login'))

    return wrap



#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logget out','success')
    return redirect(url_for('login'))


#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles");
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg="No Articles Found"
        return render_template('dashboard.html',msg=msg)
    cur.close()
    # return render_template('dashboard.html')

#Article form class
class ArticleForm(Form):
    title=StringField('Title', validators=[validators.DataRequired(),validators.Length(min=1,max=200)])
    body=StringField('Body',validators=[validators.DataRequired(),validators.Length(min=30)])

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title =form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))
        mysql.connection.commit()
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True);
