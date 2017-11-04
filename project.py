from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError 
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']

#Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def generateResponse(message, code):
    response = make_response(json.dumps(message), code)
    response.headers['Content-Type'] = 'application/json'
    return response

def generateAlertOutput(message):
    output = ''
    output += '<script>function alertMessage() { alert("' 
    output += message
    output += '");}</script><body onLoad="alertMessage()"></body>'
    return output

def generateLoginWelcome():
    if 'username' not in login_session or 'picture' not in login_session:
        return None
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

def getHttpResult(url):
    h = httplib2.Http()
    return h.request(url, 'GET')[1]

def createUser(login_session):
    if ('username' in login_session):
        newUser = User(name = login_session['username'],
                email = login_session['email'],
                picture = login_session['picture'])
        session.add(newUser)
        session.commit()
        user = session.query(User).filter_by(email = login_session['email']).one()
        return user.id
    return None

def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id = user_id).one()
        return user
    except:
        return None

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

#JSON APIs to view Restaurant Information
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(Menu_Item = Menu_Item.serialize)

@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants= [r.serialize for r in restaurants])


#Show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    if 'username' in login_session:
        return render_template('restaurants.html', restaurants = restaurants)
    return render_template('publicrestaurants.html', restaurants = restaurants)

#Create a new restaurant
@app.route('/restaurant/new/', methods=['GET','POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'], user_id = login_session['userId'])
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

#Edit a restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if editedRestaurant.user_id != login_session['userId']:
            return generateAlertOutput("You do not have authorization to edit this restaurant")
        elif request.form['name']:
            editedRestaurant.name = request.form['name']
            session.add(editedRestaurant)
            session.commit()
            flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('editRestaurant.html', restaurant = editedRestaurant)


#Delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    restaurantToDelete = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if restaurantToDelete.user_id != login_session['userId']:
            return generateAlertOutput("You do not have authorization to delete this restaurant")
        else:
            session.delete(restaurantToDelete)
            flash('%s Successfully Deleted' % restaurantToDelete.name)
            session.commit()
        return redirect(url_for('showRestaurants', restaurant_id = restaurant_id))
    else:
        return render_template('deleteRestaurant.html',restaurant = restaurantToDelete)

#Show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if 'username' in login_session and restaurant.user_id == login_session['userId']:
        return render_template('menu.html', items = items, restaurant = restaurant)
    return render_template('publicmenu.html', items = items, restaurant = restaurant)

#Create a new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if restaurant.user_id != login_session['userId']:
            return generateAlertOutput("You do not have authorization to add new menu item to this restaurant")
        else:
            newItem = MenuItem(name = request.form['name'], 
                    description = request.form['description'], 
                    price = request.form['price'], 
                    course = request.form['course'], 
                    restaurant_id = restaurant_id, 
                    user_id = restaurant.user_id)
            session.add(newItem)
            session.commit()
            flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id = restaurant_id)

#Edit a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedItem = session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if editedItem.user_id != login_session['userId']:
            return generateAlertOutput("You do not have authorization to edit this menu item")
        else:
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['course']:
                editedItem.course = request.form['course']
            session.add(editedItem)
            session.commit() 
            flash('Menu Item Successfully Edited')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)


#Delete a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id,menu_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id = menu_id).one() 
    if request.method == 'POST':
        if itemToDelete.user_id != login_session['userId']:
            return generateAlertOutput("You do not have authorization to delete this menu item")
        else:
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('deletemenuitem.html', item = itemToDelete)


# Login page
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)


# Google Authentication
@app.route('/gconnect', methods = ['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        return generateResponse('Invalid state parameter', 401)
    code = request.data
    try:
        oauthFlow = flow_from_clientsecrets('client_secrets.json', scope = '')
        oauthFlow.redirect_uri = 'postmessage'
        credentials = oauthFlow.step2_exchange(code)
    except FlowExchangeError:
        return generateResponse('Failed to upgrade authorization code', 401)

    accessToken = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % accessToken)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        return generateResponse(result.get('error'), 500)

    gplusId = credentials.id_token['sub']
    if result['user_id'] != gplusId:
        return generateResponse('Token\' user ID is not match user ID', 401)

    storedCredentials = login_session.get('credentials')
    storedGPlusId = login_session.get('gplusId')
    if  storedCredentials is not None and gplusId == storedGPlusId:
        return generateResponse('Current user is already connected', 200)

    login_session['credentials'] = credentials.access_token
    login_session['gplusId'] = gplusId 
    userInfoUrl = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = { 'access_token': credentials.access_token, 'alt': 'json' };

    answer = requests.get(userInfoUrl, params = params);
    data = json.loads(answer.text);
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(data['email'])
    if user_id is None:
        user_id = createUser(login_session)
    login_session['userId'] = user_id

    return generateLoginWelcome() 


@app.route('/gdisconnect')
def gdisconnect():
    accessToken = login_session.get('credentials')
    if accessToken is None:
        return generateResponse('Current user not connected', 401)

    # Revoke current token
    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % accessToken
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        return generateResponse('Successfully disconnected', 200)
    else:
        return generateResponse('Failed to revoke token for given user', 400)


@app.route('/fbconnect', methods = ['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        return generateResponse('Invalid state parameter', 401)
    accessToken = request.data
    appId = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    appSecret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s" % (appId, appSecret, accessToken)
    result = getHttpResult(url)

    token = json.loads(result)['access_token']
    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    result = getHttpResult(url)
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebookId'] = data['id']

    url = "https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200" % token
    result = getHttpResult(url)
    print "NEW RESULT"
    print result
    data = json.loads(result)
    login_session['picture'] = data['data']['url']

    user_id = getUserID(login_session['email'])
    if user_id is None:
        user_id = createUser(login_session)
    login_session['userId'] = user_id

    return generateLoginWelcome()


@app.route('/fbdisconnect')
def fbdisconnect():
    facebookId = login_session['facebookId']
    if facebookId is None:
        return generateResponse('Current user not connected', 401)
    url = "https://graph.facebook.com/%s/permissions" % facebookId 
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return generateResponse('Successfully disconnected', 200)

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['credentials']
            del login_session['gplusId']
        elif login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebookId']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['userId']
        del login_session['provider']
        flash("You have been successfully logged out")
    else:
        flash("You are not logged in to begin with")
    return redirect(url_for("showRestaurants"))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)



