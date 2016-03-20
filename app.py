from flask import Flask, render_template, request, json, session, redirect
from flask.ext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash
from flask_oauth import OAuth
import datetime

GOOGLE_CLIENT_ID = '1050490126928-v2pamupbefj2fa7lktu2e89pq64vkuuo.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '1gp6ukQGvKGiG26taYJcYKWE'
REDIRECT_URI = '/oauthCallback'

SECRET_KEY = 'development key'

DEBUG = True

app = Flask(__name__)
mysql = MySQL()
app.secret_key = SECRET_KEY
app.debug = DEBUG

oauth = OAuth()

google = oauth.remote_app('gogle', 
							base_url = 'https://www.google.com/accounts/',
							authorize_url = 'https://accounts.google.com/o/oauth2/auth',
							request_token_url = None,
							request_token_params = {'scope': 'https://www.googleapis.com/auth/userinfo.email', 'response_type': 'code'},
							access_token_url = 'https://accounts.google.com/o/oauth2/token',
							access_token_method = 'POST',
							access_token_params = {'grant_type': 'authorization_code'},
							consumer_key = GOOGLE_CLIENT_ID,
							consumer_secret = GOOGLE_CLIENT_SECRET)



# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'developer'
app.config['MYSQL_DATABASE_PASSWORD'] = 'vv$tgY001'
app.config['MYSQL_DATABASE_DB'] = 'T20Predict'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route("/")
def main():
	return render_template('index.html')

@app.route("/showSignUp")
def showSignUp():
	return render_template('signup.html')

@app.route('/signUp', methods = ['POST'])
def signUp():
	try:
		_name = request.form['inputName']
		_email = request.form['inputEmail']
		_password = request.form['inputPassword']

		if _name and _email and _password:
			conn = mysql.connect()
			cursor = conn.cursor()
			_hashed_password = generate_password_hash(_password)
			cursor.callproc('sp_createUser',(_name,_email,_hashed_password))
			data = cursor.fetchall()

			if len(data) is 0:
				conn.commit()
				return json.dumps({'success': True, 'html':'Registration Successful!'})
			else:
				return json.dumps({'error':str(data[0])})
		else:
			return json.dumps({'success': False, 'html':'Enter the required fields'})
	except Exception as e:
		return json.dumps({'error':str(e)})
	finally:
		pass

@app.route('/showSignin')
def showSignin():
	return render_template('signin.html')

@app.route('/validateLogin', methods = ['POST', 'GET'])
def validateLogin():
	try:
		_username = request.form['inputEmail']
		_password = request.form['inputPassword']
		con = mysql.connect()
		cursor = con.cursor()
		cursor.callproc('sp_validateLogin',(_username,))
		data = cursor.fetchall()
		if len(data) > 0:
			if check_password_hash(str(data[0][3]), _password):
				session['user'] = data[0][0]
				return redirect('/todaysMatch')
			else:
				return render_template('signin.html', error = 'Wrong email address or password')
		else:
			return render_template('signin.html', error = "Wrong email address or password")
	except Exception, e:
		return render_template('signin.html', error = str(e))
	finally:
		cursor.close()
		con.close()

@app.route('/userHome')
def userHome():
	if session.get('user'):
		return render_template('userHome.html')
	else:
		return render_template('error.html', error = 'You are not authorized')
	return render_template('userHome.html')

@app.route('/logout')
def logout():
	session.pop('user', None)
	return redirect('/')

def getTodaysMatch():
	start = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
	end = datetime.datetime.today().replace(hour=23, minute=59, second=0, microsecond=0)
	try:
		con = mysql.connect()
		cursor = con.cursor()
		sql = "select * from matches where startdate BETWEEN '{}' and '{}';".format(start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))
		cursor.execute(sql)
		data = cursor.fetchone()
		if len(data) > 0:
			return data
	except Exception, e:
		return str(e)
	finally:
		cursor.close()
		con.close()

def getTeam(id):
	start = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
	end = datetime.datetime.today().replace(hour=23, minute=59, second=0, microsecond=0)
	try:
		con = mysql.connect()
		cursor = con.cursor()
		sql = "SELECT * FROM teams WHERE id=%d" % id
		cursor.execute(sql)
		data = cursor.fetchone()
		if len(data) > 0:
			return data
	except Exception, e:
		return None
	finally:
		cursor.close()
		con.close()

@app.route('/todaysMatch')
def todaysMatch():
	if session.get('user'):
		todayMatch = getTodaysMatch()
		team1 = getTeam(todayMatch[1])
		team2 = getTeam(todayMatch[2])
		return render_template('todays.html', team1 = team1, team2 = team2)
	else:
		return render_template('signin.html', error = 'Please Login')


if __name__ == "__main__":
	app.run()