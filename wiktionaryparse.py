#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import collections as cl

# matches to Language titles
title2PT = re.compile('==([^=]+)==')
# matches to section/subsection titles
title3pPT = re.compile('={3,}([^=]+)={3,}?')
# matches plural rule labels for any language - groups the inner contents
plrre = re.compile('{{([a-z]{2,3}-(?:noun|verb).*)}}')
# matches definitions - extracts first set of labels and definition
defre1 = re.compile('#+? (?:{{lb\|[a-z]{2,3}\|(?P<labels>.+?)}} ?)?(?P<def>.+)')
# matches definitions - extracts pre/post labels and definition
defre2 = re.compile('^(?:{{(?P<prelabels>.+?)}} ?)?(?P<def>[^{]*)(?:{{(?P<postlabels>.+)}})?')
# levels of countability corresponding with indeces 0,1,2
countableTypes = ['No', 'Yes', 'Sometimes', 'Unknown']
partsOfSpeech = {'Adjective', 'Adverb', 'Ambiposition', 'Article', 'Circumposition',
	'Classifier', 'Conjunction', 'Contraction', 'Counter', 'Determiner', 'Ideophone',
	'Interjection', 'Noun', 'Numeral', 'Participle', 'Particle', 'Postposition',
	'Preposition', 'Pronoun', 'Proper noun', 'Verb'}
# split a string into labels {{a|b|c}}
def labelify(s):
	return s[2:-2].split('|')

# eg: {{sometimes|that}}
leadingLabels = {'sometimes', 'stereotypically', 'now', 'usually'}
# eg: {{chiefly|UK|Australia}}
listLabels = {'chiefly'}

# formats labels properly
def handleLabels(l):
	newLabels = []
	labels = [removeFormatting(lab) for lab in l.split('|')]

	currentList = None
	currentListTitle = None

	i = 0
	count = len(labels)

	while i < count:
		lab = labels[i]
		if(lab in leadingLabels):
			if(currentListTitle):
				newLabels.append(currentListTitle + ', '.join(currentList))
				currentListTitle = None
			if(i == count-1):
				print('Leading label error @ line: ' + l)
			newLabels.append(lab + ' ' + labels[i+1])
			i+=2
			continue

		if(lab == '_'):
			if(currentListTitle):
				newLabels.append(currentListTitle + ', '.join(currentList))
				currentListTitle = None
			if(i == count-1):
				print('Combining label error (after) @ line: ' + l)

			prev = None
			if(len(newLabels) == 0):
				print('Combining label error (before) @ line: ' + l)
				prev = ''
			else:
				prev = newLabels.pop()
			newLabels.append(prev + ' ' + labels[i+1])
			i+=2
			continue

		if(lab in listLabels):
			if(currentListTitle):
				newLabels.append(currentListTitle + ', '.join(currentList))
			currentListTitle = lab + ': '
			currentList = list()
			i+=1
			continue


		if(currentListTitle):
			currentList.append(lab)
			i+=1
			continue

		newLabels.append(lab)
		i+=1

	if(currentListTitle):
		newLabels.append(currentListTitle + ', '.join(currentList))

	return newLabels

# remove bolded / linked words
# should probably make this more efficient later
stops = set(',.; -~/()|#')

def removeFormatting(w):
 	w = w.replace('[[','').replace(']]','').replace('\'\'\'','').replace('\'\'','')
	w2 = ''
	# remove pairs apple|Apple by picking first
	rem = False
	for c in w:
		if(rem):
			if(c in stops):
				w2 += c
				rem = False
			continue
		if(c == '|' or c == '#'):
			rem = True
			continue
		w2 += c
	return w2


# formats a definition properly - returns (formatted def, tags to add)
def cleanDef(d):
	match = defre2.match(d)
	defi = removeFormatting(match.group('def'))
	prelabels = match.group('prelabels')
	postlabels = match.group('postlabels')

	# deal with prelabel-specific definitions
	if(prelabels):
		prelabels = prelabels.split('|')
		# remove formatting on prelabels
		for i in range(1,len(prelabels)):
			prelabels[i] = removeFormatting(prelabels[i])

		# first label - defines label type
		f = prelabels[0]
		if(f == 'alternative form of'):
			return ('Alternate form of ' + prelabels[1], 'alt form')
		if(f == 'alternative spelling of'):
			return ('Alternate spelling of ' + prelabels[1],'alt spelling')
		if(f == 'misspelling of'):
			return ('Misspelling of ' + prelabels[1],'misspelling')
		if(f == 'initialism of'):
			return ('Initialism of ' + prelabels[1],'initialism')
		if(f == 'present participle of'):
			return ('Present participle of ' + prelabels[1], 'present participle')
		if(f == 'en-comparative of'):
			return ('Comparative of ' + prelabels[1], 'comparative')
		if(f == 'abbreviation of'):
			return ('Abbreviation of ' + prelabels[1], 'abbreviation')
		if(f == 'non-gloss definition'):
			return (prelabels[1] + ' ' + defi, 'non-gloss')
		if(f == 'inflection of'):
			# TODO handle inflections properly
			'''
			return ['first','second','third'][d[3]] +
		 		'-person ' +
				{'s':'singular'}[d[4]] + ' ' +
				{'indc':'indicative', 'subj':'subjunctive', 'impr':'imperative'}[d[6]] + ' ' +
			'''
			return ('Inflection of ' + prelabels[1],'inflection')
		if(f == 'senseid'):
			# TODO deal with this
			# senseid requires poselabel 'qualifier'
			# senseid sometimes refers to Wikidata Q#### code, sometimes to word(s)
			# return prelabels[2] + postlabels
			return (defi,)
		if(f == 'en-past of' or f == 'en-simple past of'):
			return ('Past form of ' + prelabels[1],)
		return (d,)
		# if(f == )
	return (defi,)





class WiktionaryParser():
	def __init__(self, inpath, outpath):
		self.__inpath = inpath	# input XML file's path
		self.__outpath = outpath	# output JSON file's path
		self.__maxPageCount = 100	# maximum number of words/pages to save
		# words in these languages should be saved - set empty or None to accept all languages
		self.__targetLangs = {'English'}
		self.__oneLang = len(self.__targetLangs) == 1
		# content in these sections should be saved
		self.__targetSections = set(partsOfSpeech)
		self.__oneSect = len(self.__targetSections) == 1
		# if info about plurals should be tracked
		self.__trackPlurals = True
		# if definitions should be tracked
		self.__trackDefinitions = True
		# if definition labels should be tracked
		self.__trackDefLabels = True
		# if parser is currently running
		self.__running = False
		# if parser should track info about how much data it has parsed
		self.__trackSelf = True
		# if parser should make a list of words and nothing else
		self.__wordsOnly = False
		self.__skipLines = 0

	def getSkipLines(self):
		return 0

	def setSkipLines(self, num):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__skipLines = num
		return True

	def getInPath(self):
		return self.__inpath

	def setInPath(self, path):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__inpath = path
		return True

	def setOutPath(self, path):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__outpath = path
		return True

	def getOutPath(self):
		return self.__outpath

	def getMaxPageCount(self):
		return self.__maxPageCount

	def setMaxPageCount(self, count):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__maxPageCount = count
		return True

	def getTargetLanguages(self):
		return set(self.__targetLangs)

	def setTargetLanguages(self, *langs):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__targetLangs = set(langs)
		self.__oneLang = len(langs) == 1
		return True

	def getTargetSections(self):
		return set(self.__targetSections)

	def setTargetSections(self, *sects):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__targetSections = set(sects)
		self.__oneSect = len(sects) == 1
		return True

	def isTrackingPlurals(self):
		return self.__trackPlurals

	def setTrackPlurals(self, track):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__trackPlurals = track
		return True

	def isTrackingDefinition(self):
		return self.__trackDefinitions

	def setTrackDefinitions(self, track):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__trackDefinitions = track
		return True

	def isTrackingDefLabels(self):
		return self.__trackDefLabels

	def setTrackDefLabels(self, track):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__trackDefLabels = track
		return True

	def isGettingWordsOnly(self):
		return self.__wordsOnly

	def setWordsOnly(self, w):
		if(self.__running):
			print('Cannot change settings while running!')
			return None
		self.__wordsOnly = w
		return True

	# stops the parser before its next iteration
	def forceStop(self):
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

		# the XML file being read
		inf = None
		try:
			inf = open(self.__inpath, 'r')
		except:
			print('Failed to open input file. Quitting...')
			return None

		for i in range(self.__skipLines):
			inf.readline()

		if(self.__skipLines):
			print('Skipped ' + str(self.__skipLines) + ' lines')

		pageCount = 0	# number of saved pages
		# holds all pages - one page per word
		pages = '' if self.__wordsOnly else cl.OrderedDict()
		page = cl.OrderedDict()	# holds the current page being parsed/created

		hasContent = False	# if current page has any content that should be saved
		currentWord = None	# the actual word as a string

		# HEIRARCHY: word/page (eg: cat) > language (eg: English) > section (eg: Noun) > contents (eg: definitions)
		currentLang = None	# dict of a language's sections
		currentLangName = None	# name of the current language
		currentSection = None	# dict of a section's contents
		currentSectionName = None	# name of the current section
		inPOS = None	# currently in a Part of Speech section
		currentDefs = None

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
							if(self.__wordsOnly):
								pages += currentWord + '\n'
							else:
								pages[currentWord] = page

							pageCount += 1
						# reset some variables
						hasContent = False
						currentLang = None
						currentLangName = None
						currentName = None
						currentSection = None
						currentSectionName = None
						# inPOS = None
						# currentDefs = None
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

						# the next next line contains the word inside a <title>
						# extract the word from the <title> s
						currentWord = inf.readline()[11:-9]

						# skip meta pages
						if(':' in currentWord):
							skipPage = True
							continue

						# set up the next word's page
						if(not self.__wordsOnly):
							page = cl.OrderedDict()

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
							if(self.__wordsOnly):
								continue
							# if there's only one language, skip creating a -
							# lang section and enter info right into the page dict.
							# This is a really sketchy way to do this, but it's efficient and it works.
							if(self.__oneLang):
								currentLang = page
							else: # otherwise, if there are multiple langs:
								# create a dict for this language's sections
								currentLang = cl.OrderedDict()
								# add the language section to the word's page
								page[lang] = currentLang
						else:
							currentLangName = None
							if(self.__wordsOnly):
								continue
							currentLang = None
							# if the language isn't desired, skip it
							skipLang = True
					# if not in a lang, don't bother checking for sections
					continue

				# check if this is a section title
				match = title3pPT.match(line)
				if(match):
					# if it is a section title, extract the section type
					section = match.group(1)
					# check if this section is desired
					if((not self.__targetSections) or (section in self.__targetSections)):
						currentSectionName = section
						if(self.__wordsOnly):
							# if this word has the desired section and we're only-
							# looking for words, then this page is done
							hasContent = True
							skipPage = True
							continue

						if(self.__oneSect):
							currentSection = currentLang
						else:
							# create a dict for this section's contents
							currentSection = cl.OrderedDict()
							# add the section to the language dict
							currentLang[section] = currentSection

						if(self.__trackDefinitions):
							inPOS = section in partsOfSpeech
							# just assume that any part of speech sections have definitions in them
							if(inPOS):
								if('defs' in currentSection):
									currentDefs = currentSection['defs']
								else:
									currentDefs = list()
									currentSection['defs'] = currentDefs
						# flag the page as having desired content
						hasContent = True
					else:
						currentSectionName = None
						if(self.__wordsOnly):
							continue
						currentSection = None
						# if the section isn't desired, skip it
						skipSection = True
					# reset the flag for whether or not plural rules have been found
					foundPlurals = False
					continue

				if(self.__wordsOnly):
					continue

				# grab definitions
				if(currentSectionName and self.__trackDefinitions and inPOS):
					# regex match for definition format {{lb|en|...}} def1
					match = defre1.match(line)
					if(match):
						cleanDefResults = cleanDef(match.group('def'))
						cleanedDef = cleanDefResults[0]

						# cleaned labels being sent to output
						outLabels = list(cleanDefResults[1:])

						labels = match.group('labels')
						if(labels):
							outLabels.extend(handleLabels(labels))

						if(self.__trackDefLabels):
							defLabelCombo = cl.OrderedDict()
							if(outLabels):
								defLabelCombo['labels'] = outLabels
							defLabelCombo['def'] = cleanedDef
							currentDefs.append(defLabelCombo)
						else:
							currentDefs.append(cleanedDef)

				if(currentSectionName == 'Noun'):
					# check for plural rules if necessary
					# currently locked to English only... other languages have different plural rules.
					if(self.__trackPlurals and not foundPlurals and currentLangName == 'English'):
						# try to match the plural rules line
						match = plrre.match(line)
						if(match):
							# if plural rules line is found, extract the labels
							plurlabels = labelify(match.group(0))
							numPlurlabels = len(plurlabels)

							# converts plural notation to actual plural words
							solvedPlurs = []

							# is word countable?
							# 0: no, 1: yes, 2: maybe
							countable = 0
							 # default rule en-noun - add an s
							if(numPlurlabels == 1):
								countable = 1
								solvedPlurs.append(currentWord + 's')
							else:
								# remove the ISO-noun label
								plurlabels.pop(0)
								numPlurlabels -= 1
								for i in range(numPlurlabels):
									rule = plurlabels[i]
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
										# if ~ is the only label, assume plural is +s
										if(numPlurlabels == 1):
											solvedPlurs.append(currentWord + 's')
									elif(rule == '-'): # non-countable or rarely countable
										if(countable == 1):
											countable = 2
									elif(rule == '?'): # unknown plural form
										countable = 3
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

		out = pages[:-1] if self.__wordsOnly else json.dumps(pages)

		try:
			outf = open(self.__outpath, 'w')
			outf.write(out)
			outf.close()
		except:
			print('Failed to write to file.')

		# end stats
		print('Finished with ' + str(len(pages)) + ' words.')
		if(self.__trackSelf):
			print('Parsed ' + str(linesRead) + ' lines.')
			print('Turned ' + str(bytesRead) + ' bytes into ' + str(len(out.decode('utf8'))) + '.')

		return out

def example():
	parser = WiktionaryParser('/Users/default/Documents/Wikiparse/wiktionary.xml', '/Users/default/Documents/Wikiparse/parsed.json')
	parser.setMaxPageCount(17)
	parser.setTargetSections('Noun')
	parser.setWordsOnly(False)
	parser.parse()

example()