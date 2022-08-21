# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import sys
import dateutil.parser
import babel
from flask import render_template, request, flash, redirect, url_for, abort
import logging
from logging import Formatter, FileHandler
from flask import Flask
from flask_moment import Moment
from flask_migrate import Migrate
from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


# Database connection done in config.py

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues display DONE
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    error = False
    data = []
    places = set()
    try:
        venues = Venue.query.all()
        # get all [cities, states] -{duplicated}
        for venue in venues:
            places.add((venue.city, venue.state))
        for place in places:
            data.append({
                'city': place[0],
                'state': place[1],
                "venues": []
            })
        # num_upcoming_shows based on number of upcoming shows per venue
        for venue in venues:
            num_upcoming_shows = 0
            shows = Show.query.all()
            for show in shows:
                if show.start_time > datetime.now():
                    num_upcoming_shows += 1
            for venue_places in data:
                if venue.state == venue_places['state'] and venue.city == venue_places['city']:
                    venue_places['venues'].append({
                        'id': venue.id,
                        'name': venue.name,
                        'num_upcoming_shows': num_upcoming_shows
                    })
    except():
        error = True
        print(sys.exc_info())
    if not error:
        return render_template('pages/venues.html', areas=data)


#  Search Venue DONE
#  ----------------------------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '').lower()
    search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    response = {
        "count": len(search_result),
        "data": search_result
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term)


#  Show Venue bi ID DONE
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue_id).all()
    upcoming_shows = []
    past_shows = []

    # past & upcoming shows
    for show in shows:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time)),
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(data)
        else:
            past_shows.append(data)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
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


#  Create Venue DONE
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Venue Creation implemented
    error = False
    if 'seeking_talent' in request.form:
        seeking = True
    else:
        seeking = False
    print(seeking)
    lis = request.form.getlist('genres')
    venue = Venue(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        address=request.form['address'],
        phone=request.form['phone'],
        genres=lis,
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website_link=request.form['website_link'],
        seeking_talent=seeking,
        seeking_description=request.form['seeking_description']
    )
    try:
        db.session.add(venue)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash an error
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Delete Venue DONE
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>/delete/', methods=['DELETE'])
def delete_venue(venue_id):
    # Venue deletion controller & vue implementation with session commit error handling
    error = False
    venue = Venue.query.get(venue_id)
    try:
        for show in venue.shows:
            db.session.delete(show)
        db.session.delete(venue)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + venue.name + ' was not deleted.')
    else:
        flash('Venue ' + venue.name + ' was successfully deleted.')
        return redirect(url_for('venues'))


#  Artists display DONE
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    error = False
    data = []
    try:
        artists = Artist.query.all()
        for artist in artists:
            data.append({
                "id": artist.id,
                "name": artist.name,
            })
    except Artist.GetFailed:
        error = True
        print(sys.exc_info())
    return render_template('pages/artists.html', artists=data)


#  Search Artist DONE
#  ----------------------------------------------------------------
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '').lower()
    search_result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(search_result),
        "data": search_result
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


# Display Artist by ID DONE
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    shows = Show.query.filter_by(artist_id=artist_id).all()
    upcoming_shows = []
    past_shows = []

    # past & upcoming shows
    for show in shows:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": format_datetime(str(show.start_time)),
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(data)
        else:
            past_shows.append(data)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


# ----------------------------------------------------------------------------#
#  Updates
# ----------------------------------------------------------------------------#

#  Update Artist DONE
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    artist = Artist.query.get(artist_id)
    if 'seeking_venue' in request.form:
        seeking = True
    else:
        seeking = False
    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')

        if not request.form['facebook_link'] == "":
            artist.facebook_link = request.form['facebook_link']
        else:
            artist.facebook_link = Artist.facebook_link
        if not request.form['image_link'] == "":
            artist.image_link = request.form['image_link']
        else:
            artist.image_link = Artist.image_link
        if not request.form['website_link'] == "":
            artist.website_link = request.form['website_link']
        else:
            artist.website_link = Artist.website_link
        artist.seeking_venue = seeking
        if not request.form['seeking_description'] == "":
            artist.seeking_description = request.form['seeking_description']
        else:
            artist.seeking_description = Artist.seeking_description
        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # on unsuccessful db update, flash an error
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be update.')
    else:
        # on successful db update, flash success
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))


#  Update Venue DONE
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    venue = Venue.query.get(venue_id)
    if 'seeking_venue' in request.form:
        seeking = True
    else:
        seeking = False
    print(seeking)
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.genres = request.form.getlist('genres')
        venue.phone = request.form['phone']

        if not request.form['facebook_link'] == "":
            venue.facebook_link = request.form['facebook_link']
        else:
            venue.facebook_link = Venue.facebook_link
        if not request.form['image_link'] == "":
            venue.image_link = request.form['image_link']
        else:
            venue.image_link = Venue.image_link
        if not request.form['website_link'] == "":
            venue.website_link = request.form['website_link']
        else:
            venue.website_link = Venue.website_link
        venue.seeking_talent = seeking
        if not request.form['seeking_description'] == "":
            venue.seeking_description = request.form['seeking_description']
        else:
            venue.seeking_description = Venue.seeking_description
        db.session.commit()
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # on unsuccessful db update, flash an error
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be update.')
    else:
        # on successful db update, flash success
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist DONE
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Artist Creation implemented
    error = False
    if 'seeking_venue' in request.form:
        seeking = True
    else:
        seeking = False
    print(seeking)
    lis = request.form.getlist('genres')
    artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=lis,
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website_link=request.form['website_link'],
        seeking_venue=seeking,
        seeking_description=request.form['seeking_description']
    )
    try:
        db.session.add(artist)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash an error
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Delete Artist DONE
#  ----------------------------------------------------------------
@app.route('/artists/<artist_id>/delete/', methods=['DELETE'])
def delete_artist(artist_id):
    # Artist deletion controller & vue implementation with session commit error handling
    error = False
    artist = Artist.query.get(artist_id)
    try:
        for show in artist.shows:
            db.session.delete(show)
        db.session.delete(artist)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + artist.name + ' was not deleted.')
    else:
        flash('Artist ' + artist.name + ' was successfully deleted.')
        return redirect(url_for('show_artist'))


#  Display Shows DONE
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # Display Shows order by Start Date Desc
    shows = Show.query.order_by(Show.start_time.desc()).all()
    data = []
    error = False
    try:
        for show in shows:
            data.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    except():
        error = True
    if error:
        abort(404)
    else:
        return render_template('pages/shows.html', shows=data)


#  Create Show DONE
#  ----------------------------------------------------------------
@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # Show Creation implemented
    error = False
    show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time']
    )
    try:
        db.session.add(show)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash an error
        flash('An error occurred. Show could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')
        return render_template('pages/home.html')


#  Search Show DONE
#  ----------------------------------------------------------------
@app.route('/shows/search', methods=['POST'])
def search_shows():
    search_term = request.form.get('search_term', '').lower()
    search_result = Show.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(search_result),
        "data": search_result
    }
    return render_template('pages/show.html', results=response,
                           search_term=search_term)


# ----------------------------------------------------------------------------#
#  Error Handling
# ----------------------------------------------------------------------------#

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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#
if __name__ == '__main__':
    app.run()
