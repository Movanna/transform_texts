# transform_texts
**Python scripts for transforming texts using Beautiful Soup: XML, HTML, EPUB, TXT. Some of the transformation results are part of an API endpoint response. Also some automated Excel reporting of text statistics and data using Pandas and openpyxl.**

**I work with texts** (and [data](https://github.com/Movanna/database_population)). Texts are often seen as uncomplicated: just characters, words and paragraphs in a text document. Everyone knows how to create a text, right? Just open Word and start writing. Then send the file to be published – and the fun begins.

Hardly surprising at this point, my view is that **texts, textual phenomena, books and text formats are rather complex**. A Word document can *look* just perfect, but still be a nightmare for someone who wants to publish the contents online. Wait, getting text from one place or format to another is as simple as anything, isn't it? Well, that's what developers always told me: ”But, clearly, the texts you wanted to appear on the site *are* all there now!”. Yeah, maybe (never be too sure, though), but they certainly looked bad. When the initial result is that the subtitle is larger than the title, the text is cramped, the font is ugly, the italics you were expecting have disappeared, footnotes are gone, and the indentation is all off, then maybe publishing texts isn't necessarily such an easy business.

Of course **CSS** goes hand in hand with this, but you still need to work on the **word processor document/XML/HTML** first in order to get sensible results. Especially in terms of accessibility. And since editors, in the case of this particular project, are dealing with the resulting XML files all day, they don't want to see five irrelevant attributes with endless values on each element, which is what you often get straight out of any conversion. This is why I started transforming texts myself.

Add to this **TEI XML**, [the Text Encoding Initiative](https://tei-c.org/), where all kinds of textual features such as deletions, substitutions, underlining and language usage are meticulously recorded in tags and attributes. Let it simmer with **a web site based on those source files**: [the digital archive Leo Mechelin – Pro lege](https://leomechelin.fi). Stir in **e-books**, add seasoning from [Transkribus Handwritten Text Recognition](https://readcoop.eu/transkribus/), mix with **desktop publishing**, sprinkle with **OCR**, **.odt** and **.docx** and serve it all on a plate from the [Generic Digital Edition Platform](https://github.com/slsfi/digital_edition_documentation/wiki), using its **API**. Don't forget the traditional tasty side dishes that cause great joy whenever editing texts: dashes, whitespace, all the different quotation marks used ... And for dessert there's some **data processing with Pandas**. Now this meal can either grow your appetite for all things texty, or put you off completely. I'm still hungry, so here we go:

## 1. Transform messy XML to clean XML and save the editors some work
A common task for me is to **convert a word processor document into the kind of XML this project uses**. The starting point is to get collaborators to use styles in Word. If you provide everyone with a .dotx model document, where you have defined the styles you need, and some instructions, there's an actual chance you'll get neatly formatted Word documents back. Direct formatting instead of style usage will produce messy files (that still may look great, but *only* in Word, not when you investigate the resulting code). For instance, a surprisingly large number of writers still use tabs for separating, indenting and aligning paragraphs. But the tabs will disappear in the conversion, leaving you with a whole bunch of paragraphs without any differences at all in indentation and alignment. Or, if tabs have been used instead of Enter, you'll get one gigantic paragraph with a whole bunch of words stuck together.

As stated above, I start off by checking the style usage in the document, correcting it if needed. Then I convert the document to TEI XML using [TEIGarage Conversion](https://teigarage.tei-c.org/). After that, I run transform_xml.py on it. You could just as well use Pandoc for the initial file conversion. In fact, that would probably give you less to fix by script. You could also use the [TEIGarage code on GitHub](https://github.com/TEIC/TEIGarage) and e.g. add your own custom stylesheets: ”TEIGarage is a webservice and RESTful service to transform, convert and validate various formats, focussing on the TEI format.”

Another common scenario is to **receive XML files exported from Transkribus**. [Transkribus](https://readcoop.eu/transkribus/) is a great platform which is immensely useful to projects where manucripts (and also printed texts, they have excellent OCR too) have to be transcribed. But even though you can export as TEI, the XML is not the way this project wants it, and there's the Transkribus functionality of every line in the original image being connected to the corresponding line of text. You can export without the connections, but each paragraph is still divided into multiple lines by newlines, tabs and spaces. This line functionality is great when inside the Transkribus UI, but not once exported, so I remove all of that with my script. This way editors can use Transkribus to get texts transcribed, and then easily continue to work on them after the export without having to manually correct/change any of this code.

Because **the XML files created by the project are the base for both the website, the e-books and the printed books**, only a pre-defined set of XML tags can be used, and there can't be spaces, tabs and newlines all over the place. **Documents coming in from different sources and collaborators may have a lot of ”extras”**, and that's why I need this transformation.

After the project had been going on for a while, it turned out that editors spent a lot of time on expanding abbreviations in the texts (”Rbl.” -> ”Rubel”), often typing in the same expansions over and over again. So I expanded (pun intended) the XML transformation into **checking the texts for abbreviations and inserting the likely expansions**. This is probably a useful feature for many TEI projects, and the script for creating a dictionary out of abbreviations and expansions could easily be tweaked into making a dictionary of e.g. editors' corrections.

### 1. a) transform_xml.py
An XML to XML transformation using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/). Tags, attributes and values are transformed. Also a lot of string replacement with re and replace in order to firstly get rid of tabs, extra spaces and newlines, then add newlines as preferred and finally fix common text problems caused by OCR programs, editors or otherwise present in the source files (mainly character substitution, such as allowing only one type of quotation marks). If you have a dictionary of abbreviations and their expansions (see 1.b below), you'll get abbreviations in the text expanded (and, if needed, encoded) simultaneously.

### 1. b) create_abbr_dictionary.py
This script goes through a list of abbreviations and their expansions and makes a dictionary out of them. The starting point is a match list of all already existing expanded abbreviations in a large material. They have been TEI encoded as
```xml
<choice><abbr>Dr</abbr><expan>Doctor</expan></choice>
```
I exported this match list from "Find in Files" in the Oxygen XML Editor and then cleaned it up with this script. Then I used Beautiful Soup to get the contents of the abbr and expan tags. The contents were then inserted into a dictionary.

## 2. Transform an EPUB to XML
Google Books has digitized a lot of obscure 19th century books that are really hard to find anywhere else. Just what this project needs! However, the EPUBs are messy and the content is of course divided into many different files. In this project, each text consists of just one XML file. This script **gets the EPUB files in the right order, transforms the tags and outputs a single file of pretty XML**.  Not for commercial use, please check copyright and licence conditions for each EPUB provider.

### 2. a) transform_epub.py
This script transforms an EPUB into a single XML document, transforms the tags using Beautiful Soup and gets rid of unnecessary clutter and useless info. The string replacement is similar to the one in the previous script. 

## 3. Transform XML to HTML
This project uses the [Generic Digital Edition Platform](https://github.com/slsfi/digital_edition_documentation/wiki), which includes a website. The platform is designed for **publishing TEI XML online**. This edition project publishes the works of the Finnish author and politician **Leo Mechelin** (1839–1914): [the digital archive Leo Mechelin – Pro lege](https://leomechelin.fi). The archive contains tens of thousands of texts, which are **published on the website and to some extent also as e-books and in print**. The main purpose of the project is to make historical texts and archive material accessible online by digitizing, transcribing and translating documents and by presenting them in a meaningful context.

There's a handful of projects using the digital edition platform, but this was the first one where **XML files are transformed into HTML using Python's Beautiful Soup library**. The other projects are using XSLT. However, the XSLT stylesheets were long, messy and contained 13 years of legacy code and quite a bit of hard coding. I never liked working with XSLT and I found it difficult to find solutions to problems. In my opinion, Python and Beautiful Soup are much easier to handle and Beautiful Soup has great [documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), so I definitely knew that was the way I was going to create the HTML for this project. I'm grateful to Jonas Lillqvist (@jonaslil), who was already using Beautiful Soup for making EPUB:s and inspired me to give it a go.

These scripts **produce HTML specific to the platform's website**. These scripts are **written for easy testing without involving the platform**: XML file in, HTML file out, inspect the result. The scripts for the site are slightly different but the transformation is the same. But instead of a file, the output is a string, which is part of an API endpoint response, together with other data. In part 5 below there are examples of what the scripts for the website look like.

**Tasks handled by these scripts include**: transforming tags, attributes and values. Inserting/removing/unwrapping/wrapping tags, extracting text. Finding footnotes in the text and transforming them into tooltips, as well as listing all the notes for each part of the text as a separate note section at the end of that part. Checking for first paragraphs in sections and making sure they're not indented. Producing lots of different tooltips with varying content. Finding and deleting paragraphs that are empty (as a result of getting rid of text tagged as deleted). Dealing with space issues.

### 3. a) replaces_xslt.py
This script transforms XML documents into HTML for the project's [website](https://leomechelin.fi). The site has several different text types that all have their own transformation. This one works only for text type "est" (established text, or reading text on the digital edition platform). The reading text is the main version of a text and is meant to be easy to read, incorporating manuscript features seamlessly into the text without highlighting them.

If the original text is a manuscript, it is encoded line by line in order to enable easy comparison with the lines of text on the facsimile image. But for the reading text version of the document we don't want those separate lines. We want one paragraph with reflowable text instead of e.g. 15 lines, some of them ending with a hyphen. This transformation makes line breaks, newlines and end-of-line hyphens within paragraphs disappear tracelessly, along with crossed out text. Since deletions are encoded like ”word <del>word</del>, word”, there's some fiddling with space issues too. The output of the website version of this script can be inspected through the [API endpoint for text type est](https://leomechelin.fi/api/leomechelin/text/2/1710/est-i18n/sv).

### 3. b) transform_ms.py
This transformation works only for text type "ms" (manuscript/transcription on the digital edition platform). The transcription is the original version of a text, usually a manuscript. The specific manuscript features, such as deletions and additions to the text, are made visible in the manuscript view (deleted text is not present in the reading text column). Literary scholars and researchers may find deleted text interesting (what was said in the text never printed or never seen by readers?), so it's important to record it and provide a view for it. Original line breaks are preserved within paragraphs in order to allow easy comparison with the lines of text on the facsimile image. Apart from that, it's the same as above. The output of the website version of this script can be inspected through the [API endpoint for text type ms](https://leomechelin.fi/api/leomechelin/text/2/1710/ms).

### 3. c) transform_ms_normalized.py
This transformation works only for text type "ms normalized" (normalized manuscript/transcription on the digital edition platform). The transcription is the original version of a text, usually a manuscript. But this view of it shows the final stage of all changes made to the text by the author, such as deleted text being actually deleted and not visible. Apart from that, it's the same as above. So if the original document had 20 lines of text, of which 3 were crossed out, you'll se 17 lines. The normal ms transformation will highlight additions, this one will simply incorporate them into the text. This view is helpful to the reader if the manuscript has numeral changes. The output of the website version of this script can be inspected through the [API endpoint for text type ms](https://leomechelin.fi/api/leomechelin/text/2/1710/ms).

## 4. Find out the length of the text content in XML files, combine it with database data and do some automated data preparation and visualization
I construct all XML files in this project using scripts in my repo [database_population](https://github.com/Movanna/database_population). The file names contain the publication ID, which is the main identifier for texts, and also the language of the file content. The main directories are named after the different types of texts, and subdirectories after e.g. the correspondent (sender/receiver of a letter) or newspaper (in which an article was published). All files contain a template. The files are kept in a GitHub repository and editors can thus add content to any file they choose at any time. The project also has facsimile images of the original documents.

**The project needed a way of keeping statistics on the tens of thousands of texts and images**: how many texts are there in each language, how long is each text, how many pages of text are there within each category, how many facsimile images are there for each text and category, who's the translator of a certain text and which texts are still missing from the repo (meaning that the files have no other content than the template)? When many collaborators continuously work on the texts, it's hard to keep up with what letter was possibly left untranslated last month. As a publishing project, it's also important to be able to **calculate the estimated number of printed pages for a given subset of texts**. In the Oxygen XML Editor you can count the words and characters of an XML file without the tags, but obviously you wouldn't do that on a large scale. That's what I use this script for.

The script **automates the whole Excel reporting**, so I only have to run it and it outputs an Excel workbook containing all the stats and pivot tables styled to perfection, so there's no need to actually do anything in Excel except for looking at the data.

### 4. a) content_length_and_statistics.py
This script measures the content length of each XML file in a repo or given directory by counting the characters in the human-readable text (the content of the tags), using Beautiful Soup. The script combines the content length with data from the database and outputs an Excel workbook containing lots of info about each text. The data is neatly organized as several different tables with Pandas and styled with openpyxl.

**Tasks handled using Pandas include**: creating pivot tables containing subtotals and totals, so there's some concatenation of tables. Querying data frames. Adding new columns containing values calculated from the contents of a newly created pivot table. Finding specific cells. Appending rows. Changing column order. Writing to Excel.

**Tasks handled using openpyxl include**: replacing values, setting column width, adding gradient colours depending on cell value, constructing sheet names and styling certain cells, rows and columns.

## 5. Transform the project's original XML files into different XML as well as TXT for download on the website
The project's [website](https://leomechelin.fi) features **an option to download all texts as XML or TXT**, so these scripts transform the project's original XML documents into downloadable XML or TXT, as an XML to XML (to string) or XML to HTML (to string) transformation using Beautiful Soup. The downloadable text types are both "est" (established/read text) and "ms" (manuscript/transcription). The texts can be downloaded in Swedish, in Finnish, or (for manuscripts) in the original language. The text's metadata is translated before being inserted into the teiHeader element of the (to-be) XML file. In the case of TXT the translated metadata is part of the endpoint response and not included in the resulting file. If the document's original language isn't sv/fi, the metadata is in Swedish. The difference between the original XML and the downloadable XML is mostly the added metadata, which isn't present in the original file. The metadata is fetched directly from the database. Also, if the original archive document is handwritten, the original XML file contains all the original document's line breaks. This transformation gets rid of those line breaks and end-of-line hyphens, which makes it easier to use the XML/TXT file for other purposes than the ones on the website. The two TXT transformations differ depending on text type (est/ms), containing/not containing e.g. editors' changes or expanded abbreviations.

### 5. a) transform_downloadable_xml.py
This is the script version used by the website, so unlike the other transformation scripts in this repo, you can't use it directly as such, as this transformation gets called upon by the corresponding API endpoint. But you can try out live examples through the API, e.g. https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est-i18n/sv or https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est-i18n/fi, where the first number is the collection ID, the second number is the text ID, and the last part of the URL is the abbreviation of the two available est text languages: either sv or fi. The ms endpoint for the downloadable xml is e.g. https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/1005/ms/962, where the third number in the URL is the ms ID (the first example document, ID 594, has no manuscript: it's a printed document). And of course you can try out the result by downloading any document on the [website](https://leomechelin.fi). The code for the API endpoints and their database queries can be found in my repo [database_population](https://github.com/Movanna/database_population).

### 5. b) transform_downloadable_txt.py
As in 5. a) above, this is the script version used by the website, so you can't use it directly as such, as this transformation gets called upon by the corresponding API endpoint. But you can try out live examples through the API, e.g. https://leomechelin.fi/api/leomechelin/text/downloadable/txt/1/594/est-i18n/sv or https://leomechelin.fi/api/leomechelin/text/downloadable/xml/2/3807/ms/5685, where the first number is the collection ID and the second number is the text ID. If you're accessing text type est, the last part of the URL is the abbreviation of the two available est text languages: either sv or fi. If you're accessing an ms, the third number in the url is the ms ID. And of course you can try out the result by downloading any document on the [website](https://leomechelin.fi). The transformation result is different depending on whether the text is of type est or ms. The code for the API endpoints and their database queries can be found in my repo [database_population](https://github.com/Movanna/database_population).
