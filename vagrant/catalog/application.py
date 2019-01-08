from flask import Flask, render_template, request, redirect, url_for, jsonify, \
    flash
from sqlalchemy import create_engine, desc
from sqlalchemy.event import listen
from sqlalchemy import event, DDL
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///categoryitems.db', 
    connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('')
@app.route('/catalog/')
def latestItems():
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(desc(Item.id)).limit(5).all()
    return render_template('latest_items.html', categories=categories, 
        latest_items=latest_items)

@app.route('/catalog/<string:category_name>/Items')
def getItemsFromCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('items_by_category.html',
        category_name=category_name, items=items)

# @app.route('/category/<int:category_id>/menu/new/', methods=['GET', 'POST'])
# def newMenuItem(category_id):
#     if request.method == 'POST':
#         newItem = MenuItem(
#             category_id=category_id, 
#             name=request.form['name'], 
#             description=request.form['description'], 
#             price=request.form['price'],
#             course=request.form['course'])
#         session.add(newItem)
#         session.commit()
#         flash("New Item Created")
#         return redirect(url_for('showMenu', category_id=category_id))
#     else:
#         return render_template('newMenuItem.html', category_id=category_id)

# @app.route('/category/<int:category_id>/menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
# def editMenuItem(category_id, menu_id):
#     editItem = session.query(MenuItem).filter_by(id=menu_id).one()

#     if request.method == 'POST':
#         editItem.name = request.form['name']
#         editItem.description = request.form['description']
#         editItem.price = request.form['price']
#         editItem.course = request.form['course']
#         session.add(editItem)
#         session.commit()
#         flash("Menu Item Successfully Edited")
#         return redirect(url_for('showMenu', category_id=category_id))
#     else:
#         return render_template('editMenuItem.html', category_id=category_id, 
#             menu_id=menu_id, item=editItem)
#     return "This page edit the menu item {}".format(menu_id)

# # Task 3: Create a route for deleteMenuItem function here
# @app.route('/category/<int:category_id>/menu/<int:menu_id>/delete/', methods=['GET', 'POST'])
# def deleteMenuItem(category_id, menu_id):
#     deleteItem = session.query(MenuItem).filter_by(id=menu_id).one()

#     if request.method == 'POST':
#         session.delete(deleteItem)
#         session.commit()
#         flash("Menu Item Successfully Deleted")
#         return redirect(url_for('showMenu', category_id=category_id))
#     else:
#         return render_template('deleteMenuItem.html', 
#                 category_id=category_id, menu_id=menu_id, item=deleteItem)

# @app.route('/categories/JSON')
# def categoriesJSON():
#     categories = session.query(category).all()
#     return jsonify(category=[i.serialize for i in categories])

# @app.route('/categories/<int:category_id>/menu/JSON')
# def categoryMenuJSON(category_id):
#     category = session.query(category).filter_by(id=category_id).one()
#     items = session.query(MenuItem).filter_by(
#         category_id=category.id).all()
#     return jsonify(MenuItems=[i.serialize for i in items])

# @app.route('/categories/<int:category_id>/menu/<int:menu_id>/JSON')
# def categoryMenuItemJSON(category_id, menu_id):
#     menuItem = session.query(MenuItem).filter_by(category_id=category_id, id=menu_id).one()
#     return jsonify(MenuItems=menuItem.serialize)

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=8000)