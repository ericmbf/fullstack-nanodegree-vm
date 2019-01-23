#!/usr/bin/python
from flask import Flask, render_template, request, redirect, url_for, \
    jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.event import listen
from sqlalchemy import event, DDL
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
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

app = Flask(__name__)

engine = create_engine('sqlite:///categoryitems.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = \
    json.loads(open('./client_secrets.json', 'r').read())['web']['client_id']

# Implement anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/disconnect')
def disconnect():
    del login_session['username']
    del login_session['user_id']
    return redirect(url_for('latestItems'))


@app.route('/gconnect', methods=['POST'])
def gconnect():

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
        print "Token's client ID does not match app's."
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

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


def createUser(login_session):
    newUser = User(username=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/')
@app.route('/catalog/')
def latestItems():
    categories = session.query(Category).all()
    latest_items = \
        session.query(Item).order_by(desc(Item.id)).limit(5).all()
    login = False

    if login_session.get('user_id'):
        login = True

    return render_template('latest_items.html', categories=categories,
                           latest_items=latest_items, login=login)


@app.route('/catalog/<string:category_name>/Items')
def getItemsFromCategory(category_name):
    categories = session.query(Category).all()
    category = \
        session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('items_by_category.html',
                           category_name=category_name, items=items,
                           categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def getItem(category_name, item_name):
    category = \
        session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        category_id=category.id, name=item_name).one()
    login = False

    if login_session.get('user_id'):
        login = True

    return render_template('item_description.html', item=item,
                           login=login)


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect('/login')
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
def editItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')
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
def deleteItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = session.query(Item).filter_by(name=item_name).one()

    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('latestItems'))
    else:
        return render_template('delete_item.html', item=deleteItem)


@app.route('/catalog.json')
def getItemsByCategoryJSON():
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


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=8000)
