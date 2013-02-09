# -*- coding: utf-8 -*-
"""
    Reporter Tests

    Tests the osm-reporter application.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import os
import unittest
import xml.sax
import logging
import ast
import logging.handlers

from reporter.app import app
from reporter.core import (
    split_bbox,
    get_totals,
    osm_object_contributions,
    interpolated_timeline)
from reporter.osm_parser import OsmParser
from reporter.logger import setup_logger
from reporter.osm import load_osm_document


setup_logger()
LOGGER = logging.getLogger('osm-reporter')

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data',
    'swellendam.osm'
)


class TestCaseLogger(unittest.TestCase):
    def failureException(self, msg):
        LOGGER.exception(msg)
        return self.super(TestCaseLogger, self).failureException(msg)


class CoreTestCase(TestCaseLogger):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_current_status(self):
        try:
            return self.app.post('/', data=dict(), follow_redirects=True)
        except Exception, e:
            LOGGER.exception('Basic front page load failed.')
            raise e

    def test_load_osm_document(self):
        """Check that we can fetch an osm doc and that it caches properly."""
        #
        # NOTE - INTERNET CONNECTION NEEDED FOR THIS TEST
        #
        myUrl = ('http://overpass-api.de/api/interpreter?data='
                 '(node(-34.03112731086964,20.44997155666351,'
                 '-34.029571310785315,20.45501410961151);<;);out+meta;')
        myFilePath = '/tmp/test_load_osm_document.osm'
        if os.path.exists(myFilePath):
            os.remove(myFilePath)
        # We test twice - once to ensure it is fetched from the overpass api
        # and once to ensure the cached file is used on second access
        # Note: There is a small chance the second test could fail if it
        # exactly straddles the cache expiry time.
        try:
            myFile = load_osm_document(myFilePath, myUrl)
        except:
            LOGGER.exception('load_osm_document from overpass test failed %s'
                             % myUrl)
            raise
        myString = myFile.read()
        myMessage = 'load_osm_document from overpass content check failed.'
        assert 'Jacoline' in myString, myMessage

        myFile = load_osm_document(myFilePath, myUrl)
        myFileTime = os.path.getmtime(myFilePath)
        myString = myFile.read()
        #
        # This one should be cached now....
        #
        load_osm_document(myFilePath, myUrl)
        myFileTime2 = os.path.getmtime(myFilePath)
        myMessage = 'load_osm_document cache test failed.'
        self.assertEqual(myFileTime, myFileTime2, myMessage)

    def test_osm_building_contributions(self):
        """Test that we can obtain correct contribution counts for a file."""
        myFile = open(FIXTURE_PATH)
        myList = osm_object_contributions(myFile, tag_name="building")
        myExpectedList = ast.literal_eval(file(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'test_data',
            'expected_osm_building_contributions.txt'
        ), 'rt').read())

        self.maxDiff = None
        print myList
        self.assertListEqual(myList, myExpectedList)

    def test_get_totals(self):
        """Test we get the proper totals from a sorted user list."""
        mySortedUserList = osm_object_contributions(open(FIXTURE_PATH),
                                                    tag_name="building")
        myWays, myNodes = get_totals(mySortedUserList)
        self.assertEquals((myWays, myNodes), (427, 52))

    def test_interpolated_timeline(self):
        """Check that we can get an interpolated timeline,"""
        myTimeline = {u'2012-12-01': 10,
                      u'2012-12-10': 1}
        myExpectedResult = ('[["2012-12-01",10],'
                            '["2012-12-02",0],'
                            '["2012-12-03",0],'
                            '["2012-12-04",0],'
                            '["2012-12-05",0],'
                            '["2012-12-06",0],'
                            '["2012-12-07",0],'
                            '["2012-12-08",0],'
                            '["2012-12-09",0],'
                            '["2012-12-10",1]]')
        myResult = interpolated_timeline(myTimeline)
        self.maxDiff = None
        self.assertEqual(myExpectedResult, myResult)


class OsmParserTestCase(TestCaseLogger):
    """Test the sax parser for OSM data."""

    def test_parse(self):
        """Test that we can parse a predefined osm file."""
        myParser = OsmParser(tagName="building")
        source = open(FIXTURE_PATH)
        xml.sax.parse(source, myParser)
        myExpectedWayDict = {u'Babsie': 37,
                             u'Firefishy': 12,
                             u'Jacoline': 3}
        myExpectedNodeDict = {u'Babsie': 306,
                              u'Firefishy': 104,
                              u'Jacoline': 17}
        myExpectedTimelineDict = {
            u'Babsie': {
                u'2012-12-08': 15,
                u'2012-12-10': 22
            },
            u'Burger': {
                u'2010-05-16': 1
            },
            u'Firefishy': {
                u'2012-09-26': 10,
                u'2012-12-08': 15,
                u'2012-12-09': 5,
                u'2012-12-10': 1
            },
            u'Jacoline': {
                u'2012-12-08': 1,
                u'2012-12-10': 2
            },
            u'thomasF': {
                u'2012-08-22': 5
            },
            u'timlinux': {
                u'2010-12-09': 1,
                u'2012-07-10': 1
            }
        }

        #OsmParser way count test
        self.assertDictEqual(myExpectedWayDict,
                             myParser.wayCountDict)

        #OsmParser node count test
        self.assertDictEqual(myExpectedNodeDict,
                             myParser.nodeCountDict)

        #OsmParser timeline test
        self.assertDictEqual(myExpectedTimelineDict,
                             myParser.userDayCountDict)


class UtilsTestCase(TestCaseLogger):
    def test_split_bbox(self):
        myMessage = 'test_split_box failed.'
        self.assertEqual(
            split_bbox('106.78674459457397,-6.141301491467023,'
                       '106.80691480636597,-6.133834354201348'),
            {
                'SW_lng': 106.78674459457397,
                'SW_lat': -6.141301491467023,
                'NE_lng': 106.80691480636597,
                'NE_lat': -6.133834354201348
            },
            myMessage
        )

    def test_split_bad_bbox(self):
        with self.assertRaises(ValueError):
            split_bbox('invalid bbox string')


if __name__ == '__main__':
    unittest.main()
