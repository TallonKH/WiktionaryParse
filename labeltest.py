groupOpeners = {'{{':1,'[[':2}
groupClosers = {'}}':1,']]':2}
def formatTerm(term):
	termlen = len(term)
	if(termlen < 5):
		return term
	result = ''
	lastStart = 0
	i = 0
	while i < termlen:
		char = term[i]
		pair = term[i:i+2]

		groupType = groupOpeners.get(pair, None)
		if(groupType):
			# add current running string to result
			result += term[lastStart:i]

			# look for the end of the section
			i2 = i+2
			searchDepth = 1
			while i2 < termlen:
				pair2 = term[i2:i2+2]

				if(pair2 in groupOpeners):
					searchDepth += 1
					i2+=2
				elif(pair2 in groupClosers):
					searchDepth -= 1
					i2+=2
				else:
					i2+=1
				if(searchDepth == 0):
					break

			result += formatTerm(term[i+2:i2-2])
			# move lastStart to the end of the section
			i = i2
			lastStart = i
		else:
			# keep going
			i+=1
	# add on remainder of string
	result += term[lastStart:]
	return result

print(formatTerm('a{{b}}{{c}}{{d{{e{{{{f}}}}}}}}'))

def altf(labs,tags,defi):
	tags.append('alt form')
	return 'Alternate form of ' + labs[1]
def idia(labs,tags,defi):
	tags.append('dialect')
	return 'Eye dialect of ' + labs[1]
def alts(labs,tags,defi):
	tags.append('alt spelling')
	return 'Alternative spelling of ' + labs[1]
def misp(labs,tags,defi):
	tags.append('mispelling')
	return 'Misspelling of ' + labs[1]
def inio(labs,tags,defi):
	tags.append('initialism')
	return 'Initialism of ' + labs[1]
def plur(labs,tags,defi):
	tags.append('plural')
	return 'Plural of ' + labs[1]
def prpo(labs,tags,defi):
	tags.append('participle')
	tags.append('present')
	return 'Present participle of ' + labs[1]
def ncmp(labs,tags,defi):
	tags.append('comparative')
	return 'Comparative of ' + labs[1]
def abbv(labs,tags,defi):
	tags.append('abbreviation')
	return 'Abreviaton of ' + labs[1]
def ntps(labs,tags,defi):
	tags.append('third-person')
	tags.append('singular')
	return 'Third-person singular of ' + labs[1]
def arch(labs,tags,defi):
	tags.append('archaic')
	tags.append('alt spelling')
	return 'Archaic alternative spelling of ' + labs[1]
def ngls(labs,tags,defi):
	tags.append('non-gloss')
	return prelabels[1] + ' ' + defi
def obsf(labs,tags,defi):
	tags.append('obsolete')
	tags.append('alt form')
	return 'Obsolete form of ' + labs[1]
def taxl(labs,tags,defi):
	tags.append(labs[2])
	return 'Of the ' + labs[2] + ' ' + labs[1]
def srnm(labs,tags,defi):
	tags.append('surname')
	return 'surname'
def gvnm(labs,tags,defi):
	tags.append('')
	for lb in labs[2:]:
		if(lb.startswith('or=')):
			tags.append('male')
			tags.append('female')
			return 'Given name (male or female)'
	tags.append(labs[1])
	return 'Given name (' + labs[1] + ')'
	tags.append('given name')
def hgvn(labs,tags,defi):
	tags.append('given name')
	tags.append('historic')
	return 'Historic given name, used by ' + labs[2]
def infl(labs,tags,defi):
	#TODO F1X
	tags.append('inflection')
	return 'Inflection of ' + labs[1]
def snsd(labs,tags,defi):
	tags.append('')
	return '{{SENSE ID - WIP}}'
def npst(labs,tags,defi):
	tags.append('')
	return ' of ' + labs[1]


defTags = {
'alternate form of':altf,
'eye dialect of':idia,
'alternative spelling of':alts,
'misspelling of':misp,
'initialism of':inio,
'plural of':plur,
'present participle of':prpo,
'en-comparative of':ncmp,
'abbreviation of':abbv,
'en-third-person singular of':ntps,
'archaic spelling of':arch,
'non-gloss definition':ngls,
'n-g':ngls,
'obsolete form of':obsf,
'taxlink':taxl,
'surname':srnm,
'given name':gvnm,
'historical given name':hgvn,
'inflection of':infl,
'senseid':snsd,
'rfv-sense':snsd,
'en-past of':npst,
'en-simple past of':npst,
}