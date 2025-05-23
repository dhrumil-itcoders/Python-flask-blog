from flask import Flask , render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import pymysql
pymysql.install_as_MySQLdb()
from datetime import datetime 
from werkzeug.utils import secure_filename
import json
import math
import os

local_server = True
with open('config.json' , 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key='admin_login'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL= True,
    MAIL_USERNAME=params['gmail_username'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)

class Contect(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80) , nullable = False)
    email = db.Column(db.String(20) , nullable = False)
    phone_num = db.Column(db.String(12), nullable = False)
    msg = db.Column(db.String(120) , nullable = False)
    date = db.Column(db.DateTime)

class Postss(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80) , nullable = False)
    tagline = db.Column(db.String(80) , nullable = False)
    slug = db.Column(db.String(30) , nullable = False)
    content = db.Column(db.String(120), nullable = False)
    img_file = db.Column(db.String(120), nullable = True)
    date = db.Column(db.DateTime)

@app.route('/')
def home():
    posts = Postss.query.filter_by().all() 
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int (page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('index.html',params=params,posts=posts,prev=prev, next=next)

@app.route('/about')
def about():
    return render_template('about.html',params=params)


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if('user' in session and session['user'] == params['admin_user']):
        Posts = Postss.query.all()
        return render_template('dashboard.html',params=params,posts=Posts)
    
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pwd')
        if(username == params['admin_user'] and password == params['admin_password']):
            session['user'] = username
            Posts = Postss.query.all()
            return render_template('dashboard.html',params=params,posts=Posts)
        
    return render_template('login.html',params=params)

@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content= request.form.get('content')
            img_file= request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Postss(title=box_title,tagline=tagline ,slug=slug,content=content, img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Postss.query.filter_by(sno=sno).first()
                post.title=box_title
                post.tagline=tagline
                post.slug=slug
                post.content=content
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Postss.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post)

@app.route('/post/<string:post_slug>', methods=['GET'])
def post(post_slug):
    post = Postss.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params, post=post)

@app.route('/upload_img',methods = ['GET','POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_user']):
        if(request.method=='POST'):
            f = request.files['fupload']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Sucessfully"
        
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/delete/<string:sno>' ,methods = ['GET','POST'])
def delete(sno):
        if('user' in session and session['user'] == params['admin_user']):
            post = Postss.query.filter_by(sno=sno).first()
            db.session.delete(post)
            db.session.commit()
            return redirect('/dashboard')

@app.route('/contact',methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        name= request.form.get('name')
        email= request.form.get('email')
        phone_num= request.form.get('phone_num')
        msg= request.form.get('msg')
        entry = Contect(name=name ,email=email, phone_num=phone_num,msg=msg,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From ' + name, 
                        sender=email,
                        recipients = [params['gmail_username']],
                        body = msg + "\n" + phone_num
                        )
    return render_template('contact.html',params=params)


if __name__ == '__main__':
    app.run(debug=True)
