cl2shp
======
Search CraigsList and turn the results into a ShapeFile. 

This tool can search multiple sites at once. This could be handy when you're 
wanting to buy something that's worth traveling for. I came up with the idea
when I was truck shopping. I was willing to drive a couple hours to buy a truck, 
which meant searching multiple cities over and over. 

Usage
-----

     python.exe cl2shp.py -o output.shp -c list,of,cities [-t type] -s "search terms"

-c list of CraigsList cities must be comma separated with no spaces
     
-t type is optional and is the 3-letter CraigsList category type. It defaults to sss (for sale). 

Some common types include:

 * sss -- for sale
 * zip -- free
 * cta -- cars and trucks
     
Sample Commands
---------------
     
Search minneapolis, duluth and brainerd for 'dodge ram 1500'

     python.exe cl2shp.py -o truck\truck.shp -c minneapolis,duluth,brainerd -s "dodge ram 1500"
     
Search for free saws in minneapolis

     python.exe cl2shp.py -o tools\saws.shp -c minneapolis -t zip -s "saw"

Notes 
-----
Requires arcpy,request,simplejson and urllib

