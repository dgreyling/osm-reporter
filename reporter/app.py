import urllib2
import optparse
import logging

from flask import Flask, request, jsonify, render_template

from reporter import config
from reporter.utilities import (
    split_bbox,
    osm_object_contributions,
    get_totals, osm_nodes_by_user)
from reporter.osm import get_osm_file
from reporter.static import static_file
from reporter.logger import setup_logger

setup_logger()
LOGGER = logging.getLogger('osm-reporter')

app = Flask(__name__)


@app.route('/')
def current_status():
    mySortedUserList = []
    bbox = request.args.get('bbox', config.BBOX)
    myTagName = request.args.get('obj', config.TAG_NAMES[0])
    error = None
    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
    else:
        try:
            myFile = get_osm_file(bbox, coordinates)
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
        else:
            if not myTagName in config.TAG_NAMES:
                error = "Unsupported object type"
            else:
                mySortedUserList = osm_object_contributions(myFile, myTagName)

    myNodeCount, myWayCount = get_totals(mySortedUserList)

    # We need to manually cast float in string, otherwise floats are
    # truncated, and then rounds in Leaflet result in a wrong bbox
    # Note: slit_bbox should better keep returning real floats
    coordinates = dict((k, repr(v)) for k, v in coordinates.iteritems())

    context = dict(
        mySortedUserList=mySortedUserList,
        myWayCount=myWayCount,
        myNodeCount=myNodeCount,
        myUserCount=len(mySortedUserList),
        bbox=bbox,
        current_tag_name=myTagName,
        available_tag_names=config.TAG_NAMES,
        error=error,
        coordinates=coordinates,
        display_update_control=int(config.DISPLAY_UPDATE_CONTROL),
    )
    return render_template('base.html', **context)


@app.route('/user')
def user_status():
    """Get nodes for user as a json doc.

        .. note:: User from reporter.js

        To use e.g.:

        http://localhost:5000/user?bbox=20.431909561157227,
        -34.02849543118406,20.45207977294922,-34.02227106658948&
        obj=building&username=timlinux
    """
    username = request.args.get('username')
    bbox = request.args.get('bbox')

    try:
        coordinates = split_bbox(bbox)
    except ValueError:
        error = "Invalid bbox"
        coordinates = split_bbox(config.BBOX)
        LOGGER.exception(error + coordinates)
    else:
        try:
            myFile = get_osm_file(bbox, coordinates)
        except urllib2.URLError:
            error = "Bad request. Maybe the bbox is too big!"
            LOGGER.exception(error + coordinates)
        else:
            node_data = osm_nodes_by_user(myFile, username)
            return jsonify(d=node_data)


if __name__ == '__main__':
    setup_logger()
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', default=False,
                      help='turn on Flask debugging', action='store_true')

    options, args = parser.parse_args()

    if options.debug:
        LOGGER.info('Running in debug mode')
        app.debug = True
        # set up flask to serve static content
        app.add_url_rule('/<path:path>', 'static_file', static_file)
    else:
        LOGGER.info('Running in production mode')
    app.run()
