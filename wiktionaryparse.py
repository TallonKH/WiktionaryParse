#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json

title2PT = re.compile('==([^=]+)==')
title34PT = re.compile('====?([^=]+)====?')
plrre = re.compile('{{(\w{2,3}-(?:noun|verb).*)}}')

# split a string into tags {{a|b|c}}
def tagify(s):
	return s[2:-2].split('|')

class WiktionaryParser():
	def __init__(self, inpath, outpath):
		self.inpath = inpath
		self.outpath = outpath
		self.maxPageCount = 25
		self.targetLangs = {'English'}
		self.targetSections = {'Noun', 'Verb', 'Adjective'}
		self.trackPlurals = True
		self.solvePlurals = True

	def parse(self):
		inf = open(self.inpath, 'r')

		pageCount = 0
		pages = dict()
		page = dict()

		hasContent = False
		currentWord = None
		currentLang = None
		currentSection = None
		currentSectionName = None

		foundPlurals = False

		skipPage = False
		skipLang = False
		skipSection = False

		while pageCount < self.maxPageCount:
			line = inf.readline()
			if(not line):
				print('Reached end of file.')
				break
			line = line.strip()
			if(line):
				if(line[0] == '<'):
					# if page ended
					if(line == '</page>'):
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

						# overnext line contains word inside <title>
						inf.readline()
						currentWord = inf.readline()[11:-9]
						# skip meta pages
						if(':' in currentWord):
							skipPage = True
							continue

						page = dict()
						continue
					elif(line.startswith('<text xml:space="preserve">')):
						line = line[27:]

				if(skipPage):
					continue

				# if lang ended
				if(line == '----'):
					currentLang = None
					continue

				if(skipLang):
					continue

				# check for new lang beginning
				# compare None because 'not currentLang' would match empty sets too
				if(currentLang == None):
					match = title2PT.match(line)
					if(match):
						lang = match.group(1)
						if((not self.targetLangs) or (lang in self.targetLangs)):
							currentLang = dict()
							page[lang] = currentLang
						else:
							currentLang = None
							skipLang = True
					# if not in a lang, skip checking for sections/subsections
					continue

				# check for new section
				match = title34PT.match(line)
				if(match):
					section = match.group(1)
					if((not self.targetSections) or (section in self.targetSections)):
						currentSection = dict()
						currentSectionName = section
						currentLang[section] = section
						hasContent = True
					else:
						currentSection = None
						currentSectionName = None
						skipSection = True
					foundPlurals = False
					continue

				# if currently in specific section
				if(currentSectionName == 'Noun'):
					if(self.trackPlurals and not foundPlurals):
						match = plrre.match(line)
						if(match):
							plurtags = tagify(match.group(0))
							if(self.solvePlurals):
								print(currentWord, plurtags)
							else:
								print(currentWord, plurtags)
						else:
							# it's a different type of {{...}} tag
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
	parser.parse()

example()