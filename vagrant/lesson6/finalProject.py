from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}

@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    # return "This page show all my restaurants"
    return render_template('restaurants.html', restaurants=restaurants)

@app.route('/restaurant/new')
def newRestaurant():
    # return "New Restaurant page"
    return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit')
def editRestaurant(restaurant_id):
    # return "Edit Restaurant {}".format(restaurant_id)
    restaurant = restaurants[restaurant_id - 1]
    return render_template('editRestaurant.html', restaurant=restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete')
def deleteRestaurant(restaurant_id):
    restaurant = restaurants[restaurant_id - 1]
    return render_template('deleteRestaurant.html', restaurant=restaurant)

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    # restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    # return render_template('menu.html', restaurant=restaurant, items=items)
    # return "This page show the menu from restaurant {}".format(restaurant_id)
    return render_template('menu.html', restaurant=restaurants[restaurant_id - 1], 
        items=items)

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    # if request.method == 'POST':
    #     newItem = MenuItem(
    #         name=request.form['name'], restaurant_id=restaurant_id)
    #     session.add(newItem)
    #     session.commit()
    #     flash("New item added!")
    #     return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    # else:
    #     return render_template('newMenuItem.html', restaurant_id=restaurant_id)
    # return "This page is making a new menu item for restaurant {}".format(restaurant_id)
    return render_template('newMenuItem.html', restaurant_id=restaurant_id)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    # editItem = session.query(MenuItem).filter_by(id=menu_id).one()

    # if request.method == 'POST':
    #     editItem.name = request.form['name']
    #     session.add(editItem)
    #     session.commit()
    #     flash("{} is the new name!".format(editItem.name))
    #     return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    # else:
    #     return render_template('editMenuItem.html', restaurant_id=restaurant_id, 
    #         menu_id=menu_id, i=editItem)
    # return "This page edit the menu item {}".format(menu_id)
    return render_template('editMenuItem.html', restaurant_id=restaurant_id, 
        menu_id=menu_id, restaurant=restaurant)

# Task 3: Create a route for deleteMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    # deleteItem = session.query(MenuItem).filter_by(id=menu_id).one()

    # if request.method == 'POST':
    #     session.delete(deleteItem)
    #     session.commit()
    #     flash("{} was deleted!".format(deleteItem.name))
    #     return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    # else:
    #     return render_template('deleteMenuItem.html', item=deleteItem)
    # return "This page delete the menu item {}".format(menu_id)
    return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, 
        menu_id=menu_id, item=items[menu_id - 1])

# @app.route('/restaurants/<int:restaurant_id>/menu/JSON')
# def restaurantMenuJSON(restaurant_id):
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     items = session.query(MenuItem).filter_by(
#         restaurant_id=restaurant.id).all()
#     return jsonify(MenuItems=[i.serialize for i in items])


# # ADD JSON API ENDPOINT HERE
# @app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
# def restaurantMenuItemJSON(restaurant_id, menu_id):
#     menuItem = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()
#     return jsonify(MenuItems=menuItem.serialize)

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)