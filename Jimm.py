import nltk
import irc.bot
import irc.strings
import threading
import time
import sys
import random
from datetime import datetime

# Shared variables for communication between threads
_SHARED = {
	'owner': "",
	'servers': dict(),
	'nickname': "jimm", 
	'_COMMANDS': [],
	'origin': {
		'server': "",
		'channel': "",
		'key': "",
		'context': None,
	}
}

class Jimm(irc.bot.SingleServerIRCBot):
	def __init__(self, server, channel, key, port):
		self.server = server
		self.channel = channel
		self.key = key
		self.talking_time = {}
		self.talking_time["times_talked"] = 0
		self.talking_time["lines"] = 0

		irc.bot.SingleServerIRCBot.__init__(self, [(server,port)], _SHARED['nickname'], _SHARED['nickname'])

	def on_welcome(self, context, event):
		if _SHARED['origin']['context'] == None:
			_SHARED['origin']['context'] = context
		else:
			_SHARED['servers'][self.server] = dict()
			_SHARED['servers'][self.server]['channels'] = self.channels
			_SHARED['servers'][self.server]['context'] = context
		context.join(self.channel, self.key)

	def on_pubmsg(self, context, event):
		self.do(context, event)

	def on_privmsg(self, context, event):
		self.do(context, event)

	def do(self, context, event):
		self.talking_time["lines"] += 1
		self.understand(context, event)

	def is_owner(self, context, event):
		user = event.source.split("!")[0]
		if user != _SHARED['owner']:
			return False
		return True

	def time_to_talk(self, target, text):
		if self.talking_time["lines"] >= 7 and self.talking_time["times_talked"] < 2:
			self.talking_time["times_talked"] += 1
			self.talking_time["lines"] = 0
			return True

		if self.talking_time["lines"] >= 2 and self.talking_time["times_talked"] >= 2:
			self.talking_time["times_talked"] = 0
			self.talking_time["lines"] = 0
			return True

		if _SHARED['nickname'] in text:
			return True

		return False

	def understand(self, context, event):

		# my_owner = self.is_owner(context, event)
		# if not my_owner:
		#	return False

		#if event.target == _SHARED['origin']['channel'] or (my_owner and event.target == _SHARED['nickname']) or event.target in self.channels.keys():
		#	if my_owner and event.target == _SHARED['nickname']:
		#		event.target = _SHARED['owner']

		try:
			event.target.index(_SHARED['nickname'])
		except ValueError:
			text = event.arguments[0]
			speech = self.think(event.target, text).strip()
			if not self.time_to_talk(event.target, text):
				return False
			if speech != text:
				try:
					context.privmsg(event.target, speech)
				except irc.client.MessageTooLong:
					pass
			return True

		return False

	def think(self, target, text):
		self.learn_sentence(text)
		return self.what_to_say(text)

	def what_to_say(self, text):
		sentence = []
		brains = ["subjects.txt", "verbs.txt", "nouns.txt"]
		i = 0

		for memory in brains:
			sentence.append(self.open_brain(text, memory))

		if sentence:
			text = " ".join(sentence)
		else:
			text = ""

		text = text.replace("\n", "").split(" ")
		text_more_sense = []
		[text_more_sense.append(item) for item in text if item not in text_more_sense]
		text_more_sense = " ".join(text_more_sense)
		text_more_sense = text_more_sense.replace("jimm", "")

		return text_more_sense
	
	def open_brain(self, text, memory):
		words = text.split(" ")
		with open(memory, "r") as brain:
			lines = brain.readlines()
			random.shuffle(lines)
			for word in words:
					for line in lines:
						line = line.replace("jimm","")
						parts = line.split(" ")
						for part in parts:
							if part == "" or part == "\n" or part == " ":
								break

							if word == part:
								return " ".join(parts)
		return ""


	def is_a_subject(self, word):
		if word[1] in ["NNP", "PRP"]:
			return True
		return False

	def is_a_verb(self, word):
		if word[1] in ["VBZ", "VB"]:
			return True
		return False

	def is_a_noun(self, word):
		return False

	def learn(self, filename):
		with open(filename, "r") as external_influence:
			lines = external_influence.readlines()
			for line in lines:
				self.learn_sentence(line)


	def learn_sentence(self, text):
		sentence = {"subject": "", "verb": "", "noun": ""}
		found = {"subject": False, "verb": False, "noun": False}

		words = nltk.pos_tag(nltk.word_tokenize(text))

		for word in words:
			if (not found["subject"]):
				if not self.is_a_subject(word):
					sentence["subject"] += word[0]+" "
				else:
					sentence["subject"] += word[0]+"\n"
					sentence["verb"] += word[0]+" "
					found["subject"] = True

			if (not found["verb"]) and found["subject"]:
				if not self.is_a_verb(word):
					sentence["verb"] += word[0]+" "
				else:
					sentence["verb"] += "\n"
					found["verb"] = True
					continue

			if (not found["noun"]) and found["verb"] and found["subject"]:
				if not self.is_a_noun(word):
					sentence["noun"] += word[0]+" "
				else:
					sentence["noun"] += "\n"
					found["noun"] = True

			if found["noun"] and found["verb"] and found["subject"]:
				if sentence["noun"][-1] != "\n":
					sentence["noun"] += "\n"
				break

		try:
			if sentence["noun"][-1] != "\n":
				sentence["noun"] += "\n"
		except IndexError:
			pass

		with open("subjects.txt", "a") as brain:
			brain.write(sentence["subject"])
		with open("verbs.txt", "a") as brain:
			brain.write(sentence["verb"])
		with open("nouns.txt", "a") as brain:
			brain.write(sentence["noun"])

	def get_args(self, event):
		return event.arguments[0].split(" ")

def main():
	if len(sys.argv) == 2:
		jimm = Jimm("", "", "", 0)
		jimm.learn(sys.argv[1])
		return
	if len(sys.argv) != 4:
		print("Usage: python Jimm.py owner server channel\nNote: bash is a bitch, remember # is comment in bash.")
	_SHARED['owner'] = sys.argv[1];
	_SHARED['origin']['server'] = sys.argv[2]
	_SHARED['origin']['channel'] = sys.argv[3]
	if len(sys.argv) > 4:
		_SHARED['origin']['key'] = sys.argv[4]
	Jimm(_SHARED['origin']['server'], _SHARED['origin']['channel'], _SHARED['origin']['key'], 6667).start()

main()
