drop table if exists passenger;
create table passenger (
  p_id integer primary key,
  name text not null,
  pw_hash text not null,
  email text not null
);

drop table if exists location;
create table location (
  l_id integer primary key,
  name text
);


drop table if exists route;
create table route (
  r_id integer primary key,
  from_id integer,
  to_id integer,
  distance integer,
  foreign key(from_id) references location(l_id),
  foreign key(to_id) references location(l_id)

);

drop table if exists company;
create table company (
  c_id integer primary key,
  name text
);


drop table if exists flight;
create table flight (
  f_id integer primary key,
  r_id integer,
  c_id integer,
  eco_fare integer,
  bus_fare integer,
  eco_capacity integer,
  bus_capacity integer,
  eco_booked integer,
  bus_booked integer,
  dept_date text,
  dept_time text,
  arr_date text,
  arr_time text,

  foreign key(r_id) references route(r_id),
  foreign key(c_id) references company(c_id)
);

drop table if exists old_flight;
create table old_flight (
  f_id integer primary key,
  r_id integer,
  c_id integer,
  eco_fare integer,
  bus_fare integer,
  eco_capacity integer,
  bus_capacity integer,
  eco_booked integer,
  bus_booked integer,
  dept_date text,
  dept_time text,
  arr_date text,
  arr_time text,

  foreign key(r_id) references route(r_id),
  foreign key(c_id) references company(c_id)
);

drop table if exists booking;
create table booking (
  b_id integer primary key,
  f_id integer,
  p_id integer,
  b_time text,
  flight_type text,
  price integer,
  foreign key(f_id) references flight(f_id),
  foreign key(p_id) references passenger(p_id)
);


insert into company (name) values('Indian airlines');
insert into company (name) values('Jet airways');

insert into location (name) values('New Delhi');
insert into location (name) values('Mumbai');
insert into location (name) values('Chennai');
insert into location (name) values('Kolkata');
insert into location (name) values('Bangalore');

insert into passenger values(1, 'Nikhil', '1234', 'nikhilksingh97@gmail.com');
insert into passenger values(2, 'Manish', '1212', 'niveshksingh@gmail.com');
insert into passenger values(3, 'Nivesh', '4321', 'm_rawat@gmail.com');