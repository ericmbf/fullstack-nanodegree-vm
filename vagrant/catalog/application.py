#!/usr/bin/python
from flask import Flask, render_template, request, redirect, url_for, \
    jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.event import listen
from sqlalchemy import event, DDL
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User, engine
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests
from flask_httpauth import HTTPBasicAuth
from flask_wtf.csrf import CSRFProtect, CSRFError
from functools import wraps


app = Flask(__name__)
csrf = CSRFProtect()

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = \
    json.loads(open('./client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def showLogin():
    """
        Implement anti-forgery state token and redirect to login.html page.
    Args:
    Returns:
        The login.html page to authentication.
    """
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


@app.route('/disconnect')
def disconnect():
    """
        Disconnect the user from session.
    Args:
    Returns:
        Redirect to the main page from applicaiton.
    """
    if login_session.get('username'):
        del login_session['username']
    if login_session.get('user_id'):
        del login_session['user_id']
    return redirect(url_for('latestItems'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
        Implement the google oauth2 authentication process.
    Args:
    Returns:
        Return 200 code if the authentication was successful.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Check if the acess token is valid
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


def createUser(login_session):
    """
        Create a new user to application on database
    Args:
        login_session: the session from user
    Returns:
        Return the user id created
    """
    newUser = User(username=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """
        Return the user information.
    Args:
        user_id: The user ID.
    Returns:
        Return the user model.
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """
        Return the user ID by email.
    Args:
        email: The user email.
    Returns:
        Return the user UD.
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/')
@app.route('/catalog/')
def latestItems():
    """
        Render the main page with the 5 most recently added items in catalog
        and all the categories.
    Args:
    Returns:
        Render the main page from web application.
    """
    # Get all categories
    categories = session.query(Category).all()
    # Get the recently itens added
    latest_items = \
        session.query(Item).order_by(desc(Item.id)).limit(5).all()
    login = False
    # Check if the user is logged
    if login_session.get('user_id'):
        login = True

    return render_template('latest_items.html', categories=categories,
                           latest_items=latest_items, login=login)


@app.route('/catalog/<string:category_name>/Items')
def getItemsFromCategory(category_name):
    """
        Return the 5 most recently added items in catalog.
    Args:
        email: The user email.
    Returns:
        Return the user UD.
    """
    categories = session.query(Category).all()
    category = \
        session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('items_by_category.html',
                           category_name=category_name, items=items,
                           categories=categories)


def checkItemOwner(function):
    @wraps(function)
    def wrapper(item_name):
        if login_session.get('user_id'):
            item = session.query(Item).filter_by(name=item_name).one()
            user = getUserInfo(login_session.get('user_id'))
            if item.user_id == user.id:
                return function(item_name)
        return render_template('invalid_user.html', item_name=item_name)
    return wrapper


@app.route('/catalog/<string:category_name>/<string:item_name>')
def getItem(category_name, item_name):
    """
        Render a specific item description.
    Args:
        category_name: the category_name
        item_name: the specific item
    Returns:
        Render the item_description.html page.
    """
    # Get the category
    category = \
        session.query(Category).filter_by(name=category_name).one()
    # Get the item using category ID
    item = session.query(Item).filter_by(
        category_id=category.id, name=item_name).one()
    login = False

    # Check item owner
    user = getUserInfo(login_session.get('user_id'))
    if item.user_id == user.id:
        login = True

    return render_template('item_description.html', item=item,
                           login=login)


def login_required(function):
    @wraps(function)
    def wrapper():
        if 'username' in login_session:
            return function()
        else:
            return showLogin()
    return wrapper


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def addItem():
    """
        Handle the insert of item to catalog.
    Args:
    Returns:
        Render the new_item.html page when method is GET and add the new item
        when the method is POST.
    """
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['category']).one()
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category.id,
            category=category,
            user_id=login_session['user_id'],
            user=getUserInfo(login_session['user_id']),
            )
        session.add(newItem)
        session.commit()
        return redirect(url_for('latestItems'))
    else:
        categories = session.query(Category).all()
        return render_template('new_item.html', categories=categories)


@app.route('/catalog/<string:item_name>/edit/', methods=['GET', 'POST'])
@checkItemOwner
@csrf.exempt
def editItem(item_name):
    """
        Handle the edit item from catalog.
    Args:
    Returns:
        Render the edit_item.html page when method is GET and edit item
        when the method is POST.
    """
    editItem = session.query(Item).filter_by(name=item_name).one()
    categories = session.query(Category).all()

    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['category']).one()
        editItem.name = request.form['name']
        editItem.description = request.form['description']
        editItem.category_id = category.id
        editItem.category = category
        session.add(editItem)
        session.commit()
        return redirect(url_for('latestItems'))
    else:
        return render_template('edit_item.html', item=editItem,
                               categories=categories)


@app.route('/catalog/<string:item_name>/delete/', methods=['GET', 'POST'])
@checkItemOwner
@csrf.exempt
def deleteItem(item_name):
    """
        Handle the delete item from catalog.
    Args:
    Returns:
        Render the delete_item.html page when method is GET and delete item
        when the method is POST.
    """
    deleteItem = session.query(Item).filter_by(name=item_name).one()

    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('latestItems'))
    else:
        return render_template('delete_item.html', item=deleteItem)


@app.route('/catalog/Categories.json')
def getAllCategoriesJSON():
    """
        Implement a endpoint to get all categgories from catalog
    Args:
    Returns:
        All categories in JSON format.
    """
    categoriesList = session.query(Category).all()
    return jsonify(Categories=[i.serialize for i in categoriesList])


@app.route('/catalog/<string:category_name>/Items.json')
def getItemsByCategoryJSON(category_name):
    """
        Implement a endpoint to get all item from category
    Args:
        category_name: Category name.
    Returns:
        All items from category in JSON format.
    """
    category = \
        session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()

    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<string:category_name>/<string:item_name>.json')
def getItemJSON(category_name, item_name):
    """
        Implement a endpoint to get a specific item.
    Args:
        category_name: Category name.
        item_name: item name.
    Returns:
        Return a specific item in JSON format.
    """
    category = \
        session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        category_id=category.id, name=item_name).one()

    return jsonify(Item=item.serialize)


@app.route('/catalog.json')
def getCatalogJSON():
    """
        Implement a endpoint to get all categories with all items.
    Args:
    Returns:
        Return all categories with its specifics items in JSON format.
    """
    categories = session.query(Category).all()
    categoryList = []
    for category in categories:
        itemsFromCategory = \
            session.query(Item).filter_by(category_id=category.id).all()

        categoryItem = {
            'id': category.id,
            'name': category.name,
            'Item': [item.serialize for item in itemsFromCategory]}

        categoryList.append(categoryItem)

    return jsonify(Category=categoryList)


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
        Handle csrf error.
    Args:
    Returns:
        Return a csrf error page with error description
    """
    return render_template('csrf_error.html', reason=e.description), 400


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    csrf.init_app(app)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=8000)
