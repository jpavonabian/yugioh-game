import gettext
import locale

from .channels.tell import Tell
from .constants import *
from . import globals
from .deck_editor import DeckEditor
from .i18n import set_language as i18n_set_language
from .parsers.duel_parser import DuelParser
from .parsers.lobby_parser import LobbyParser
from .parsers.room_parser import RoomParser
from . import models

class Player:

	def __init__(self, name):
		self._ = gettext.NullTranslations().gettext
		self.afk = False
		self.card_list = []
		self.challenge = True
		self.chat = True
		self.connection = None
		self.deck = {'cards': []}
		self.deck_editor = DeckEditor(self)
		self.duel = None
		self.ignores = set()
		self.is_admin = False
		self.language = 'en'
		self.nickname = name
		self.paused_parser = None
		self.room = None
		self.reply_to = ""
		self.say = True
		self.seen_waiting = None
		self.soundpack = False
		self.tell = Tell()
		self.watch = True
		self.watching = False
		self.tell.add_recipient(self)

	def set_language(self, lang):
		i18n_set_language(self, lang)
		self.get_account().language = self.language
		self.connection.session.commit()

	def attach_connection(self, connection):
		self.connection = connection

	def detach_connection(self):
		self.connection = None

	def notify(self, *args, **kwargs):

		if self.connection:
			self.connection.notify(*args, **kwargs)

	def count_deck_cards(self, deck = None):
		if deck is None:
			deck = self.deck['cards']
		rows = globals.server.db.execute('select id, type from datas where id in (%s)'%(','.join([str(c) for c in set(deck)])))
		main = 0
		extra = 0
		for row in rows:
			if row[1]&(TYPE_XYZ | TYPE_SYNCHRO | TYPE_FUSION | TYPE_LINK):
				extra += deck.count(row[0])
			else:
				main += deck.count(row[0])

		return (main, extra)

	def get_invalid_cards_in_deck(self, deck=None):

		if deck is None:
			deck = self.deck['cards']

		return set([c for c in deck if c not in globals.server.all_cards])

	def set_parser(self, p):
		p=p.lower()
		if p == 'lobbyparser':
			self.connection.parser = LobbyParser
		elif p == 'duelparser':
			self.connection.parser = DuelParser
		elif p == 'roomparser':
			self.connection.parser = RoomParser

	def __del__(self):
		self.tell.remove_recipient(self)

	def get_account(self, session = None):
		if session is None:
			if self.connection is None:
				session = globals.server.session_factory()
			else:
				session = self.connection.session
		return session.query(models.Account).filter_by(name=self.nickname).first()

	def __statistics(self, player, win = 0, lose = 0, draw = 0, giveup = 0):
		if self.connection is not None:
			session = self.connection.session
		elif player.connection is not None:
			session = player.connection.session
		else:
			return
		me = self.get_account(session)
		op = player.get_account(session)
		try:
			stat = [s for s in me.statistics if s.account_id == me.id and s.opponent_id == op.id][0]
		except IndexError:
			stat = models.Statistics(account_id = me.id, opponent_id = op.id)
			stat.win = 0
			stat.lose = 0
			stat.draw = 0
			stat.giveup = 0
			session.add(stat)
		stat.win += win
		stat.lose += lose
		stat.draw += draw
		stat.giveup += giveup
		session.commit()

	def win_against(self, player):
		return self.__statistics(player, win = 1)

	def lose_against(self, player):
		return self.__statistics(player, lose = 1)

	def draw_against(self, player):
		return self.__statistics(player, draw = 1)

	def giveup_against(self, player):
		return self.__statistics(player, giveup = 1)

	def get_locale(self):
		return locale.normalize(self.language).split('_')[0]
