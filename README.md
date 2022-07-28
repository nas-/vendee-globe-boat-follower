# vendee-globe-boat-follower
Does its best to get data for vendee globe boats from marinetraffic

For the first run, you need to fill the config.py file with the marinetraffic links to each of the boats.

Zoom in, a single boat should be visible.

The bot will then go to that link and hopefully get the boat data.

In the following runs, it will first scan a large area.

Then for each BOAT_A, predicts where it should be based on the speed and heading for the previous position, assuming it continued straight.

If there is a single boat BOAT_B close to the predicted position, than probably BOAT_A and BOAT_B are the same boat.


If the step above does not succeed, falls back at zooming in the predicted position. If there is a single boat closeby, that's it.

In the final case, it goes to the link that you entered in the config, and tries to see if there is a single entity there.

In the default state, it will run every 10 minutes.

# How to use:
Install Python (duh)

Install requirements : `pip install requirements.txt`

Since marinetraffic is protected by cloudflare, i used cfscrape to bypass it. In the requirements it is stated that you need to have nodejs installed.

So if the program crashes, either install nodejs or launch it with -sel flag, to use the legacy selenium retrieval.


Delete `data.json`

Enter marinetraffic links in `config.py` files. Selenium supports all zooms, the cfscrape one only zoom 6 and zoom 10

Launch `main.py` [-r] [-d] [-sel]

The optional parameters:

-r reads only the urls provided in config, without touching the data stored previously.

-d enables debug logs.

-sel Forces usage of selenium backend.

Script will keep running until stopped (1 run every 10 minutes).


Does not work very well for boats that dont send often AIS signals, and boats that are close together.

If positions, get mixed up, the best is to either clean up the data for that boat in data.json
for example, BOSS is mixed up, delete this "BOSS":[{...},...,{...}] in data.json, enter the link from marinetraffic and restart.
