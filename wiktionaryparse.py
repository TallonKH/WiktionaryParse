#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json

# matches to Language titles
title2PT = re.compile('==([^=]+)==')
# matches to section/subsection titles
title34PT = re.compile('====?([^=]+)====?')
# matches plural rule tags for any language - groups the inner contents
plrre = re.compile('{{(\w{2,3}-(?:noun|verb).*)}}')
# matches default plural rule (append s to word)
plrBase = re.compile('\w{2,3}-(?:noun|verb)')
# levels of countability corresponding with indeces 0,1,2
countableTypes = ['No', 'Yes', 'Sometimes']
# split a string into tags {{a|b|c}}
def tagify(s):
	return s[2:-2].split('|')

class WiktionaryParser():
	def __init__(self, inpath, outpath):
		self.__inpath = inpath	# input XML file's path
		self.__outpath = outpath	# output JSON file's path
		self.__maxPageCount = 100	# maximum number of words/pages to save
		# words in these languages should be saved - set empty or None to accept all languages
		self.__targetLangs = {'English'}
		self.__oneLang = len(self.__targetLangs) == 1
		# content in these sections should be saved
		self.__targetSections = {'Noun', 'Verb', 'Adjective'}
		# if info about plurals should be tracked
		self.__trackPlurals = True
		# if the parser is currently running
		self.__running = False
		# if the parser should track info about how much data it has parsed
		self.__trackSelf = True

	def setInPath(path):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__inpath = path
		return True

	def setOutPath(path):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__outpath = path
		return True

	def setMaxPageCount(count):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__maxPageCount = count
		return True

	def setTargetLanguages(*langs):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__targetLangs = set(langs)
		self.__oneLang = len(langs) == 1
		return True

	def setTrackPlurals(track):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__trackPlurals = track
		return True

	# stops the parser before its next iteration
	def forceStop():
		if(self.__running):
			self.__running = False
			return True
		else:
			print('Can\'t stop if not running!')
			return False

	def parse(self):
		# prevent stupidity
		if(self.__running):
			print('Failed to run. This parser is already running!')
			return None
		self.__running = True

		inf = open(self.__inpath, 'r')

		pageCount = 0	# number of saved pages
		pages = dict()	# holds all pages - one page per word
		page = dict()	# holds the current page being parsed/created

		hasContent = False	# if current page has any content that should be saved
		currentWord = None	# the actual word as a string

		# HEIRARCHY: word/page > language > section > contents
		currentLang = None	# dict of a language's sections
		currentLangName = None	# name of the current language
		currentSection = None	# dict of a section's contents
		currentSectionName = None	# name of the current section

		# bool - rules have been found in the current section
		foundPlurals = False

		# bool - the whole page should be skipped
		skipPage = False
		# bool - the whole language should be skipped
		skipLang = False
		# bool - the whole section should be skipped
		skipSection = False

		linesRead = 0
		bytesRead = 0

		while (pageCount < self.__maxPageCount):
			if(not self.__running):
				print('Stopping forcefully...')
				break
			line = inf.readline()

			if(self.__trackSelf):
				linesRead += 1
				bytesRead += len(line.decode('utf8'))

			# if line is empty, end of file has been reached
			if(not line):
				print('Reached end of file.')
				break

			line = line.strip()
			# if stripped line is empty, it's just an empty line
			if(line):
				# lines with XML formatting only contain relevant information in -
				# specific cases, which are contained in this IF
				if(line[0] == '<'):
					# if a word's page has ended, just assume there's another page after it
					if(line == '</page>'):
						# only save pages/words that have desired information
						if(hasContent):
							# add word data to the compiled list
							pages[currentWord] = page
							pageCount += 1

						# reset some variables
						hasContent = False
						currentLang = None
						currentLangName = None
						currentName = None
						currentSection = None
						currentSectionName = None
						foundPlurals = False
						skipPage = False
						skipLang = False
						skipSection = False

						# next line contains the start of the next page,
						# which we'll assume will always be there
						nxt = inf.readline()

						# on the off chance (1 in >6 million) that this is the last page...
						if(nxt.strip() != '<page>'):
							print('Reached end of file.')
							break

						# the next next line contains the word inside a <title> tag
						# extract the word from the <title> tags
						currentWord = inf.readline()[11:-9]

						# skip meta pages
						if(':' in currentWord):
							skipPage = True
							continue

						# set up the next word's page
						page = dict()
						continue

					# sometimes, important content leaks onto the back of this xml line;
					# scrap the line, save the, content, and proceed with it
					elif(line.startswith('<text xml:space="preserve">')):
						line = line[27:]
						#... unless there isn't actually content
						if(not line):
							continue

				# skip the whole page
				if(skipPage):
					continue

				# if lang ended
				if(line == '----'):
					currentLang = None
					currentLangName = None
					continue

				# skip the whole language
				if(skipLang):
					continue

				# if not currently in a language section, check to see if a new one started
				if(currentLangName == None):
					# check if this is a language title
					match = title2PT.match(line)
					if(match):
						# if it is a language title, extract the language
						lang = match.group(1)
						# check if this language is desired
						if((not self.__targetLangs) or (lang in self.__targetLangs)):
							currentLangName = lang
							# if there's only one language, skip creating a -
							# lang section and enter info right into the page dict.
							# This is a really sketchy way to do this, but it's efficient and it works.
							if(self.__oneLang):
								currentLang = page
							else: # otherwise, if there are multiple langs:
								# create a dict for this language's sections
								currentLang = dict()
								# add the language section to the word's page
								page[lang] = currentLang
						else:
							currentLang = None
							currentLangName = None
							# if the language isn't desired, skip it
							skipLang = True
					# if not in a lang, don't bother checking for sections
					continue

				# check if this is a section title
				match = title34PT.match(line)
				if(match):
					# if it is a section title, extract the section type
					section = match.group(1)
					# check if this section is desired
					if((not self.__targetSections) or (section in self.__targetSections)):
						currentSectionName = section
						# create a dict for this section's contents
						currentSection = dict()
						# add the section to the language dict
						currentLang[section] = currentSection
						# flag the page as having desired content
						hasContent = True
					else:
						currentSection = None
						currentSectionName = None
						# if the section isn't desired, skip it
						skipSection = True
					# reset the flag for whether or not plural rules have been found
					foundPlurals = False
					continue

				# if currently in a specific section...
				if(currentSectionName == 'Noun'):
					# check for plural rules if necessary
					# currently locked to English only... other languages have different plural rules.
					if(self.__trackPlurals and not foundPlurals and currentLangName == 'English'):
						# try to match the plural rules line
						match = plrre.match(line)
						if(match):
							# if plural rules line is found, extract the tags
							plurtags = tagify(match.group(0))
							numPlurTags = len(plurtags)

							# converts plural notation to actual plural words
							solvedPlurs = []

							# is word countable?
							# 0: no, 1: yes, 2: maybe
							countable = 0
							 # default rule en-noun - add an s
							if(numPlurTags == 1):
								countable = 1
								solvedPlurs.append(currentWord + 's')
							else:
								# remove the ISO-noun tag
								plurtags.pop(0)
								numPlurTags -= 1
								for i in range(numPlurTags):
									rule = plurtags[i]
									if(rule == 's'):
										solvedPlurs.append(currentWord + 's')
										# do not change if countable = sometimes
										if(countable == 0):
											countable = 1
									elif(rule == 'es'):
										solvedPlurs.append(currentWord + 'es')
										# do not change if countable = sometimes
										if(countable == 0):
											countable = 1
									elif(rule == '~'): # sometimes countable
										countable = 2
										# if ~ is the only tag, assume plural is +s
										if(numPlurTags == 1):
											solvedPlurs.append(currentWord + 's')
									elif(rule == '-'): # non-countable or rarely countable
										if(countable == 1):
											countable = 2
									else:
										# do not change if countable = sometimes
										if(countable == 0):
											countable = 1
										solvedPlurs.append(rule)

							currentSection['countable'] = countableTypes[countable]

							# solvedPlurs will be falsy if a - causes it to be None
							if(solvedPlurs):
								currentSection['plural'] = solvedPlurs
							continue
				elif(currentSectionName == 'Verb'):
					pass
				elif(currentSectionName == 'Adjective'):
					pass
		inf.close()

		js = json.dumps(pages)
		outf = open(self.__outpath, 'w')
		outf.write(js)
		outf.close()

		print('Finished with ' + str(len(pages)) + ' words.')
		if(self.__trackSelf):
			print('Parsed ' + str(linesRead) + ' pages.')
			print('Turned ' + str(bytesRead) + ' bytes into ' + str(len(js.decode('utf8'))) + '.')

		return js

#TODO maybe check the API to update existing words in the JSON

def example():
	parser = WiktionaryParser('/Users/default/Documents/Wikiparse/wiktionary.xml', '/Users/default/Documents/Wikiparse/parsed.json')
	parser.maxPageCount = 100
	parser.parse()

example()