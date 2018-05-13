# WiktionaryParse

A Python script that uses wiktionary's backup XML files to create a JSON dictionary of words along with info about those words. The desired info can be specified (eg: part of speech, synonyms). Words can be filtered based on specified criteria (eg: English only, Nouns and Verbs only). The goal is to use wiktionary.org to create readable language data without flooding wiktionary's API with requests.

## Status
Far from finished, but functional to the degree specified below.

## Current features:
- Grab up to N words that meet criteria
- Filter words/info by language(s), part(s) of speech
- Retreive an English noun's countability and any plural forms
- Create a simple plaintext list of words without extra info
- Give basic statistics on how many lines/bytes were read
- Extract/format definitions & definition labels
* Basically every feature is optional.

## Planned Features:
- Split output into multiple files by specified criteria
- Sort output by specified criteria
- Retreive definitions
- Retreive synonyms, derived terms, related terms, etc

## Maybe Planned Features:
- Better handling of non-English languages
- Use wiktionary's API to update individual words without re-parsing the entire site

## How to use

1. Download one of wiktionary's backup files. The latest ones are [here](https://dumps.wikimedia.org/enwiktionary/latest/). The one you want is called ```enwiktionary-latest-pages-articles.xml.bz2```. **WARNING:** **This is a big file.** Uncompress the bz2 and put it wherever you want. Keep in mind this makes the already-big file *significantly bigger*.

2. Download the wiktionaryparse.py file. Feel free to edit the ```example()``` method. If you don't want to, you'll have to import wiktionaryparse.py into your own file.
3. Run the .py file in a console however you want. I recommend running it in a console to make sure no errors happen.
4. Once your output file is done, feel free to delete the xml.


```Python3
def example():
	# this creates a parser object, with the input and output file paths respectively
	parser = WiktionaryParser('/input/file.xml', '/output/file.json')

	# this writes to the output file (and returns the json as a string)
	parser.parse()
```

Changing settings:

```Python3
def example():
	parser = WiktionaryParser('/input/file.XML', '/output/file.JSON')

	# this specify the maximum number of words/pages to parse - (default = 100)
	parser.setMaxPageCount(2500)
	# set which languages to save - (leave empty for all languages) (default = 'English')
	parser.setTargetLanguages('English', 'French', 'Arabic')
	# set which sections to save - (leave empty for all sections) (defaults to all parts of speech)
	parser.setTargetSections('Noun', 'Verb', 'Synonyms')
	# sets if the parser should keep plural forms of words (default = True)
	parser.setTrackPlurals(False)

	parser.parse()
```

## Built With

- [Python 3](https://www.python.org/)

## Required Imports

- re (regex)
- JSON (JSON)
- collections (Ordered Dictionaries)

## Author

**Tallon Hodge**

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see [here](https://opensource.org/licenses/MIT) for details. 
WiktionaryParse does not directly contain any copyrighted property; however, its one and only function is to grab info from wiktionary.org. Please see [here](https://en.wiktionary.org/wiki/Wiktionary:Copyrights) for copyright information on any files created by WiktionaryParse.

## Acknowledgments

* The Wikimedia Foundation, for making a frankly ridiculous amount of information available for free.
