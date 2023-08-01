from authlib.integrations.flask_client import OAuth
from flask import Flask, abort, redirect, render_template, session, url_for,request,flash
from src.logger import logging
from src.utils import sqli_connect
import http.client
import json

app = Flask(__name__)

appConf = {
    "OAUTH2_CLIENT_ID": "YOUR CLIENT ID",
    "OAUTH2_CLIENT_SECRET": "YOUR CLIENT SECRET",
    "OAUTH2_META_URL": "https://accounts.google.com/.well-known/openid-configuration",
    "FLASK_SECRET": "ALongRandomlyGeneratedString",
    "FLASK_PORT": 5000
}

app.secret_key = appConf.get("FLASK_SECRET")
oauth = OAuth(app)

oauth.register(
    "myApp",
    client_id=appConf.get("OAUTH2_CLIENT_ID"),
    client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email https://www.googleapis.com/auth/user.birthday.read https://www.googleapis.com/auth/user.gender.read",
    },
    server_metadata_url=f'{appConf.get("OAUTH2_META_URL")}',
)

#==================== home =============================================
@app.route("/")
def home():
    return render_template("base.html", session=session.get("user"))

#=================== google sign-in ====================================
@app.route("/sign-in-google")
def googleCallback():
    # fetch access token and id token using authorization code
    token = oauth.myApp.authorize_access_token()
    session["user"] = token
    return redirect(url_for("choice_page"))


@app.route("/google-login")
def googleLogin():
    if "user" in session:
        abort(404)
    return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True))


@app.route("/logout")
def logout():
    session.pop("user", None)
    # return redirect(url_for("home"))
    return render_template('base.html',session=session.get("user"),user_data='')

#===================== recruitment-details =========================================
@app.route('/choice')
def choice_page():
    return render_template('choice.html')

@app.route('/recruit',methods=['GET','POST'])
def recruit_details():
    if request.method == 'GET':
        return render_template('recruit.html')
    else:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        title = request.form.get('title')
        company_name = request.form.get('company_name')
        company_address = request.form.get('company_address')
        company_website = request.form.get('company_website')
        phone = request.form.get('phone')
        email = request.form.get('email')
    
    conn = sqli_connect('coursify')
    cursor = conn.cursor()     
    query = "INSERT INTO recruiter101 (firstName,lastName,title,companyName,companyAddress,companySite,phone,email) VALUES('{fn}','{ln}','{t}','{cn}','{ca}','{cw}','{p}','{e}');".format(fn=first_name,ln=last_name,t=title,cn=company_name,ca=company_address,cw=company_website,p=phone,e=email)
    try:
        cursor.execute(query)
        conn.commit()
        conn.close()
        flash("Noted! Go to Next page")
        return render_template('recruit.html')
    except Exception as e:
        flash("Invalid details check properly")
        logging.info(f"{e}") 
        return render_template('recruit.html')
    


@app.route('/recruit_2',methods=['GET','POST'])
def recruit_details_2():
    if request.method == 'GET':
        return render_template('recruit_2.html')
    else:
        role = request.form.get('role')
        area = request.form.get('area')
        instagram = request.form.get('instagram')
        linkedin = request.form.get('linkedin')
        check = request.form.get('check')
        confirm_email = request.form.get('confirm_email')
    conn = sqli_connect('coursify')
    cursor = conn.cursor()     
    query = "UPDATE recruiter101 SET role = '{r}', description = '{d}', instagram = '{i}', linkedin = '{l}', received = '{c}' WHERE email = '{ce}';".format(r=role,d=area,i=instagram,l=linkedin,c=check,ce=confirm_email)
    try:
        cursor.execute(query)
        conn.commit()
        conn.close()
        flash("Submitted successfully")
        return render_template('recruit_end.html')
    except Exception as e:
        flash("Invalid details check properly")
        logging.info(f"{e}") 
        return render_template('recruit_2.html')

@app.route('/student',methods=['GET','POST'])
def student_details():
    if request.method == 'GET':
        return render_template('student.html')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        country = request.form.get('country')
        category = request.form.get('field')
        title = request.form.get('job_title')
        gender = request.form.get('gender')
    conn = sqli_connect('coursify')
    cursor = conn.cursor()     
    query = "INSERT INTO student101 VALUES('{n}','{e}','{p}','{c}','{ca}','{t}','{g}');".format(n=name,e=email,p=phone,c=country,ca=category,t=title,g=gender)
    try:
        # api calling and recommendation
        host = 'jooble.org'
        key = 'YOUR API KEY'

        connection = http.client.HTTPConnection(host)
        headers = {"Content-type": "application/json"}
        body = str({ "keywords": str(category).lower() , "location": str(country).lower()})
        connection.request('POST','/api/' + key, body, headers)
        response = connection.getresponse()
        data = response.read()
        json_string = data.decode('utf-8')
        data_dict = json.loads(json_string)

        cursor.execute(query)
        conn.commit()
        conn.close()
        
        flash("Recommending....")
        return render_template('role_recommend.html',data = data_dict['jobs'])
    except Exception as e:
        flash("Invalid details check properly")
        logging.info(f"{e}") 
        return render_template('student.html') 


@app.route('/role')
def recommend():
    return render_template('role_recommend.html')


#====================== login-register==============================================
@app.route('/login',methods=['GET','POST'])
def login():
    name=''
    password=''
    if request.method == 'GET':
        return redirect(url_for('login_register'))
    else:
        name = request.form.get('name')
        password = request.form.get('password')
    conn = sqli_connect('coursify')
    cursor = conn.cursor()
    query = "SELECT username, password from user101 where username='{usrname}' and password='{pswd}';".format(usrname=name,pswd=password)
    rows = cursor.execute(query)
    rows = rows.fetchall()
    if len(rows) == 1:
        flash(f"Hi {name}, welcome")
        return render_template('choice.html',user_data=name)
    else:
        message_alert = "Invalid username and password"
        flash(message_alert)
        return render_template('log_register.html')    

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('log_register.html')  
    else:
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password') 

    conn = sqli_connect('coursify')
    cursor = conn.cursor()     
    query = "INSERT INTO user101 VALUES('{u}','{e}','{p}');".format(u=username,e=email,p=password)
    try:
        cursor.execute(query)
        conn.commit()
        conn.close()
        flash("Registered Successfully Go to Login!")
        return render_template('log_register.html')
    except Exception as e:
        flash("User already exist")
        logging.info(f"{e}") 
        return render_template('log_register.html') 



@app.route('/login-register')
def login_register():
    return render_template('log_register.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=appConf.get(
        "FLASK_PORT"), debug=True)