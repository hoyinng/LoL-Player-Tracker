# LoL-Player-Tracker

### What this program do

LoL-Player-Tracker return a list of all the teammate and opposing players a player encountered in the past.
 
LoL-Player-Tracker takes in an in-game name & region and compute a text file containing informations of the players that the player have played with and other relevant informations.

All match history retrieve will be saved in local disk.

Only public matches with MatchHistory V2 system can be retrieved.

# Running the program
```
$ python -V
Python 3.6.0

$ python 1.py -h
usage: 1.py [options]

optional arguments:
  -h, --help            show this help message and exit
  -name  [ ...], --name  [ ...]
                        A summoner name ex: A cute cat irl
  -region region, --region region
                        A region id ['NA1', 'OC1', 'OC', 'NA', 'KR', 'EUW',
                        'EUW1', 'EUNE', 'EUNE1']
  --json, -json         Dump json file after a search

$ python 1.py -name apple -region OC1 
Summoner Name : apple
Summoner ID :208418589, Platform ID: NA1
Match History Loaded: True
New match found: False
There are 52 matches
Loading match history ...
Processing data ...
Writing results\NA1\apple.txt
...

```

LoL-Player-Tracker is not affiliated with Riot Games, this is a personal project.

