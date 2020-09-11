#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from datetime import datetime
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


from models import *


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en_US')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  # Lists all the venues in a state -> city

  unique_city_states = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  data = []

  for unique_city_state in unique_city_states:

    current_area = Venue.query.filter_by(state=unique_city_state.state).filter_by(city=unique_city_state.city).all()

    venue_data = []

    for venue in current_area:

      venue_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
      })

    data.append({
      "city": unique_city_state.city,
      "state": unique_city_state.state,
      "venues": venue_data

    })

  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():

  # list the venues that matches with the search term

  search_term = request.form.get('search_term', '')

  venue_result_set = Venue.query.filter(func.lower(Venue.name).like(func.lower("%" + search_term + "%"))).all()

  num_matches = len(venue_result_set)

  data = []

  for venue in venue_result_set:

    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
    })

  response = {
    "count": num_matches,
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  venue = db.session.query(Venue).get(venue_id)

  if not venue:
    return render_template('errors/404.html')

  past_show_results = db.session.query(Show).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

  past_shows = []

  for show in past_show_results:

    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S')
    })

  upcoming_show_results = db.session.query(Show).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

  upcoming_shows = []

  for show in upcoming_show_results:

    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S')
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  # store venue form data to database

  error = False

  try:
    name = request.form.get('name')
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    website = request.form['website']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']

    new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,  website=website, image_link=image_link, facebook_link=facebook_link, seeking_talent=seeking_talent, seeking_description=seeking_description)

    db.session.add(new_venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  # delete a venue with given id

  error = False

  try:
    tobe_del_venue = Venue.query.get(venue_id)
    db.session.delete(tobe_del_venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash(f'Venue {venue_id} was deleted successfully!')
      return redirect(url_for('index'))
    else:
      flash(f'An error occurred! Venue {venue_id} could not be deleted.')

  return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  # lists all the available artists

  data = []

  artists = db.session.query(Artist).with_entities(Artist.id, Artist.name).all()

  for artist in artists:

    data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

  # logic to search artists with provided search term

  search_term = request.form.get('search_term','')

  artists = Artist.query.filter(func.lower(Artist.name).like(func.lower("%" + search_term + "%"))).all()

  data = []

  for artist in artists:

    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all())
    })

  response = {
    "count": len(artists),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id

  artist = Artist.query.get(artist_id)

  if not artist:
    return render_template('errors/404.html')

  past_show_data = db.session.query(Show).join(Venue).filter(Show.artist_id == artist.id).filter(Show.start_time < datetime.now()).all()
  past_shows = []

  for past_show in past_show_data:

    past_shows.append({
      "venue_id": past_show.venue_id,
      "venue_name": past_show.venue.name,
      "venue_image_link": past_show.venue.image_link,
      "start_time": past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_show_data = db.session.query(Show).join(Venue).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()
  upcoming_shows = []

  for upcoming_show in upcoming_show_data:

    upcoming_shows.append({
      "venue_id": upcoming_show.venue_id,
      "venue_name": upcoming_show.venue.name,
      "venue_image_link": upcoming_show.venue.image_link,
      "start_time": upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  # pre-fill the edit form with artist details

  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  if artist:
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  # updates the artist with given id

  error = False

  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash('Artist was successfully updated!')
    else:
      flash('An error occurred. Artist could not be changed.')

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  # pre-fill the edit form with venue details

  form = VenueForm()

  venue = Venue.query.get(venue_id)

  if venue:
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  # updates the venue with given id

  error = False

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.address = request.form.get('address')
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash('Venue was successfully updated!')
    else:
      flash('An error occurred. Venue could not be changed.')

  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():

  # shows form for Artist creation

  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # called upon submitting the new artist listing form

  error = False

  try:
    name = request.form.get('name')
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    website = request.form['website']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']

    new_artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, website=website,
                      image_link=image_link, facebook_link=facebook_link, seeking_venue=seeking_venue,
                      seeking_description=seeking_description)

    db.session.add(new_artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  # displays list of shows at /shows

  shows = db.session.query(Show).join(Venue).join(Artist).all()

  data = []

  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():

  # lists all shows from the database

  form = ShowForm()

  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  # creates a new show based on the values from Show form

  error = False

  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request. form.get('start_time')

    new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(new_show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

    if not error:
      flash('Show was successfully listed!')
    else:
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
