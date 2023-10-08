"""
Routes and views for the flask application.
"""

from flask import render_template, flash, redirect, request, session, url_for, g, abort
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
from msal import ConfidentialClientApplication, SerializableTokenCache
import uuid

imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER']  + '/'

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.filter_by(user_id=current_user.id)
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        app.logger.info(f'Post created by {current_user.username}')
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.filter_by(id=id).first_or_404()
    if (post.user_id != current_user.id):
        app.logger.warning(f'User {current_user.username} does not have access to post {id}')
        abort(403)
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        app.logger.info(f'Post {id} is updated by {current_user.username}')
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    session["state"] = str(uuid.uuid4())
    auth_url = _auth_url(authority=app.config['AUTHORITY'], scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)

@app.route(Config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('home'))
    if "error" in request.args:
        app.logger.error(request.args["error"])
        return render_template("auth_error.html", result=request.args)
    if 'code' in request.args:
        tokenCache = _load_token_cache()
        authResult = _msal_app(cache=tokenCache).acquire_token_by_authorization_code(
            code=request.args['code'],
            scopes=app.config['SCOPE'] or [],
            redirect_uri=url_for('authorized', _external=True))
        if "error" in authResult:
            app.logger.error(authResult["error"])
            return render_template("auth_error.html", result=authResult)
        session["user"] = authResult.get("id_token_claims")
        username = session["user"]["name"]
        user = User.query.filter_by(username=username).first()
        if (user is None):
            app.logger.info(f'Appending new user {session["user"]["name"]}')
            user = User()
            user.username = session["user"]["name"]
            user.set_password(str(uuid.uuid4())) # Random password, this user always login by MS account
            db.session.add(user)
            db.session.commit()
            app.logger.info(f'User {session["user"]["name"]} was added to DB')
        login_user(user)          
        _save_token_cache(tokenCache)
    
    app.logger.info(f'User {user.username} logged in successfully')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    app.logger.info(f'Logging out user {current_user.username}')
    logout_user()
    if session.get("user"): # Used MS Login
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True))

    return redirect(url_for('login'))

def _load_token_cache():
    tokenCache = SerializableTokenCache()
    if session.get("token_cache"):
        tokenCache.deserialize(session["token_cache"])
    return tokenCache

def _save_token_cache(tokenCache):
    if not tokenCache.has_state_changed:
        pass
    session["token_cache"] = tokenCache.serialize()
    pass

def _msal_app(cache=None, authority=None): # Singleton
    g.msalApp = getattr(g, 'msalApp', ConfidentialClientApplication(
        app.config['CLIENT_ID'],
        authority=authority or app.config['AUTHORITY'],
        client_credential=app.config['CLIENT_SECRET']))
    return g.msalApp

def _auth_url(authority=None, scopes=None, state=None):
    return _msal_app(authority=authority).get_authorization_request_url(
        app.config['SCOPE'] or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for('authorized', _external=True))
