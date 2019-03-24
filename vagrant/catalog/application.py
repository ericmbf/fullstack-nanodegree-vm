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
from google.oauth2 import id_token
from google.auth.transport import requests
from flask import session
from flask_session.__init__ import Session

app = Flask(__name__)
sess = Session()
csrf = CSRFProtect()

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = \
    json.loads(open('/var/www/fullstack-nanodegree-vm/vagrant/catalog/client_secrets.json', 'r').read())['web']['client_id']


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

    token = request.args.get('id_token')

    try:
        data = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
    except:
        response = make_response(
            json.dumps('Invalid oauth authentication.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Specify the CLIENT_ID of the app that accesses the backend:
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    return json.dumps({'success': true}), 200, {
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
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    sess.init_app(app)
    csrf.init_app(app)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=8000)
