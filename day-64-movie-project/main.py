from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
import requests

# az apihoz szükséges kód és weboldal

headers = {
    "api_key": "cb5e9fc9d6dc98c1c07b5da8c10eff47",
    "query": "Inception"
}
website = "https://api.themoviedb.org/3/search/movie"

# a bootstrap es sqalchemy beagyazasa a flask be

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
db = SQLAlchemy(app)

# a szerkesztes flask form letrehozasa

class EditForm(FlaskForm):
    rating_label = StringField('A te értékelésed, pl. 7.5', [InputRequired()])
    review_label = StringField('Rövid vélemény a filmről:', [InputRequired()])
    submit = SubmitField(label='Kész')

# a hozzadas flask form letrehozasa

class AddForm(FlaskForm):
    movie_title = StringField('Film címe', [InputRequired()])
    submit = SubmitField(label='Kész')

# az sqalchemy model letrehozasa, az oszlopok neveinek meghatarozasa

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(350), nullable=False)
    rating = db.Column(db.String(10), nullable=False)
    ranking = db.Column(db.String(10), nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

# az adatbazis letrehozasa a fenti kriteriumok alapjan

db.create_all()
movies = Movie.query.all()

# db.session.add(new_movie)
db.session.commit()

# a fooldal letrehozasa
# filmek lekerdezese rating szerint rendezve
# a ranking ertek megadasa helyezes szerint, amit a rating alapjan hataroztunk meg
# a lista ujrarendezese
# a fooldal renderelese, az ujrarendezett adatbazis bevitele az index.html be, mint movies

@app.route("/")
def home():
    movies = db.session.query(Movie).order_by(Movie.rating.desc()).all()
    for i in movies:
        i.ranking = movies.index(i) + 1
    db.session.commit()
    return render_template("index.html", new_movie=movies)

# a szerkeszto oldal letrehozasa, id lekerdezes a html-bol
# szerkeszto form lekerdezese a fenti formbol
# gombnyomasra torteno parancs
# az id alapjan szurjuk az adatbazis, az alapjan az aktualis filmet szerkesztjuk
# adatbazis frissites es fooldalra atiranyitas
# nem gombnyomaskor torteno parancsok
# az aktualis film cimenek lekerdezes id alapjan
# a form es a film cimenek tovabbitasa az edit.html fele

@app.route('/edit/<string:id>', methods=["POST", "GET"])
def edit(id):
    form = EditForm()
    if form.validate_on_submit():
        book_to_update = Movie.query.filter_by(id=id).first()
        book_to_update.rating = form.rating_label.data
        book_to_update.review = form.review_label.data
        db.session.commit()
        return redirect(url_for('home'))
    this_movie = Movie.query.filter_by(id=id).first()
    return render_template("edit.html", form=form, movie=this_movie)

# a hozzadas oldal letrehozasa, form hozzaadas
# ha a formot aktivaljuk a gombnyomassal a kovetkezok tortennek
# lekerdezi a film cimet amit beirunk a formba
# az api ba bejelyettesiti es a requests el rakeres
# a talalatok listajat beviszi az add.html be es azt is hogy megtortent a bevitel
# nem gombnyomasra torteno parancs
# az add.html renderelese es a form bevitele, ami lekerdezi a film cimet

@app.route('/add', methods=["POST", "GET"])
def add():
    form = AddForm()
    if request.method == "POST":
        title = form.movie_title.data
        headers_api = {
            "api_key": "cb5e9fc9d6dc98c1c07b5da8c10eff47",
            "query": title
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie?", params=headers_api)
        result = response.json()
        movies_api = (result["results"])
        return render_template("add.html", post=True, result=movies_api)
    return render_template("add.html", form=form)

# a beerkezo filmet kezelo modul
# az id alapjan rakeres a filmre az apival
# a film adatlapjat letolti a kriteriumok alapjan
# film cime, kep, leiras, ev
# ezt beviszi az sql adatbazisba uj filmkent
# utana atiranyit a szerkeszto oldalra

@app.route('/add_movie/<string:id>', methods=["POST", "GET"])
def add_movie(id):
    headers_api = {
        "api_key": "cb5e9fc9d6dc98c1c07b5da8c10eff47",
        "language": "hu"
    }
    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{id}?", params=headers_api)
    result = response.json()
    title = (result["original_title"])
    description = (result["overview"])
    year = (result["release_date"]).split("-")[0]
    img_url = (result["poster_path"])
    first_path = "https://www.themoviedb.org/t/p/w600_and_h900_bestv2"
    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        rating=11,
        ranking=11,
        review="Good movie.",
        img_url=f"{first_path}{img_url}"
    )
    db.session.add(new_movie)
    db.session.commit()
    this_movie = Movie.query.filter_by(title=title).first()
    id_1 = this_movie.id
    return redirect(url_for('edit', id=id_1))

# torles modul
# lekerdezi a film id-t
# rakeres az adatbazisban a filmre es torli onnan
# atiranyit a fooldalra

@app.route('/delete/<string:id>')
def delete(id):
    book_id = id
    book_to_delete = Movie.query.get(book_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

# app elinditasa es a debuggolas bekapcsolasa

if __name__ == '__main__':
    app.run(debug=True)
