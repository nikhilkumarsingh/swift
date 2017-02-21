import atexit
import logging
import time
from datetime import datetime, timedelta
import flask, flask_login
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from db_fetcher import *

# initialize flask app
app = flask.Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


#-------------------- LOGIN FUNCIONALITY ---------------------#

# initialize login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = fetch_valid_users()
    if email not in users:
        return 
    user = User()
    user.id = email
    user.name = users[email]['name']
    return user


@login_manager.request_loader
def request_loader(request):
    users = fetch_valid_users()
    email = request.form.get('email')
    if email not in users:
        return None

    user = User()
    user.id = email
    user.name = users[email]['name']
    user.is_authenticated = request.form['password'] == users[email]['pw']

    return user


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    
    if flask.request.method == 'GET':
        msg = flask.request.args.get('msg')
        if flask_login.current_user.get_id() != None:
            return flask.redirect(flask.url_for('home_page'))
        else:
            return flask.render_template('signup.html', msg = msg)

    if flask.request.method == 'POST':
        name = flask.request.form['name']
        email = flask.request.form['email']
        pw = flask.request.form['pw']

        users = fetch_valid_users()

        if name != '' and email != '' and pw != '' and email not in users:
            register_user(name, email, pw)
            users = fetch_valid_users()
            msg = "Registration successful! Please login."
            return flask.redirect(flask.url_for('login', msg = msg))
        else:
            msg = "Registration failed"
            return flask.redirect(flask.url_for('signup', msg = msg))
            
    

        
@app.route('/login', methods=['GET', 'POST'])
def login():

    error = flask.request.args.get('msg')
    
    if flask.request.method == 'GET':
        if flask_login.current_user.get_id() != None:
            return flask.redirect(flask.url_for('home_page'))
        else:
            return flask.render_template('login.html', error = error)

    email = flask.request.form['email']

    users = fetch_valid_users()

    if email not in users:
        return flask.render_template('login.html', error = "User does not exist!")

    
    if flask.request.form['pw'] != users[email]['pw']:
        return flask.render_template('login.html', error = "Wrong password!")

    user = User()
    user.id = email
    flask_login.login_user(user)
    return flask.redirect(flask.url_for('home_page'))


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('home_page'))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

#------------------------------------------------------------------------------#

@app.route('/', methods=['GET'])
def home_page():
    valid_user = False
    username = 'Guest'
    if flask_login.current_user.get_id() != None:
        valid_user = True
    return flask.render_template('index.html', valid_user = valid_user)


@app.route('/about', methods=['GET'])
def about_page():
    valid_user = False
    username = 'Guest'
    if flask_login.current_user.get_id() != None:
        valid_user = True
    return flask.render_template('about.html', valid_user = valid_user)


@app.route('/flights', methods=['GET', 'POST'])
@flask_login.login_required
def journey_planner():

    locations_1 = [{'id':'none', 'name':'From'}] + fetch_locations()
    locations_2 = [{'id':'none', 'name':'To'}] + locations_1[1:]
    
    dates = ['Date'] + [str((datetime.now() + timedelta(hours = 24*i)).date()) for i in range(3)]

    companies = [{'id':'none', 'name':'Company'}] + fetch_companies()
    
    if flask.request.method == 'GET':
        defaults = ['none', 'none', 'Date', 'none']
        return flask.render_template('flights.html', locations_1 = locations_1,
                                     locations_2 = locations_2, defaults = defaults,
                                     dates = dates, companies = companies, rows = None)

    if flask.request.method == 'POST':
        orig_id = flask.request.form['orig']
        dest_id = flask.request.form['dest']
        dept_date = flask.request.form['date']
        company_id = flask.request.form['company']

        if orig_id != 'none':
            orig_id = int(orig_id)
        if dest_id != 'none':
            dest_id = int(dest_id)
        if company_id != 'none':
            company_id = int(company_id)
            
        defaults = [orig_id, dest_id, dept_date, company_id]

        
        headers = ["Flight ID", "Route", "Company", "Departure", "Arrival",
                   "Economy class<br/>Booked/Capacity", "Economy fare",
                   "Business class<br/>Booked/Capacity", "Business fare"]
        
        rows = fetch_flights(orig_id, dest_id, dept_date, company_id)
        
        return flask.render_template('flights.html', locations_1 = locations_1,
                                     locations_2 = locations_2,defaults = defaults,
                                     dates = dates, companies = companies, headers = headers,
                                     rows = rows)


      
@app.route('/flight/<int:flight_id>/', methods=['GET', 'POST'])
@flask_login.login_required
def flight_info(flight_id):

    headers = ["Flight ID", "Route", "Company", "Departure", "Arrival",
               "Economy class<br/>Booked/Capacity", "Economy fare",
               "Business class<br/>Booked/Capacity", "Business fare", "Status"]

    flight = fetch_flights(None, None, None, None, flight_id)

    if flask.request.method == 'GET':
        return flask.render_template('flight_info.html', headers = headers,
                                     flight = flight)

    if flask.request.method == 'POST':
        flight_type = flask.request.form['type']
        email = flask_login.current_user.id
        btime = datetime.now()
        if flight_type == 'eco':
            price = flight[0][6][4:]
        else:
            price = flight[0][8][4:]

        commit_booking(flight_id, email, btime, flight_type, price)

        msg = "Success!<br/>Booking confirmed!"
        
        return flask.render_template("information.html", msg = msg)




@app.route('/cancel/<int:booking_id>/', methods=['GET'])
@flask_login.login_required
def cancel_flight(booking_id):

    email = flask_login.current_user.id
    result = cancel_booking(email, booking_id)

    if result == -1:
        msg = "Sorry, booking not found or you are not authorized to cancel this booking!"
    elif result == 0:
        msg = "Sorry, booking can't be cancelled as flight has already departed!"
    else:
        msg = "Booking successfully cancelled!"

    return flask.render_template("information.html", msg = msg)

    

    
@app.route('/profile', methods=['GET'])
@flask_login.login_required
def user_profile():
    
    headers = ["Booking ID", "Flight ID", "Booking time",
               "Flight type", "Fare", "Cancel"]

    email = flask_login.current_user.id
    bookings = fetch_bookings(email)

    return flask.render_template("profile.html", bookings = bookings,
                                 headers = headers)
    

    
#--------------------- Update flights data -------------------#
#logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.start()

scheduler.add_job(
    func = update_flights,
    trigger = IntervalTrigger(hours=1),
    id = 'flight_updation',
    name = 'Update existing flights',
    replace_existing = False
    )

atexit.register(lambda: scheduler.shutdown())
#-------------------------------------------------------------#


if __name__ == '__main__':
    app.run(debug = True, port = 5050)
