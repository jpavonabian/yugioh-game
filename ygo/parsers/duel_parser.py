import gsb
import natsort

from ..constants import *
from ..constants import __
from .. import globals

DuelParser = gsb.Parser(command_substitutions = COMMAND_SUBSTITUTIONS)

@DuelParser.command(names=['h', 'hand'])
def hand(caller):
	pl = caller.connection.player
	pl.duel.show_cards_in_location(pl, pl.duel_player, LOCATION_HAND, pl.watching)

@DuelParser.command(names=['hand2'])
def hand2(caller):

	caller.connection.player.duel.show_cards_in_location(caller.connection.player, 1 - caller.connection.player.duel_player, LOCATION_HAND, True)

@DuelParser.command(names=['tab'])
def tab(caller):
	duel = caller.connection.player.duel
	me = caller.connection.player.duel_player
	if caller.connection.player.watching:
		if duel.tag is True:
			o = caller.connection._("team %s")%(duel.players[me].nickname+", "+duel.tag_players[me].nickname)
		else:
			o = duel.players[me].nickname
		caller.connection.notify(caller.connection._("%s's table:") % o)
		duel.show_table(caller.connection.player, me, True)
	else:
		caller.connection.notify(caller.connection._("Your table:"))
		duel.show_table(caller.connection.player, me)

@DuelParser.command(names=['tab2'])
def tab2(caller):
	duel = caller.connection.player.duel
	me = caller.connection.player.duel_player
	if caller.connection.player.watching:
		if duel.tag is True:
			o = caller.connection._("team %s")%(duel.players[1 - me].nickname+", "+duel.tag_players[1 - me].nickname)
		else:
			o = duel.players[1 - me].nickname
		caller.connection.notify(caller.connection._("%s's table:") % o)
	else:
		caller.connection.notify(caller.connection._("Opponent's table:"))
	duel.show_table(caller.connection.player, 1 - me, True)

@DuelParser.command(names=['grave'])
def grave(caller):
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, caller.connection.player.duel_player, LOCATION_GRAVE)

@DuelParser.command(names=['grave2'])
def grave2(caller):
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, 1 - caller.connection.player.duel_player, LOCATION_GRAVE, True)

@DuelParser.command
def removed(caller):
	if caller.connection.player.watching is True:
		hide = True
	else:
		hide = False
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, caller.connection.player.duel_player, LOCATION_REMOVED, hide)

@DuelParser.command
def removed2(caller):
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, 1 - caller.connection.player.duel_player, LOCATION_REMOVED, True)

@DuelParser.command(names=['extra'])
def extra(caller):
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, caller.connection.player.duel_player, LOCATION_EXTRA, caller.connection.player.watching)

@DuelParser.command(names=['extra2'])
def extra2(caller):
	caller.connection.player.duel.show_cards_in_location(caller.connection.player, 1 - caller.connection.player.duel_player, LOCATION_EXTRA, True)

@DuelParser.command(names=['watchers'])
def show_watchers(caller):
	watchers = [w for w in caller.connection.player.duel.watchers if w.watching is True]
	if len(watchers) == 0:
		caller.connection.notify(caller.connection._("No one is watching this duel."))
	else:
		caller.connection.notify(caller.connection._("People watching this duel:"))
		for pl in natsort.natsorted(watchers, key=lambda x: x.nickname):
			caller.connection.notify(pl.nickname)

@DuelParser.command(names=['info'], args_regexp=r'(.*)')
def info(caller):
	caller.connection.player.duel.show_info_cmd(caller.connection.player, caller.args[0])

@DuelParser.command(names=['giveup'], allowed = lambda c: c.connection.player.watching is False)
def giveup(caller):

	duel = caller.connection.player.duel

	for pl in duel.players+duel.watchers:
		pl.notify(pl._("%s has ended the duel.")%(caller.connection.player.nickname))

	if not duel.private:
		if duel.tag is True:
			op = "team "+duel.players[1 - caller.connection.player.duel_player].nickname+", "+duel.tag_players[1 - caller.connection.player.duel_player].nickname
		else:
			op = duel.players[1 - caller.connection.player.duel_player].nickname
		globals.server.challenge.send_message(None, __("{player1} has cowardly submitted to {player2}."), player1 = caller.connection.player.nickname, player2 = op)

		if not duel.paused:
			for pl in duel.players+duel.tag_players:
				for op in duel.players+duel.tag_players:
					if pl is not op:
						pl.giveup_against(op)

	duel.end()

@DuelParser.command(names=['sc', 'score'])
def score(caller):
	caller.connection.player.duel.show_score(caller.connection.player)

@DuelParser.command(names=['tag'], args_regexp=r'(.*)', allowed = lambda c: c.connection.player in c.connection.player.duel.players or c.connection.player in c.connection.player.duel.tag_players and c.connection.player.duel.tag is True)
def tag(caller):

	if len(caller.args) == 0 or caller.args[0] == '':
		caller.connection.notify(caller.connection._("You need to send some text to this channel."))
		return
	
	caller.connection.player.duel.tags[caller.connection.player.duel_player].send_message(caller.connection.player, caller.args[0])

@DuelParser.command(names=['taghistory'], allowed = lambda c: c.connection.player in c.connection.player.duel.players or c.connection.player in c.connection.player.duel.tag_players and c.connection.player.duel.tag is True)
def taghistory(caller):
	caller.connection.player.duel.tags[caller.connection.player.duel_player].print_history(caller.connection.player)
