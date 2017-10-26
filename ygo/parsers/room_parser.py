import gsb
import json

from ..card import Card
from ..constants import COMMAND_SUBSTITUTIONS, RE_NICKNAME, __
from ..duel import Duel
from .. import globals
from .. import models

class room_parser(gsb.Parser):

	def prompt(self, connection):
		connection.notify(connection._("Enter ? to show all commands and room preferences"))

	def huh(self, caller):
		caller.connection.notify(caller.connection._("This command isn't available right now."))

	def handle_line(self, connection, line):
		super(room_parser, self).handle_line(connection, line)
		if connection.parser is self:
			self.prompt(connection)

	def explain(self, command, connection):
		# we don't want the parser to construct absurd help texts for us
		# but the caller we pass in will probably have very less information available
		c = gsb.Caller(connection, args = [])
		command.func(c)

RoomParser = room_parser(command_substitutions = COMMAND_SUBSTITUTIONS)

@RoomParser.command(names=['?'])
def list(caller):
	pl = caller.connection.player
	room = pl.room

	pl.notify(pl._("The following settings are defined for this room:"))

	pl.notify(pl._("Banlist: %s")%(room.get_banlist()))

	s = pl._("Duel Rules:")+" "

	if room.rules == 4:
		s += pl._("Link")
	elif room.rules == 1:
		s += pl._("Traditional")
	elif room.rules == 0:
		s += pl._("Default")

	pl.notify(s)

	pl.notify(pl._("Lifepoints - %s: %d, %s: %d")%(pl._("team %d")%(1), room.lp[0], pl._("team %d")%(2), room.lp[1]))

	pl.notify(pl._("Privacy: %s")%(pl._("private") if room.private is True else pl._("public")))

	pl.notify(pl._("The following commands are available for you:"))

	if not room.open:
		pl.notify(pl._("banlist - define banlist"))
		pl.notify(pl._("finish - finish room creation and open it to other players"))
		pl.notify(pl._("lifepoints - set lifepoints per team"))
		pl.notify(pl._("private - toggles privacy"))
		pl.notify(pl._("rules - define duel rules"))
		pl.notify(pl._("save - save settings for all your future rooms"))

	if room.open:
		pl.notify(pl._("deck - select a deck to duel with"))
		pl.notify(pl._("move - move yourself into a team of your choice"))
		pl.notify(pl._("teams - show teams and associated players"))

		if room.creator is pl:
			pl.notify(pl._("invite - invite player into this room"))
			pl.notify(pl._("start - start duel with current teams"))

	if room.creator is pl:
		pl.notify(pl._("leave - leave this room and close it"))
	else:
		pl.notify(pl._("leave - leave this room"))

@RoomParser.command(names=['finish'], allowed = lambda c: not c.connection.player.room.open and c.connection.player.room.creator is c.connection.player)
def finish(caller):

	pl = caller.connection.player
	room = pl.room

	room.open = True

	pl.notify(pl._("You finished the room setup."))

	if room.private is True:
		pl.notify(pl._("You can now invite players to join this room."))
	else:
		pl.notify(pl._("Players can now join this room, or you can invite them to join you."))
		globals.server.challenge.send_message(None, __("{player} created a new duel room."), player = pl.nickname)

@RoomParser.command(names=['leave'])
def leave(caller):

	pl = caller.connection.player
	room = pl.room

	room.leave(pl)

@RoomParser.command(names=['banlist'], args_regexp=r'([a-zA-Z0-9\.\- ]+)', allowed = lambda c: not c.connection.player.room.open and c.connection.player.room.creator is c.connection.player)
def banlist(caller):

	pl = caller.connection.player
	room = pl.room

	if len(caller.args) == 0:
		pl.notify(pl._("You can set the banlist to ocg or tcg, which will automatically select the newest tcg/ocg banlist for you."))

		pl.notify(pl._("You can also set the banlist to none or one of the following:"))
		pl.deck_editor.check(None)

	elif len(caller.args) == 1 and caller.args[0] == None:
		pl.notify(pl._("Invalid banlist specified."))
	else:
		success = room.set_banlist(caller.args[0])
		if success is True:
			pl.notify(pl._("The banlist for this room was set to %s.")%(room.get_banlist()))
		else:
			pl.notify(pl._("This game doesn't know this banlist. Check the banlist command to get all possible arguments to this command."))

@RoomParser.command(names=['teams'], allowed = lambda c: c.connection.player.room.open)
def teams(caller):

	pl = caller.connection.player
	room = pl.room

	for i in (1, 2):
		if len(room.teams[i]) == 0:
			pl.notify(pl._("No players in %s.")%(pl._("team %d")%i))
		else:
			pl.notify(pl._("Players in %s: %s")%(pl._("team %d")%i, ', '.join([p.nickname for p in room.teams[i]])))

	if len(room.teams[0]) == 0:
		pl.notify(pl._("No remaining players in this room."))
	else:
		pl.notify(pl._("Players not yet in a team: %s")%(', '.join([p.nickname for p in room.teams[0]])))

@RoomParser.command(names=['move'], args_regexp=r'([0-2])', allowed = lambda c: c.connection.player.room.open)
def move(caller):

	pl = caller.connection.player
	room = pl.room

	if len(caller.args) == 0 or len(caller.args) == 1 and caller.args[0] == None:
		pl.notify(pl._("You can move yourself into team 0, 1 or 2, where 0 means that you remove yourself from any team."))
	else:
		team = int(caller.args[0])
		room.move(pl, team)
		if team == 0:
			for p in room.get_all_players():
				if p is pl:
					pl.notify(pl._("You were removed from any team."))
				else:
					p.notify(p._("%s was removed from any team.") % pl.nickname)
		else:
			for p in room.get_all_players():
				if p is pl:
					pl.notify(pl._("You were moved into %s.")%(pl._("team %d")%(team)))
				else:
					p.notify(p._("%s was moved into %s.")%(pl.nickname, p._("team %d")%(team)))

@RoomParser.command(names=['private'])
def private(caller):

	pl = caller.connection.player
	room = pl.room

	room.private = not room.private

	if room.private is True:
		pl.notify(pl._("This room is now private."))
	else:
		pl.notify(pl._("This room is now public."))

@RoomParser.command(names=['rules'], args_regexp=r'([a-zA-Z]+)', allowed = lambda c: c.connection.player.room.creator is c.connection.player and not c.connection.player.room.open)
def rules(caller):

	pl = caller.connection.player
	room = pl.room

	if len(caller.args) == 0:
		pl.notify(pl._("Following rules can be defined:"))
		pl.notify(pl._("Default - The default duelling behaviour before link summons came in"))
		pl.notify(pl._("Link - Enable link summons"))
		pl.notify(pl._("Traditional - Duel rules from the first days of Yu-Gi-Oh"))
	elif caller.args[0] is None or caller.args[0].lower() not in ('link', 'default', 'traditional'):
		pl.notify(pl._("Invalid duel rules specified. See rules command to get the possible arguments."))
	else:
		rule = caller.args[0].lower()
		if rule == 'link':
			room.rules = 4
		elif rule == 'traditional':
			room.rules = 1
		else:
			room.rules = 0

		s = pl._("Duel rules were set to %s.")

		if room.rules == 0:
			s2 = pl._("Default")
		elif room.rules == 1:
			s2 = pl._("Traditional")
		elif room.rules == 4:
			s2 = pl._("Link")

		s = s%(s2)

		pl.notify(s)

@RoomParser.command(names=['deck'], args_regexp=r'(.+)', allowed = lambda c: c.connection.player.room.open)
def deck(caller):

	pl = caller.connection.player
	room = pl.room

	if len(caller.args) == 0:
		pl.deck_editor.list()
		return

	name = caller.args[0]

	# first the loading algorithm
	# parsing the string, loading from database
	session = caller.connection.session
	account = caller.connection.player.get_account()
	if name.startswith('public/'):
		account = session.query(models.Account).filter_by(name='Public').first()
		name = name[7:]
	deck = models.Deck.find(session, account, name)
	if not deck:
		pl.notify(pl._("Deck doesn't exist."))
		return

	content = json.loads(deck.content)

	# we parsed the deck now we execute several checks

	# we filter all invalid cards first
	invalid_cards = pl.get_invalid_cards_in_deck(content['cards'])
	content['cards'] = [c for c in content['cards'] if c not in invalid_cards]
	if len(invalid_cards):
		con.notify(con._("Invalid cards were removed from this deck. This usually occurs after the server loading a new database which doesn't know those cards anymore."))

	# we check card limits first
	main, extra = pl.count_deck_cards(content['cards'])
	if main < 40 or main > 200:
		pl.notify(pl._("Your main deck must contain between 40 and 200 cards (currently %d).") % main)
		return

	if extra > 15:
		pl.notify(pl._("Your extra deck may not contain more than 15 cards (currently %d).")%extra)
		return

	# check against selected banlist
	if room.get_banlist() != 'none':
		codes = set(content['cards'])
		errors = 0
		for code in codes:
			count = content['cards'].count(code)
			if code not in globals.lflist[room.get_banlist()] or count <= globals.lflist[room.get_banlist()][code]:
				continue
			card = Card(code)
			pl.notify(pl._("%s: limit %d, found %d.") % (card.get_name(pl), globals.lflist[room.get_banlist()][code], count))
			errors += 1

		if errors > 0:
			pl.notify(pl._("Check completed with %d errors.") % errors)
			return

	pl.deck = content
	pl.notify(pl._("Deck loaded with %d cards.") % len(content['cards']))

	for p in room.get_all_players():
		if p is not pl:
			p.notify(p._("%s loaded a deck.")%(pl.nickname))

@RoomParser.command(names=['start'], allowed = lambda c: c.connection.player.room.creator is c.connection.player and c.connection.player.room.open)
def start(caller):

	pl = caller.connection.player
	room = pl.room

	# do we have an equal amount of players in both teams?

	if len(room.teams[1]) != len(room.teams[2]):
		pl.notify(pl._("Both teams must have the same amount of players."))
		return

	if not 0 < len(room.teams[1]) <= 2:
		pl.notify(pl._("Both teams may only have one or two players."))
		return

	# do all players have decks loaded?
	for p in room.teams[1]+room.teams[2]:
		if len(p.deck['cards']) == 0:
			pl.notify(pl._("%s doesn't have a deck loaded yet.")%(p.nickname))
			return

	# is it a tag duel?
	if len(room.teams[1]) > 1:
		room.options = room.options | 0x20

	for p in room.get_all_players():
		if p is pl:
			p.notify(p._("You start the duel."))
		else:
			p.notify(p._("%s starts the duel.")%(pl.nickname))

	# launch the duel
	duel = Duel()
	duel.add_players(room.teams[1]+room.teams[2])
	duel.set_player_info(0, room.lp[0])
	duel.set_player_info(1, room.lp[1])

	if not room.private:
		if duel.tag is True:
			pl0 = "team "+duel.players[0].nickname+", "+duel.tag_players[0].nickname
			pl1 = "team "+duel.players[1].nickname+", "+duel.tag_players[1].nickname
		else:
			pl0 = duel.players[0].nickname
			pl1 = duel.players[1].nickname
		globals.server.challenge.send_message(None, __("The duel between {player1} and {player2} has begun!"), player1 = pl0, player2 = pl1)

	duel.start(((room.rules&0xff)<<16)+(room.options&0xffff))

	duel.private = room.private

	# move all 	players without a team into the duel as watchers
	for p in room.teams[0]:
		duel.add_watcher(p)

	# remove the room from all players
	for p in room.get_all_players():
		p.room.say.remove_recipient(p)
		p.room = None

@RoomParser.command(names=['invite'], args_regexp=RE_NICKNAME, allowed = lambda c: c.connection.player.room.creator is c.connection.player and c.connection.player.room.open)
def invite(caller):

	pl = caller.connection.player
	room = pl.room

	if len(caller.args) == 0:
		pl.notify(pl._("You can invite any player to join this room. Simply type invite <player> to do so."))
		return

	if caller.args[0] is None:
		pl.notify(pl._("No player with this name found."))
		return

	players = globals.server.guess_players(caller.args[0], pl.nickname)

	if len(players) == 0:
		pl.notify(pl._("No player with this name found."))
		return
	elif len(players)>1:
		pl.notify(pl._("Multiple players match this name: %s")%(', '.join([p.nickname for p in players])))
		return

	target = players[0]

	if target.duel is not None:
		pl.notify(pl._("This player is already in a duel."))
		return
	elif target.room is not None:
		pl.notify(pl._("This player is already preparing to duel."))
		return
	elif target.nickname in pl.ignores:
		pl.notify(pl._("You're ignoring this player."))
		return
	elif pl.nickname in target.ignores:
		pl.notify(pl._("This player ignores you."))
		return

	room.add_invitation(target)

	if target.afk is True:
		pl.notify(pl._("%s is AFK and may not be paying attention.")%(target.nickname))

	target.notify(target._("%s invites you to join his duel room. Type join %s to do so.")%(pl.nickname, pl.nickname))

	pl.notify(pl._("An invitation was sent to %s.")%(target.nickname))

@RoomParser.command(names=['lifepoints'], args_regexp=r'([1-2]) (\d+)', allowed = lambda c: c.connection.player.room.creator is c.connection.player and not c.connection.player.room.open)
def lifepoints(caller):

	pl = caller.connection.player
	room = pl.room
	
	if len(caller.args) == 0 or caller.args[0] is None or caller.args[1] is None:
		pl.notify(pl._("Usage: lifepoints <team> <lp>"))
		return
	
	room.lp[int(caller.args[0])-1] = int(caller.args[1])
	
	pl.notify(pl._("Lifepoints for %s set to %d.")%(pl._("team %d")%(int(caller.args[0])), room.lp[int(caller.args[0])-1]))

@RoomParser.command(names=['save'])
def save(caller):

	con = caller.connection
	room = con.player.room
	account = con.player.get_account()
	
	account.banlist = room.banlist
	account.duel_rules = room.rules
	con.session.commit()
	
	con.notify(con._("Settings saved."))
