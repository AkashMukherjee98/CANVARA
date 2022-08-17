#from sqlalchemy import create_engine 
#import pandas as pd
import os
from platform import release
import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Date, Boolean #MetaData
from sqlalchemy.orm import sessionmaker , relationship, backref
from datetime import date

#engine = create_engine("postgresql://postgres:root@localhost:5432/postgres", echo = True)
engine = create_engine("postgresql://postgres:root@localhost:5432/sqlalchemy", echo = True)

#meta = MetaData()

Session = sessionmaker(bind=engine)
Base = declarative_base()

# #One To Many
# class Article(Base):
#    __tablename__ = 'articles'
#    id = Column(Integer, primary_key=True)
#    comments = relationship("Comment")


# class Comment(Base):
#    __tablename__ = 'comments'
#    id = Column(Integer, primary_key=True)
#    article_id = Column(Integer, ForeignKey('articles.id'))

# #Many To One
# class Tire(Base):
#    __tablename__ = 'tires'
#    id = Column(Integer, primary_key=True)
#    car_id = Column(Integer, ForeignKey('cars.id'))
#    car = relationship("Car")


# class Car(Base):
#     __tablename__ = 'cars'
#     id = Column(Integer, primary_key=True)

# #One To One
# class Person(Base):
#    __tablename__ = 'people'
#    id = Column(Integer, primary_key=True)
#    mobile_phone = relationship("MobilePhone", uselist=False, back_populates="person")

# class MobilePhone(Base):
#     __tablename__ = 'mobile_phones'
#     id = Column(Integer, primary_key=True)
#     person_id = Column(Integer, ForeignKey('people.id'))
#     person = relationship("Person", back_populates="mobile_phone")

# #Many To Many
# students_classes_association = Table('students_classes', Base.metadata,
#    Column('student_id', Integer, ForeignKey('students.id')),
#    Column('class_id', Integer, ForeignKey('classes.id'))
# )

# class Student(Base):
#    __tablename__ = 'students'
#    id = Column(Integer, primary_key=True)
#    classes = relationship("Class", secondary=students_classes_association)

# class Class(Base):
#    __tablename__ = 'classes'
#    id = Column(Integer, primary_key=True)

# class Movie(Base):
#    __tablename__ = 'movies'

#    id = Column(Integer, primary_key=True)
#    title = Column(String)
#    release_date = Column(Date)

#    def __init__(self, title, release_date):
#       self.title = title
#       self.release_date = release_date



movies_actors_association = Table(
    'movies_actors', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('actor_id', Integer, ForeignKey('actors.id'))
)

class Movie(Base):
   __tablename__ = 'movies'

   id = Column(Integer, primary_key=True)
   title = Column(String)
   release_date = Column(Date)
   actors = relationship("Actor", secondary=movies_actors_association)

   def __init__(self, title, release_date):
      self.title = title
      self.release_date = release_date

class Actor(Base):
   __tablename__ = 'actors'

   id = Column(Integer, primary_key=True)
   name = Column(String)
   birthday = Column(Date)

   def __init__(self, name, birthday):
      self.name = name
      self.birthday = birthday

class Stuntman(Base):
   __tablename__ = 'stuntmen'

   id = Column(Integer, primary_key=True)
   name = Column(String)
   active = Column(Boolean)
   actor_id = Column(Integer, ForeignKey('actors.id'))
   actor = relationship("Actor", backref=backref("stuntman", uselist=False))

   def __init__(self, name, active, actor):
      self.name = name
      self.active = active
      self.actor = actor


class ContactDetails(Base):
   __tablename__ = 'contact_details'

   id = Column(Integer, primary_key=True)
   phone_number = Column(String)
   address = Column(String)
   actor_id = Column(Integer, ForeignKey('actors.id'))
   actor = relationship("Actor", backref="contact_details")

   def __init__(self, phone_number, address, actor):
      self.phone_number = phone_number
      self.address = address
      self.actor = actor

def make_table():
   Base.metadata.create_all(engine)
   print("Table is created Successfully")
   return "Table is Created"

def insert_value():
   # 4 - create movies
   bourne_identity = Movie("The Bourne Identity", date(2002, 10, 11))
   furious_7 = Movie("Furious 7", date(2015, 4, 2))
   pain_and_gain = Movie("Pain & Gain", date(2013, 8, 23))

   # 5 - creates actors
   matt_damon = Actor("Matt Damon", date(1970, 10, 8))
   dwayne_johnson = Actor("Dwayne Johnson", date(1972, 5, 2))
   mark_wahlberg = Actor("Mark Wahlberg", date(1971, 6, 5))

   # 6 - add actors to movies
   bourne_identity.actors = [matt_damon]
   furious_7.actors = [dwayne_johnson]
   pain_and_gain.actors = [dwayne_johnson, mark_wahlberg]

   # 7 - add contact details to actors
   matt_contact = ContactDetails("415 555 2671", "Burbank, CA", matt_damon)
   dwayne_contact = ContactDetails("423 555 5623", "Glendale, CA", dwayne_johnson)
   dwayne_contact_2 = ContactDetails("421 444 2323", "West Hollywood, CA", dwayne_johnson)
   mark_contact = ContactDetails("421 333 9428", "Glendale, CA", mark_wahlberg)

   # 8 - create stuntmen
   matt_stuntman = Stuntman("John Doe", True, matt_damon)
   dwayne_stuntman = Stuntman("John Roe", True, dwayne_johnson)
   mark_stuntman = Stuntman("Richard Roe", True, mark_wahlberg)

   #Base.metadata.create_all(engine)

   # 3 - create a new session
   session = Session()
   # 9 - persists data
   session.add(bourne_identity)
   session.add(furious_7)
   session.add(pain_and_gain)

   session.add(matt_contact)
   session.add(dwayne_contact)
   session.add(dwayne_contact_2)
   session.add(mark_contact)

   session.add(matt_stuntman)
   session.add(dwayne_stuntman)
   session.add(mark_stuntman)

   # 10 - commit and close session
   session.commit()
   session.close()
   print("Inserted Successfuly")
   return "Inserted Successfuly" 

def row_details():
   session= Session()
   movies = session.query(Movie).all()
   # 4 - print movies' details
   print('\n### All movies:')
   for movie in movies:
      #print(f'{movie.title} was released on {movie.release_date}')
      print("Movie name is: ",movie.title,"was released on: ",movie.release_date)
      print('\n')
   print('')
   # movie_details=[]
   # for movie in movies:
   #    dic={}
   #    #print(f'{movie.title} was released on {movie.release_date}')
   #    movie_name=movie.title
   #    release_date=movie.release_date
   #    dic=movie_name,release_date
   #    movie_details.append(dic)
   # print(movie_details)
   # #print("ok")
   # return "okk"

def fetch_all_row():
   session= Session()
   movies = session.query(Movie).filter(Movie.release_date > date(2015, 1, 1)).all()
   print('### Recent movies:')
   for movie in movies:
      #print(f'{movie.title} was released after 2015')
      print("Movie Name: ",movie.title,'was released after 2015')
   #print("Okk")
   print('')

   the_rock_movies = session.query(Movie).join(Actor, Movie.actors).filter(Actor.name == 'Dwayne Johnson').all()
   print('### Dwayne Johnson movies:')
   for movie in the_rock_movies:
      print(f'The Rock starred in {movie.title}')
   #print('Okk')
   print('')

   glendale_stars = session.query(Actor).join(ContactDetails).filter(ContactDetails.address.ilike('%glendale%')).all()
   print('### Actors that live in Glendale:')
   for actor in glendale_stars:
      print(f'{actor.name} has a house in Glendale')
   print('')
   


#make_table()
#insert_value()
#row_details()
fetch_all_row()



# class Restaurant(Base):
#    __tablename__ = 'restaurant'

#    id = Column(Integer, primary_key=True, autoincrement=True)
#    name = Column(String(250), nullable=False)


# class MenuItem(Base):
#    __tablename__ = 'menu_item'

#    name = Column(String(80), nullable=False)
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    description = Column(String(250))
#    price = Column(String(8))
#    course = Column(String(250))
#    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
#    restaurant = relationship(Restaurant)

#Base.metadata.create_all(engine)

# students = Table(
#    'students', meta, 
#    Column('id', Integer, primary_key = True), 
#    Column('name', String), 
#    Column('lastname', String),
# )
#meta.create_all(engine)

# ins = students.insert()
# ins = students.insert().values(name = 'prudhvi', lastname = 'varma')
# conn = engine.connect()
# result = conn.execute(ins)
# conn = engine.connect()
# conn.execute(students.insert(), [
#    {'name':'Bhaskar', 'lastname' : 'guptha'},
#    {'name':'vibhav','lastname' : 'kumar'},
#    {'name':'prudhvi','lastname' : 'varma'},
#    {'name':'manoj','lastname' : 'varma'},
# ])

#pg_engine = ce("postgresql://postgres:root@localhost:5432/postgres")
#data.to_sql('telescope_table', pg_engine)
#print("okk")