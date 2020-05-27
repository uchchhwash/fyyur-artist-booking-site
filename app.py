import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc, text
from flask_wtf import Form
from forms import *
from models import *
recent_data_offset = 3


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# Controllers


@app.route('/')
def index():
    venues = Venue.query.order_by(desc(Venue.id)).limit(recent_data_offset)
    venue_data = []
    for venue in venues:
        venue_data.append({
            "id": venue.id,
            "name": venue.name
        })

    artists = Artist.query.order_by(desc(Artist.id)).limit(recent_data_offset)
    artist_data = []
    for artist in artists:
        artist_data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/home.html', venues=venue_data, artists=artist_data)

#venues#
# all Venues


@app.route('/venues')
def venues():
    data = []

    # all venues fetched
    venues = Venue.query.all()
    track = set()

    for venue in venues:
        track.add((venue.city, venue.state))

    for t in track:
        data.append({
            "city": t[0],
            "state": t[1],
            "venues": []
        })

    for venue in venues:
        num_upcoming_shows = 0
        shows = Show.query.filter_by(venue_id=venue.id).all()
        current_date = datetime.now()
        for show in shows:
            if show.start_time > current_date:
                num_upcoming_shows += 1
        # Comparing current date with fetched shows
        for v_location in data:
            if venue.state == v_location['state'] and venue.city == v_location['city']:
                v_location['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows
                })
    return render_template('pages/venues.html', areas=data)


# create venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm()
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            genres=','.join(form.genres.data),
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            seeking_description=form.seeking_description.data,
            seeking_talent=form.seeking_talent.data
        )

        db.session.add(venue)
        db.session.commit()
    # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
        db.session.rollback()
        flash('Error. Venue ' + request.form['name'] + ' listing Unsuccessful')
    finally:
        db.session.close()
    return render_template('pages/home.html')


# venue search
@app.route('/venues/search', methods=['POST'])
def search_venues():
    # case-insensitive search implemented
    search_term = request.form.get('search_term', '')
    sql = text('select * from public."Venue" where LOWER(city)=:n').params(n=search_term.lower())
    result = db.engine.execute(sql)
    if result.rowcount < 1:
        sql = text('select * from public."Venue" where LOWER(state)=:n').params(n=search_term.lower())
        result = db.engine.execute(sql)
        if result.rowcount  < 1:
            sql = text('select * from public."Venue" where LOWER(name) LIKE :n ;').params(n="%"+search_term.lower()+"%")
            result = db.engine.execute(sql)
    response = {
        "count": result.rowcount,
        "data": result
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


# show venue by id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)
    shows = Show.query.filter_by(venue_id=venue_id).all()
    current_time = datetime.now()
    past_shows = []
    upcoming_shows = []

    for show in shows:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        }

        if show.start_time > current_time:
            upcoming_shows.append(data)
        else:
            past_shows.append(data)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [x.strip() for x in venue.genres.split(',')],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "upcoming_shows_count": len(upcoming_shows),
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "past_shows": past_shows,
    }

    return render_template('pages/show_venue.html', venue=data)


# get venue info by id for edit
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)
    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": [x.strip() for x in venue.genres.split(',')],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


# edit venue info by id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm()
        venue = Venue.query.get(venue_id)
        if venue is None:
            abort(404)
        name = form.name.data
        venue.name = name
        venue.genres = ','.join(form.genres.data)
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.image_link = form.image_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        flash('Venue ' + name + ' has been updated')
    except:
        db.session.rollback()
        flash('Error! Update Venue Unsuccessful')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


# delete venue by id
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        # Get venue by ID
        venue = Venue.query.get(venue_id)
        if venue is None:
            abort(404)
        venue_name = venue.name

        db.session.delete(venue)
        db.session.commit()

        flash('Venue ' + venue_name + ' was deleted')
    except:
        flash('Error! Venue ' + venue_name + ' Deletion Unsuccessful')
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))

#artists#

# all artists


@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()

    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        form = ArtistForm()
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.city.data,
            phone=form.phone.data,
            genres=','.join(form.genres.data),
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data
        )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('Error. Artist ' +
              request.form['name'] + ' listing Unsuccessful.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


# search artists
@app.route('/artists/search', methods=['POST'])
def search_artists():
    # 
    search_term = request.form.get('search_term', '')
    sql = text('select * from public."Venue" where LOWER(city)=:n').params(n=search_term.lower())
    result = db.engine.execute(sql)
    if result.rowcount < 1:
        sql = text('select * from public."Venue" where LOWER(state)=:n').params(n=search_term.lower())
        result = db.engine.execute(sql)
        if result.rowcount  < 1:
            sql = text('select * from public."Venue" where LOWER(name) LIKE :n ;').params(n="%"+search_term.lower()+"%")
            result = db.engine.execute(sql)
    # 
    search_term = request.form.get('search_term', '')
    sql = text('select * from public."Artist" where LOWER(city)=:n').params(n=search_term.lower())
    result = db.engine.execute(sql)
    if result.rowcount < 1:
        sql = text('select * from public."Artist" where LOWER(state)=:n').params(n=search_term.lower())
        result = db.engine.execute(sql)
        if result.rowcount  < 1:
            sql = text('select * from public."Artist" where LOWER(name) LIKE :n ;').params(n="%"+search_term.lower()+"%")
            result = db.engine.execute(sql)
    response = {
        "count": result.rowcount,
        "data": result
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


# show artists info by id
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if artist is None:
        abort(404)
    shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()

    # Filter shows by upcoming and past
    for show in shows:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": format_datetime(str(show.start_time))
        }
        if show.start_time > current_time:
            upcoming_shows.append(data)
        else:
            past_shows.append(data)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [x.strip() for x in artist.genres.split(',')],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)

# get artist info by id for edit


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if artist is None:
        abort(404)
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [x.strip() for x in artist.genres.split(',')],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


# edit artist existing info by id
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        form = ArtistForm()
        artist = Artist.query.get(artist_id)
        if artist is None:
            abort(404)
        artist.name = form.name.data
        artist.phone = form.phone.data
        artist.state = form.state.data
        artist.city = form.city.data
        artist.genres = ','.join(form.genres.data)
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data

        db.session.commit()
        flash('The Artist ' +
              request.form['name'] + ' has been successfully updated!')
    except:
        db.session.rollback()
        flash('Error!  Update Unsuccessful')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        if artist is None:
            abort(404)
        artist_name = artist.name
        db.session.delete(artist)
        db.session.commit()

        flash('Artist ' + artist_name + ' was deleted')
    except:
        flash('Error! and Artist ' + artist_name + ' delete Unsuccessful')
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))

# create artist


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


#shows#
# preview all shows
@app.route('/shows')
def shows():
    shows = Show.query.order_by(db.desc(Show.start_time))

    data = []

    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
        print(data)

    return render_template('pages/shows.html', shows=data)


# create new show
@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        show = Show(
            artist_id=request.form['artist_id'],
            venue_id=request.form['venue_id'],
            start_time=request.form['start_time']
        )

        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('Error.Show Listing Unsuccessful.')
    finally:
        db.session.close()

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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# launch

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
