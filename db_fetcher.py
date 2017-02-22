import os, random
import sqlite3
from datetime import datetime, timedelta

num_cities = 5
num_companies = 2
num_routes = num_cities*(num_cities - 1)
num_flights = 4*num_routes*num_companies

distances = [[0, 1500, 1700, 1400, 1200],
             [1500, 0, 800, 1350, 600],
             [1700, 800, 0, 550, 400],
             [1400,1350, 550, 0, 1200],
             [1200, 600, 400, 1200, 0]]


def fill_routes():
    # fill route table initially with dummy values
    for x in range(num_cities):
        for y in range(num_cities):
            if x == y:
                continue
            c.execute("Insert into route (from_id, to_id, distance) values(%s, %s, %s)"%(x+1, y+1, distances[x][y]))
            conn.commit()


def fill_flights():
    # fill flights table with dummy values
    hours = [0, 3, 6, 9, 12, 15, 18, 21]
    eco_prices = [2000, 2400, 3500, 2750, 1500]
    bus_prices = [4000, 5500, 7500, 6000, 4500]
    eco_seats = [20, 30, 40, 50, 60]
    bus_seats = [10, 20, 25, 30, 35]


    dtimes = []

    today = datetime.now()

    for x in range(2*num_flights):
        dtimes.append(datetime.strptime("%s-%s-%s %s:00:00"%(today.year, today.month, today.day, hours[random.randint(0,7)]),"%Y-%m-%d %H:%M:%S"))

    today += timedelta(hours = 24)

    for x in range(2*num_flights):
        dtimes.append(datetime.strptime("%s-%s-%s %s:00:00"%(today.year, today.month, today.day, hours[random.randint(0,7)]),"%Y-%m-%d %H:%M:%S"))

    atimes = [t + timedelta(hours=2) for t in dtimes]


    i = 0
    for _ in range(4):
        for x in range(num_routes):
            for y in range(num_companies):
                c.execute("insert into flight values(?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)",
                          (i+1, x+1, y+1, eco_prices[random.randint(0, 4)], bus_prices[random.randint(0,4)],
                           eco_seats[random.randint(0, 4)], bus_seats[random.randint(0,4)],
                           str(dtimes[i].date()), str(dtimes[i].time()), str(atimes[i].date()), str(atimes[i].time())))
                conn.commit()
                i+=1


def init_db():
    # create db from pre-defined schema
    with open('./schema.sql', 'r') as f:
        c.executescript(f.read())
    conn.commit()


def register_user(name, email, pw):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    # insert user in passenger table
    c.execute("insert into passenger (name, pw_hash, email) values(?,?,?)", (name, pw, email))
    conn.commit()



def update_flights():
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    # fetch all current flights
    c.execute("select * from flight")
    flights = c.fetchall()


    # fetch total number of flights
    c.execute("select count(*) from flight")
    num_flights = c.fetchall()[0][0]
    c.execute("select count(*) from old_flight")
    num_flights += c.fetchall()[0][0]

    t = datetime.now()

    # checking departure time of each flight
    for flight in flights:
        dept  = flight[-4] + ' ' + flight[-3]
        dept = datetime.strptime(dept, "%Y-%m-%d %H:%M:%S")
        arr = flight[-2] + ' ' + flight[-1]
        arr = datetime.strptime(arr, "%Y-%m-%d %H:%M:%S")

        # move flight to old flight if departure time has passed
        if t > dept:

            # insertion into old flights
            c.execute("insert into old_flight values(?,?,?,?,?,?,?,?,?,?,?,?,?)", flight)
            conn.commit()

            # deletion from current flights
            c.execute("delete from flight where f_id = ?", (flight[0],))
            conn.commit()

            num_flights += 1
            flight_id = num_flights
            dept += timedelta(hours = 24)
            arr += timedelta(hours = 24)
            flight = list(flight)
            flight[0], flight[-4], flight[-3], flight[-2], flight[-1] = flight_id, str(dept.date()), str(dept.time()), str(arr.date()), str(arr.time())

            # new flight insertion
            c.execute("insert into flight values(?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(flight))
            conn.commit()


def fetch_valid_users():
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select email, pw_hash, name from passenger")
    rows = c.fetchall()
    users = {}
    for row in rows:
        users[row[0]] = {'pw':row[1], 'name':row[2]}
    return users


def fetch_locations():
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select l_id, name from location")
    data = c.fetchall()
    locations = [{'id':x[0], 'name':x[1]} for x in data]
    return locations


def fetch_companies():
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select c_id, name from company")
    data = c.fetchall()
    companies = [{'id':x[0], 'name':x[1]} for x in data]
    return companies


def fetch_routes_data(route_id = None):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select * from location")
    rows = c.fetchall()
    locations = {}
    for row in rows:
        locations[row[0]] = row[1]

    if route_id == None:
        c.execute("select * from route")
    else:
        c.execute("select * from route where r_id = ?", (route_id,))

    rows = c.fetchall()
    routes = {}
    for row in rows:
        routes[row[0]] = "%s - %s (%s km)"%(locations[row[1]], locations[row[2]], row[3])
    return routes


def fetch_companies_data(company_id = None):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    if company_id == None:
        c.execute("select c_id, name from company")
    else:
        c.execute("select c_id, name from company where c_id = ?", (company_id))

    rows = c.fetchall()
    companies = {}
    for row in rows:
        companies[row[0]] = row[1]
    return companies



def fetch_flights(from_id, to_id, dept_date, company_id, flight_id = None):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    if flight_id != None:
        pass
    elif from_id == 'none' and to_id == 'none':
        c.execute("select r_id from route")
        rows = c.fetchall()
    elif to_id == 'none':
        c.execute("select r_id from route where from_id = ?", (from_id,))
        rows = c.fetchall()
    elif from_id == 'none':
        c.execute("select r_id from route where to_id = ?", (to_id,))
        rows = c.fetchall()
    else:
        c.execute("select r_id from route where from_id = ? and to_id = ?", (from_id, to_id))
        rows = c.fetchall()


    flights = []
    if flight_id != None:
        c.execute("select * from flight where f_id = ?", (flight_id,))
        data = c.fetchall()
        if len(data) != 0:
            data = [list(data[0]) + ['Not departed']]
        else:
            c.execute("select * from old_flight where f_id = ?", (flight_id,))
            data = c.fetchall()
            data = [list(data[0]) + ['Departed']]
        flights.extend(data)

    else:
        routes = [data[0] for data in rows]

        for route in routes:
            if dept_date == 'Date':
                if company_id == 'none':
                    c.execute("select * from flight where r_id = ?", (route,))
                else:
                    c.execute("select * from flight where r_id = ? and c_id = ?", (route, company_id))
            else:
                if company_id == 'none':
                    c.execute("select * from flight where r_id = ? and dept_date = ?", (route, dept_date))
                else:
                    c.execute("select * from flight where r_id = ? and dept_date = ? and c_id = ?", (route, dept_date, company_id))
            data = c.fetchall()
            if len(data) != 0:
                flights.extend(data)

    # sort flights by arrival time
    flights.sort(key = lambda x: datetime.strptime(x[9] + ' ' + x[10], "%Y-%m-%d %H:%M:%S"), reverse = False)

    # get companies
    companies = fetch_companies_data()

    # get routes data
    routes = fetch_routes_data()

    table = []

    for row in flights:
        new_row = []
        # flight ID
        new_row.append("<a href = '/flight/%s/'>%s</a>"%(row[0], row[0]))
        # route + distance
        new_row.append(routes[row[1]])
        # company name
        new_row.append(companies[row[2]])
        # departure time
        dtime = row[10] + '<br/>' + row[9]
        new_row.append(dtime)
        # arrival time
        atime = row[12] + '<br/>' + row[11]
        new_row.append(atime)
        # eco_booked/eco_capacity
        new_row.append(str(row[7]) + '/' + str(row[5]))
        # economy fare
        new_row.append('Rs. ' + str(row[3]))
        # bus_booked/bus_capacity
        new_row.append(str(row[8]) + '/' + str(row[6]))
        # business fare
        new_row.append('Rs. ' + str(row[4]))
        # departed or not
        if len(row) == 14:
            new_row.append(row[13])

        table.append(new_row)

    return table



def commit_booking(f_id, email, btime, flight_type, price):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    if flight_type == 'eco':
        c.execute("update flight set eco_booked = eco_booked + 1 where f_id = ?", (f_id,))
    else:
        c.execute("update flight set bus_booked = bus_booked + 1 where f_id = ?", (f_id,))
    conn.commit()

    c.execute("select p_id from passenger where email = ?", (email,))
    p_id = c.fetchall()[0][0]

    c.execute("insert into booking (f_id, p_id, b_time, flight_type, price) values(?,?,?,?,?)", (f_id, p_id, btime, flight_type, price))
    conn.commit()



def booking_template(bookings, cancellation):

    rows = []

    for booking in bookings:
        row = []
        # booking ID
        row.append(booking[0])
        # flight ID
        row.append("<a href = '/flight/%s/'>%s</a>"%(booking[1], booking[1]))
        # booking time
        row.append(str(booking[3][:19]).replace(' ','<br/>'))
        # flight type
        if booking[4] == 'eco':
            row.append('economy')
        else:
            row.append('business')
        # price
        row.append('Rs. ' + str(booking[5]))

        # cancellation option
        if cancellation == True:
            row.append("<a href = '/cancel/%s/'>Cancel</a>"%(booking[0]))
        else:
            row.append("Non-cancellable")

        rows.append(row)

    return rows


def fetch_bookings(email):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select p_id from passenger where email = ?", (email,))
    p_id = c.fetchall()[0][0]

    bookings = []

    # bookings of passed flights
    c.execute("select b_id, booking.f_id, p_id, b_time, flight_type, price from booking, old_flight where p_id = ? and booking.f_id = old_flight.f_id", (p_id,))
    bookings.append(c.fetchall())

    # bookings of current flights
    c.execute("select b_id, booking.f_id, p_id, b_time, flight_type, price from booking, flight where p_id = ? and booking.f_id = flight.f_id", (p_id,))
    bookings.append(c.fetchall())

    # no bookings found
    if len(bookings[0] + bookings[1]) == 0:
        return None

    # sort bookings according to booking time
    bookings[0].sort(key = lambda x: datetime.strptime(x[3],"%Y-%m-%d %H:%M:%S.%f"), reverse = True)
    bookings[1].sort(key = lambda x: datetime.strptime(x[3],"%Y-%m-%d %H:%M:%S.%f"), reverse = True)

    table = [booking_template(bookings[0], False), booking_template(bookings[1], True)]

    return table



def cancel_booking(email, b_id):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()

    c.execute("select p_id from passenger where email = ?", (email,))
    p_id = c.fetchall()[0][0]

    c.execute("select * from booking where p_id = ? and b_id = ?", (p_id, b_id))
    booking = c.fetchall()

    # booking not found or user not authorized to cancel
    if len(booking) == 0:
        return -1

    f_id = booking[0][1]
    flight_type = booking[0][4]
    c.execute("select * from flight where f_id = ?", (f_id,))
    flight = c.fetchall()

    # flight departed
    if len(flight) == 0:
        return 0

    c.execute("delete from booking where b_id = ?", (b_id,))
    conn.commit()

    if flight_type == 'eco':
        c.execute("update flight set eco_booked = eco_booked - 1 where f_id = ?", (f_id,))
    else:
        c.execute("update flight set bus_booked = bus_booked - 1 where f_id = ?", (f_id,))
    conn.commit()

    return 1



if not os.path.isfile('./airlines.db'):
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()
    init_db()
    fill_routes()
    fill_flights()
    update_flights()
else:
    conn = sqlite3.connect('./airlines.db')
    c = conn.cursor()


