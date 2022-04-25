import os
import random
from datetime import datetime

from flask import Flask, render_template, redirect, abort, request, send_file
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

from data import db_session
from data.game import Game
from data.genres import Genre
from data.users import User
from forms.change_password import ChangePasswordForm
from forms.edit_game import EditGameForm
from forms.add_game import AddGameForm
from forms.login import LoginForm
from forms.register import RegisterForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    db_sess = db_session.create_session()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register_page.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register_page.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            email=form.email.data,
            nickname=form.login.data,
            age=form.age.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect("/login")
    return render_template('register_page.html', title='Регистрация', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.email == form.email.data) | (User.nickname == form.email.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login_page.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template("login_page.html", title="Авторизация", form=form)


@app.route("/change_avatar", methods=["GET", "POST"])
@login_required
def change_avatar():
    db_sess = db_session.create_session()
    if request.method == "POST":
        file = request.files['file']
        with open(f"static/images/avatars/{current_user.nickname}.png", "wb") as file_write:
            file_write.write(file.read())
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.user_avatar = f"{current_user.nickname}.png"
        db_sess.commit()
        return redirect("/change_avatar")
    else:
        return render_template("change_avatar_page.html", title="Смена аватара")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    db_sess = db_session.create_session()
    form = ChangePasswordForm()
    if request.method == "POST":
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.password.data)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect("/personal_account")
        else:
            return render_template("change_password_page.html", title="Смена пароля", form=form,
                                   message="Неправильный пароль")
    else:
        return render_template("change_password_page.html", title="Смена пароля", form=form)


@app.route("/", methods=["GET", "POST"])
def index():
    db_sess = db_session.create_session()
    if request.method == "POST":
        author = request.form['author-search']
        title = request.form['title-search']
        games = db_sess.query(Game).filter(Game.game_name.like(f"%{title.strip()}%")).filter(
            Game.game_author.like(f"%{author.strip()}%")).all()
        return render_template("main_page.html", title="Главная страница", games=games, games_count=len(games),
                               req=f"{title} {author}")
    else:
        games = db_sess.query(Game).all()
        return render_template("main_page.html", title="Главная страница", games=games, games_count=len(games))


@app.route("/personal_account")
@login_required
def personal_account():
    db_sess = db_session.create_session()
    user_games = db_sess.query(Game).filter(Game.user_id == current_user.id).all()
    return render_template("personal_account_page.html", games=user_games, games_count=len(user_games))


@app.route("/show_game/<int:game_id>", methods=["GET", "POST"])
def show_game(game_id):
    db_sess = db_session.create_session()
    game = db_sess.query(Game).filter(Game.id == game_id).first()
    game_description = game.game_description
    l_u = game.updated_date
    image = game.image_link
    if not image or not os.path.exists(image):
        image = "static/images/skins/standard-image.jpg"
    return render_template("game_info_page.html",
                           title=game.game_name, image=image, author=game.game_author, genre=game.genre.title,
                           user_author=game.user.nickname, game_description=game_description, last_update=l_u,
                           game=game)


@app.route("/edit_game/<int:game_id>", methods=["GET", "POST"])
@login_required
def edit_game(game_id):
    form = EditGameForm()
    db_sess = db_session.create_session()
    game = db_sess.query(Game).filter(Game.id == game_id).first()
    if not game:
        abort(404, message="Такой книги не существует")
    if request.method == "POST":
        game.game_name = form.title.data
        game.game_author = form.game_author.data
        game.genre_id = form.genre.data
        game.updated_date = datetime.now()
        game.game_description = request.form['text']
        file_image = request.files['file']
        if file_image:
            image_link = f"static/images/skins/{game.game_name}-{random.randint(1, 100000)}.png"
            os.remove(game.image_link)
            with open(image_link, "wb") as file_write:
                file_write.write(file_image.read())
            game.image_link = image_link
        db_sess.commit()
        return redirect(f"/show_game/{game_id}")
    else:
        image = game.image_link
        if not image or not os.path.exists(image):
            image = "static/images/skins/standard-image.jpg"
        form.genre.choices = [(i.id, i.title) for i in db_sess.query(Genre).all()]
        form.title.data = game.game_name
        form.game_author.data = game.game_author
        form.genre.data = game.genre_id
        return render_template("edit_game_page.html", form=form, game=game, image_link=image)


@app.route("/delete_game/<int:game_id>", methods=["GET", "POST"])
@login_required
def delete_game(game_id):
    db_sess = db_session.create_session()
    game = db_sess.query(Game).filter(Game.id == game_id).first()
    if game:
        db_sess.delete(game)
        db_sess.commit()
    else:
        abort(404)
    return redirect(request.referrer)


@app.route("/add_game", methods=["GET", "POST"])
@login_required
def add_game():
    form = AddGameForm()
    db_sess = db_session.create_session()
    if request.method == "POST":
        game = Game()
        game.game_name = form.title.data
        game.game_author = form.game_author.data
        game.genre_id = form.genre.data
        game.created_date = datetime.now()
        game.updated_date = datetime.now()
        game.game_description = request.form['text']
        file_image = request.files['file']
        image_link = f"static/images/skins/{game.game_name}-{random.randint(1, 100000)}.png"
        if file_image:
            with open(image_link, "wb") as file_write:
                file_write.write(file_image.read())
            game.image_link = image_link
        else:
            game.image_link = "static/images/skins/default_image.jpg"
        current_user.games.append(game)
        db_sess.merge(current_user)
        db_sess.commit()
        last_id = [int(*i) for i in db_sess.query(Game.id).all()]
        return redirect(f"/show_game/{last_id[-1]}")
    else:
        form.genre.choices = [(i.id, i.title) for i in db_sess.query(Genre).all()]
        return render_template("add_game_page.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    db_session.global_init("db/games.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=5000)
