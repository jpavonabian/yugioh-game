## Install dependencies
Lua is needed for ygopro-core. On Ubuntu:
    apt-get install lua5.2-dev

Install Python dependencies:
    pip3 install -r requirements.txt
## Building
ygopro-core and ygopro-scripts must be placed one level up from here.
```
git clone https://github.com/Fluorohydride/ygopro-core
git clone https://github.com/Fluorohydride/ygopro-scripts
cd ygopro-core
patch -p0 < ../yugioh-game/etc/ygopro-core.patch
g++ -shared -fPIC -o ../yugioh-game/libygo.so *.cpp -I/usr/include/lua5.2 -llua5.2 -std=c++11
cd ../yugioh-game
python3 duel_build.py
ln -s ../ygopro-scripts script
```

## Compile language catalogues
This game supports multiple languages (english, spanish, german and japanese right now).
To compile the language catalogues, run the following:
```
./compile.sh de
./compile.sh es
./compile.sh ja
```

To update the plain text files into human-readable format, run the following:
```
./update.sh de
./update.sh es
./update.sh ja
```
The generated files in locale/<language code>/LC_MESSAGES/game.po can be given to translators afterwards.

## Running
```
python3 ygo.py
```
The server will start on port 4000.

## Upgrading

### ygopro-scripts

When upgrading ygopro-scripts, always upgrade ygopro-core with it to prevent crashes. To do so, git pull the repositories cloned earlier and execute the build commands from above again.

### This game

We might change several basic things from time to time, like adding additional c-level helper functions or modify the database layout, so don't forget to run the following commands whenever pulling a major upgrade:
```
python3 duel_build.py
alembic upgrade head
```
Always remember that, even though we try to prevent it, upgrading the database might fail and leave your database in a broken state, so always back it up before proceeding.
