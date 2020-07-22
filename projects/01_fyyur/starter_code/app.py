#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import datetime

import traceback

from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:12345678@localhost:5432/fyyur'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# DTODO: connect to a local postgresql database
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)

    def __repr__(self):
      return f'Venue {self.name},{self.city}'

    @property
    def fields(self):
      return {
        "id": self.id,
        "name": self.name,
        "genres": self.genres.split(','),
        "address": self.address,
        "city": self.city,
        "state": self.state,
        "phone": self.phone,
        "website": self.website,
        "facebook_link": self.facebook_link,
        "seeking_talent": self.seeking_talent,
        "seeking_description": self.seeking_description,
        "image_link": self.image_link
        }
    @property
    def fields_with_shows(self):
      return {
        "id": self.id,
        "name": self.name,
        "genres": self.genres.split(','),
        "address": self.address,
        "city": self.city,
        "state": self.state,
        "phone": self.phone,
        "website": self.website,
        "facebook_link": self.facebook_link,
        "seeking_talent": self.seeking_talent,
        "seeking_description": self.seeking_description,
        "image_link": self.image_link,
        "past_shows": [{
          "artist_id": i[0],
          "artist_name": db.session.query(Artist.name).filter(i[0] == Artist.id).one_or_none(),
          "artist_image_link": db.session.query(Artist.image_link).filter(i[0] == Artist.id).one_or_none(),
          "start_time": str(i[1])
        } for i in db.session.query(Show.artist_id,Show.start_time).filter(Show.venue_id == self.id).
        filter(Show.start_time < datetime.datetime.now()).all()],
        "upcoming_shows": [{
          "artist_id": i[0],
          "artist_name": db.session.query(Artist.name).filter(i[0] == Artist.id).one_or_none(),
          "artist_image_link": db.session.query(Artist.image_link).filter(i[0] == Artist.id).one_or_none(),
          "start_time": str(i[1])
        } for i in db.session.query(Show.artist_id,Show.start_time).filter(Show.venue_id == self.id).
        filter(Show.start_time > datetime.datetime.now()).all()],
        "past_shows_count": len(db.session.query(Show.artist_id,Show.start_time).filter(Show.venue_id == self.id).
        filter(Show.start_time < datetime.datetime.now()).all()),
        "upcoming_shows_count": len(db.session.query(Show.artist_id,Show.start_time).filter(Show.venue_id == self.id).
        filter(Show.start_time > datetime.datetime.now()).all()),
      }


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean,default = False)
    seeking_description = db.Column(db.String)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id'))
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

# done
@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = [
    {
      "city": i[0],
      "state": i [1],
      "venues": [{
        "id": j[0],
        "name": j[1],
        "num_upcoming_shows": db.session.query(Show).filter(Show.venue_id == j[0]).count(),
        } for j in db.session.query(Venue.id,Venue.name).filter(Venue.city == i[0]).filter(Venue.state == i[1]).all()
      ]
    }
    for i in db.session.query(Venue.city,Venue.state).distinct().all()
  ]
  return render_template('pages/venues.html', areas=data)

# done
@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  dataQuery = db.session.query(Venue.id,Venue.name).filter(Venue.name.contains(request.form.get('search_term'))).all()
  data = [{
   "id":i[0],
   "name":i[1],
   "num_upcoming_shows": db.session.query(Show).filter(Venue.name == i[1]).filter(Venue.id == Show.venue_id).count()
   } for i in dataQuery ]
  response = {
    "count":len(data),
    "data":data
  }  
  print(response)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

# done
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  ven = db.session.query(Venue).filter(Venue.id == venue_id).one_or_none()
  data = ven.fields_with_shows
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

# done
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

# done
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion 
  try:
    ven = Venue(
      name =request.form['name'],
      city =request.form['city'],
      state =request.form['state'],
      address =request.form['address'],
      phone =request.form['phone'],
      image_link =request.form['image_link'],
      facebook_link =request.form['facebook_link'],
      genres =','.join(request.form.getlist('genres'))
      )
    db.session.add(ven)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as ex:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    traceback.print_exc()
  return render_template('pages/home.html')

# done
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue_to_delete = Venue.query.filter(Venue.id == venue_id).one()
    venue_to_delete.delete()
    flash("Venue "+venue_to_delete['name'] +" has been deleted successfully")
  except NoResultFound:
    abort(404)
  return None

#  Artists
#  ----------------------------------------------------------------

# done
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  dataQuery = db.session.query(Artist.id,Artist.name).all()
  data = [
    {
      "id": i[0],
      "name": i[1]
    } for i in dataQuery ]
  return render_template('pages/artists.html', artists=data)

# done
@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  dataQuery = db.session.query(Artist.id,Artist.name).filter(Artist.name.contains(request.form.get('search_term'))).all()
  print(dataQuery)
  data = [{
      "id": i[0],
      "name": i[1],
      "num_upcoming_shows": db.session.query(Show).filter(Artist.name == i[1]).filter(Artist.id == Show.artist_id).count()
    }for i in dataQuery]
  response = {
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# done
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artistQuery = db.session.query(Artist.name,Artist.city ,Artist.state ,Artist.phone ,Artist.genres ,Artist.image_link ,
  Artist.facebook_link ,Artist.website ,Artist.seeking_venue ,Artist.seeking_description).filter(Artist.id == artist_id).first()

  pastShows = [{
    "venue_id": i[0],
    "venue_name": db.session.query(Venue.name).filter(Venue.id == i[0]).first(),
    "venue_image_link": db.session.query(Venue.image_link).filter(Venue.id == i[0]).first(),
    "start_time": str(i[1])
  }
  for i in db.session.query(Show.venue_id,Show.start_time).filter(artist_id == Show.artist_id).filter(Show.start_time < datetime.datetime.now()).all()]
  upcomingShows = [{
    "venue_id": i[0],
    "venue_name": db.session.query(Venue.name).filter(Venue.id == i[0]).first(),
    "venue_image_link": db.session.query(Venue.image_link).filter(Venue.id == i[0]).first(),
    "start_time": str(i[1])
  } for i in db.session.query(Show.venue_id,Show.start_time).filter(artist_id == Show.artist_id).filter(Show.start_time > datetime.datetime.now()).all()]
  artist = {
    "id": artist_id,
    "name": artistQuery[0],
    "city": artistQuery[1],
    "state": artistQuery[2],
    "phone": artistQuery[3],
    "genres": artistQuery[4].split(','), 
    "image_link": artistQuery[5],
    "facebook_link": artistQuery[6],
    "website": artistQuery[7],
    "seeking_venue": artistQuery[8],
    "seeking_description": artistQuery[9],
    "past_shows": pastShows,
    "upcoming_shows": upcomingShows,
    "past_shows_count": len(pastShows),
    "upcoming_shows_count": len(upcomingShows),
  }
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artistQuery = db.session.query(Artist.name,Artist.city ,Artist.state ,Artist.phone ,Artist.genres ,Artist.image_link ,
  Artist.facebook_link ,Artist.website ,Artist.seeking_venue ,Artist.seeking_description).filter(Artist.id == artist_id).first()
  artist = {
    "id": artist_id,
    "name": artistQuery[0],
    "city": artistQuery[1],
    "state": artistQuery[2],
    "phone": artistQuery[3],
    "genres": artistQuery[4].split(','), 
    "image_link": artistQuery[5],
    "facebook_link": artistQuery[6],
    "website": artistQuery[7],
    "seeking_venue": artistQuery[8],
    "seeking_description": artistQuery[9]
  }
  form=ArtistForm(data=artist)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    old_artist = db.session.query(Artist).filter(Artist.id == artist_id).one_or_none()
    old_artist.name = request.form['name']
    old_artist.city = request.form['city']
    old_artist.state = request.form['state']
    old_artist.phone = request.form['phone']
    old_artist.genres = ','.join(request.form.getlist('genres'))
    old_artist.image_link = request.form['image_link']
    old_artist.facebook_link = request.form['facebook_link']
    old_artist.website = request.form['website']
    if 'seeking_venue' in request.form:
      old_artist.seeking_venue = True
    else:
      old_artist.seeking_venue = False
    old_artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    flash("Artist couldn't be edited")
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  ven = db.session.query(Venue).filter(Venue.id == venue_id).one_or_none()
  if ven is None:
    abort(404)
  venue = ven.fields
  form = VenueForm(data=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  old_venue = db.session.query(Venue).filter(Venue.id == venue_id).one_or_none()
  if old_venue == None:
    abort(404)
  old_venue.name = request.form['name'] 
  old_venue.city = request.form['city'] 
  old_venue.state = request.form['state'] 
  old_venue.address = request.form['address'] 
  old_venue.phone = request.form['phone'] 
  old_venue.image_link = request.form['image_link'] 
  old_venue.facebook_link = request.form['facebook_link'] 
  old_venue.genres = ','.join(request.form.getlist('genres'))
  old_venue.website = request.form['website'] 
  if 'seeking_talent' in request.form:
    old_venue.seeking_talent = True
  else:
    old_venue.seeking_talent = False
  old_venue.seeking_description = request.form['seeking_description'] 
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

# done
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

# done
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    art = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      genres = ','.join(request.form.getlist('genres')),
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link']
    )
    db.session.add(art)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as ex:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    traceback.print_exc()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

# done
@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = [{
    "venue_id": i[0],
    "venue_name": db.session.query(Venue.name).filter(Venue.id == i[0]).one_or_none(),
    "artist_id": i[1],
    "artist_name": db.session.query(Artist.name).filter(Artist.id == i[1]).one_or_none(),
    "artist_image_link": db.session.query(Artist.image_link).filter(Artist.id == i[1]).one_or_none(),
    "start_time": str(i[2])
  } for i in db.session.query(Show.venue_id,Show.artist_id,Show.start_time).all()]
  return render_template('pages/shows.html', shows=data)

# done
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

# done
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  print(
    "artist_id" ,request.form['artist_id'],
    "venue_id" ,request.form['venue_id'],
    "start_time" , request.form['start_time'],)
  try:
    show = Show(
    artist_id =request.form['artist_id'],
    venue_id =request.form['venue_id'],
    start_time = request.form['start_time'],
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
