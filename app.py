from flask import Flask, render_template, url_for, request, session, flash, redirect
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from Algorithm import resultant
from Tfidf import recommendation

#init
app = Flask(__name__)
app.secret_key = 'scibolts'
#app.permanent_session_lifetime = timedelta(days=1)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']  = False

# initializing DB
db = SQLAlchemy(app)

class Users(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200))
    movies = db.Column(db.String(200))
    
    def __init__(self, name, password, movies=" "):
        self.name = name
        self.password = password
        self.movies = movies
    
    def add_movies(self, movies):
        self.movies = ",".join(movies)
        return True

    def __repr__(self):
        print(f"{self.name} : [{self.movies}]")

#home
@app.route('/')
@app.route('/home/')
@app.route('/about/')
def home():
    return render_template('index.html')

#login
@app.route('/login/', methods=['POST', 'GET'])
def login():
    if 'user' in session:
        flash("You are already logged in!", 'info')
        return redirect(url_for('user'))
    elif request.method == 'POST':
        if request.form['name'].strip() and request.form['password'].strip():
            username = request.form['name'].strip()
            password = request.form['password'].strip()
            current_user = Users.query.filter_by(name=username).first()
            if current_user:
                if current_user.password == password:    
                    session['user'] = username
                    flash("Successful login", "success")
                    return redirect(url_for("user"))
                else:
                    flash("Please enter correct password", 'error')    
            else:
                db.session.add(Users(username, password, ""))
                db.session.commit()
                session['user'] = username
                flash("Successful Signup", 'success')
                return redirect(url_for("user"))
        else:
            flash("Please Enter valid Username, Password!", 'error')
    return render_template('login.html')

#user
@app.route('/user/', methods=['POST', 'GET'])
def user():
    if 'user' in session:
        if request.method == 'POST':
            movie = request.form['movie'].strip()
            session['movie'] = movie
            #adding movies to user record
            '''
            usr = Users.query.filter_by(name=session['user']).first()
            usr.add_movies(movie)
            db.session.commit()
            '''
            return redirect(url_for('movies'))
        return render_template('user.html', user=session['user'])
    else:
        flash("Please Login or Signup!", "error")
        return redirect(url_for('login'))

#logout
@app.route('/logout/')
def logout():
    session.pop('user')
    session.pop('movie')
    return redirect('/login/')

@app.route('/user/movies/')
@app.route('/movies/')
def movies():
    if 'user' in session:
        movies = []
        movies_tf = []
        if 'movie' in session:
            try:
                print("KNN:")
                movies = resultant(session['movie'])
                if movies:
                    print("Successfully found movies!!", movies)
                else:
                    print("No movies found!")
            except Exception:
                flash("Sorry we were not able to find that movie!", 'info')
                return redirect(url_for('user'))
            try:
                print("TFIDF:")
                movies_tf = recommendation(session['movie'])
                print("Found movies: ", movies_tf)
                movies_tf.append(session['movie'])
            except Exception as E:
                print(E)
        return render_template('recommend.html', user=session['user'], movies=movies, movies_tf=movies_tf)
    else:
        flash('Please SignUp/Login first!', 'error')
        return redirect(url_for('login'))

# running the application
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)