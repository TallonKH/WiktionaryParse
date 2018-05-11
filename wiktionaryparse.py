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

# split a string into tags {{a|b|c}}
def tagify(s):
	return s[2:-2].split('|')

class WiktionaryParser():
	def __init__(self, inpath, outpath):
		self.inpath = inpath	# input XML file's path
		self.outpath = outpath	# output JSON file's path
		self.maxPageCount = 25	# maximum number of words/pages to save
		# words in these languages should be saved
		self.targetLangs = {'English'}
		# content in these sections should be saved
		self.targetSections = {'Noun', 'Verb', 'Adjective'}
		# if info about plurals should be tracked
		self.trackPlurals = True
		# if the plurals themselves should be tracked - requires trackPlurals == True
		self.solvePlurals = True

	def parse(self):
		inf = open(self.inpath, 'r')

		pageCount = 0	# number of saved pages
		pages = dict()	# holds all pages - one page per word
		page = dict()	# holds the current page being parsed/created

		hasContent = False	# if current page has any content that should be saved
		currentWord = None	# the actual word as a string

		# HEIRARCHY: word/page > language > section > contents
		currentLang = None	# dict of a language's sections
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

		while pageCount < self.maxPageCount:
			line = inf.readline()

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
					continue

				# skip the whole language
				if(skipLang):
					continue

				# if not currently in a language section, check to see if a new one started
				# compare None because 'not currentLang' would match empty sets too
				if(currentLang == None):
					# check if this is a language title
					match = title2PT.match(line)
					if(match):
						# if it is a language title, extract the language
						lang = match.group(1)
						# check if this language is desired
						if((not self.targetLangs) or (lang in self.targetLangs)):
							# create a dict for this language's sections
							currentLang = dict()
							# add the language section to the word's page
							page[lang] = currentLang
						else:
							currentLang = None
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
					if((not self.targetSections) or (section in self.targetSections)):
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
					if(self.trackPlurals and not foundPlurals):
						# try to match the plural rules line
						match = plrre.match(line)
						if(match):
							# if plural rules line is found, extract the tags
							plurtags = tagify(match.group(0))

							# if specified, replace rules with the pluralized word
							if(self.solvePlurals):
								for i in range(len(plurtags)-1, -1, -1):
									rule = plurtags[i]
									if(rule == 's' or plrBase.match(rule)):
										# default rule ISO-noun - add an s
										plurtags[i] = currentWord + 's'
									elif(rule == 'es'):
										# add an 'es'
										plurtags[i] = currentWord + 'es'
									elif(rule == '~'):
										# TODO figure out how to handle this...
										plurtags.pop(i)
									elif(rule == '-'):
										# non-countable
										plurtags = None
										break

							# plurtags will be falsy if a - causes it to be None
							if(plurtags):
								currentSection['plural'] = plurtags
							continue
						else:
							# it's not a plural rules line...
							pass
				elif(currentSectionName == 'Verb'):
					pass
				elif(currentSectionName == 'Adjective'):
					pass
		inf.close()

		# for word in pages:
		# 	print(word)
		print('Pages:' + str(len(pages)))

		outf = open(self.outpath, 'w')
		outf.write(json.dumps(pages))
		outf.close()

def example():
	parser = WiktionaryParser('/Users/default/Documents/Wikiparse/wiktionary.xml', '/Users/default/Documents/Wikiparse/parsed.json')
	parser.maxPageCount = 100
	parser.parse()

example()