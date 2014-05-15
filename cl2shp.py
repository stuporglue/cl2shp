#!/usr/bin/env python

# Search multiple Craigslist sites at once and make a shapefile with the results
# Copyright 2014 Michael Moore <stuporglue@gmail.com
# Licensed under the MIT License. Free for any use.

# Usage:

# python.exe cl2shp.py -o output.shp -c list,of,cities [-t type] -s "search terms"

# -c list of CraigsList cities must be comma separated with no spaces

# -t type is optional and is the 3-letter CraigsList category type. It defaults to sss (for sale). 
# Some common types include:
# sss -- for sale
# zip -- free
# cta -- cars and trucks

# Samples

# Search minneapolis, duluth and brainerd for 'dodge ram 1500'
# python.exe cl2shp.py -o truck\truck.shp -c minneapolis,duluth,brainerd -s "dodge ram 1500"

# Search for free saws in minneapolis
# python.exe cl2shp.py -o tools\saws.shp -c minneapolis -t zip -s "saw"

# URL: http://duluth.craigslist.org/jsonsearch/sss/
# duluth, mankato, fargo, brainerd, bemidji

#  List of near by cities:
#
#     ames
#     appleton
#     bemidji
#     brainerd
#     cedar rapids
#     des moines
#     dubuque
#     duluth
#     eau claire
#     fargo
#     fort dodge
#     grand forks
#     green bay
#     iowa city
#     janesville
#     la crosse
#     madison
#     mankato
#     mason city
#     minneapolis
#     northeast sd
#     northern wi
#     quad cities
#     rochester
#     sioux city
#     sioux falls
#     southwest mn
#     st cloud
#     waterloo
#     wausau 





import sys,requests,itertools,simplejson as json,os,urllib
from optparse import OptionParser
import arcpy

# The OptionParser gives us an easy way to handle command-line options
parser = OptionParser()
parser.add_option('-o','--output',dest='shapefile',help="Required: Where to write the shapefile")
parser.add_option('-c','--cities',dest="cities",help="Required: Comma separated list of CraigsList cities to use search")
parser.add_option('-t','--type',dest='type',help="Which CraigsList section to search. Defaults to sss (For Sale)",default='sss')
parser.add_option('-s','--search',dest='search',help="Search string",default="")

# Parse out the arguments
(options,args) = parser.parse_args()

# No required args given, print an error message
if options.shapefile == None or options.cities == None:
    parser.print_help()
    exit(-1)

# Get the full file path to the shapefile
options.shapefile = os.path.realpath(options.shapefile)

# Split the cities (which were a comma separated list) into an array
options.cities = options.cities.split(',')

# http://minneapolis.craigslist.org/jsonsearch/cta/?query=chevy+truck
baseurl = '.craigslist.org/jsonsearch/'+options.type+'/'

# I copied these headers from a request made in Firefox
http_header = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux i686 on x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
            'Accept' : 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language' : 'en-us,en;q=0.8,pt-br;q=0.6,pt;q=0.4,es;q=0.2',
            'Accept-Encoding' : 'gzip, deflate',
            'X-Requested-With' : 'XMLHttpRequest',
            'Connection' : 'keep-alive',
            'Cache-Control' : 'max-age=0',
        }

# Probably don't need these 
# 'If-Modified-Since' : 'Wed, 16 Apr 2014 03:53:02 GMT',
# 'Referer' : 'http://minneapolis.craigslist.org/sss/',
# 'Host' : 'minneapolis.craigslist.org',

# Do we need to eat a cookie first? 
# 'Cookie' : 'cl_b=nL0AEhvF4xG9arVAc63RngBt1Go; cl_img=bbb%3Alist%2Cggg%3Alist%2Csss%3Agrid%2Cppp%3Agrid%2Cjjj%3Alist%2Chhh%3Alist%2Cccc%3Alist%2Cres%3Agrid; cl_def_lang=en; cl_def_hp=minneapolis; cl_tocmode=sss%3Amap; cl_map=-93.70947360992432%2C45.10054784892533%2C-93.64750385284424%2C45.11802390606867',

lookup_queue = []

for city in options.cities: 
    lookup_queue.append('http://' + city + baseurl + '?query=' + urllib.quote(options.search))

# Make the output directory
destdir = os.path.dirname(options.shapefile)
try: 
    os.makedirs(destdir)
except:
    if os.path.isdir(destdir):
        pass
    else:
        raise

filename = os.path.basename(options.shapefile)
filename_no_suffix = filename.replace('.shp','')

# Set up options for shapefile arguments
opts = {
        'out_path': os.path.dirname(options.shapefile),
        'out_name': os.path.basename(options.shapefile),
        'geometry_type':'POINT',
        'spatial_reference': 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
        }

# Create an empty shapefile
fc = arcpy.CreateFeatureclass_management(**opts)

# Different CraigsList results have different fields. We'll add the fields
# to the shapefile as we find them. This array is to keep track of which
# ones we've already seen. We add Lat/Long already because we don't want
# to add those to the attribute fields
excludedFields = ['Latitude','Longitude']
knownFields = []


# Process each URL lookup in the queue. 
# 
# Results will be a JSON array with a mix of points and clusters.
# Points go into the shapefile. Clusters go into the queue
# NOTE: This means our queue will contract and expand as we process

pointCounter = 0
while len(lookup_queue) > 0:
    url = lookup_queue.pop(0)

    if(len(lookup_queue) % 10 == 0):
        print "There are " + str(len(lookup_queue)) + " URLs left in the queue"

    r = requests.get(url,headers=http_header)
    if (r.status_code != 200):
        print "NON 200 HTTP Status Detected! Bailing out!"
        print r
        exit()
    rawpoints = json.loads(r.text)
    #rawpoints = json.loads('[[{"Longitude":-92.673516,"PostingURL":"/wsh/gms/4458685875.html","Ask":"","PostingID":"4458685875","CategoryID":"73","Latitude":45.00085,"PostingTitle":"Huge Barn Sale 965 County Road A - May 24 -26","PostedDate":"1400023838"},{"Longitude":-93.15801,"PostingURL":"/ram/zip/4461977531.html","Ask":"0","ImageThumb":"http://images.craigslist.org/00909_hsF7jCw8uML_50x50c.jpg","PostingID":"4461977531","CategoryID":"101","Latitude":44.953179,"PostingTitle":"Free burning / Fire wood Pallets and broken crates","PostedDate":"1399649092"},{"Longitude":-93.452968,"PostingURL":"/hnp/zip/4442569391.html","Ask":"0","ImageThumb":"http://images.craigslist.org/00I0I_hVlmEiKBriq_50x50c.jpg","PostingID":"4442569391","CategoryID":"101","Latitude":45.009501,"PostingTitle":"Free Wood, Pallets, Skids, Fire Wood, Etc","PostedDate":"1398909480"},{"Longitude":-93.278732,"PostingURL":"/hnp/for/4421028222.html","Ask":"5","ImageThumb":"http://images.craigslist.org/00V0V_crbxhUWegc_50x50c.jpg","PostingID":"4421028222","CategoryID":"5","Latitude":44.874455,"PostingTitle":"Baby, Its cold outside! Put another log on the fire","PostedDate":"1397414783"}],{"zoom":10,"geocoded":4,"clng":-93.1408069884243,"baseurl":"//minneapolis.craigslist.org","NonGeocoded":0,"clustered":0,"clat":44.9594968434263}]')
    for point in rawpoints[0]:
        if 'GeoCluster' in point:
            # This is a cluster. Request the specified URL to break it apart
            lookup_queue.append('http:' + rawpoints[1]['baseurl'] + point['url'])
        else:
            # Loop through all its fields
            for field in point:
                if field not in knownFields and field not in excludedFields:
                    arcpy.AddField_management(fc,field[0:9],'TEXT')
                    knownFields.append(field)

            # This is a point. Make a new point and set its shape
            inserter = arcpy.InsertCursor(fc)
            newpoint = inserter.newRow()
            newpoint.shape = arcpy.Point(point['Longitude'],point['Latitude'])

            # These URLs are relative. Make them absolute.
            point['PostingURL'] = 'http:' + rawpoints[1]['baseurl'] + point['PostingURL']

            # Add the fields to the point object
            for field in point:
                if field in knownFields:
                    newpoint.setValue(field[0:9],point[field])

            # Add the row we've been working with to the shapefile
            inserter.insertRow(newpoint)
            pointCounter += 1

# Close insert cursor
print "Found " + str(pointCounter) + " points for this Craigslist search!"
