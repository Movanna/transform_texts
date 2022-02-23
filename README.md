# transform_texts
**Python scripts for transforming texts from XML to HTML.**

I work with texts. Texts are often seen as uncomplicated: just characters, words and paragraphs in a text document. Everyone knows how to create a text, right? Just open Word and start writing. Then send the file to be published – and the fun begins.

Hardly surprising at this point, my view is that texts, textual phenomena, books and text formats are rather complex. A Word document can *look* just perfect, but still be a nightmare for someone who wants to publish the contents online. Wait, getting text from one place to another is as simple as anything, isn't it? Well, that's what developers always tell me: ”But, clearly, the text *is* all there!”. Yeah, it might be, but it still looks awful. If the result is that the subtitle is larger than the title, the text is cramped, the font is ugly, the italics you were expecting have disappeared, footnotes are gone, and the indentation is all off, then maybe that text wasn't such an easy prey after all.

Add to this TEI XML (the Text Encoding Initiative, https://tei-c.org/), where all kinds of textual features such as deletions, substitutions, underlining and language usage are meticulously recorded in tags and attributes. Let it simmer with web sites based on those source files. Stir in e-books, add seasoning from Transkribus (Handwritten Text Recognition, https://readcoop.eu/transkribus/), mix with desktop publishing, sprinkle with OCR, .odt and .docx and serve it all on a plate from the generic digital edition platform (https://github.com/slsfi/digital_edition_documentation/wiki). That dish can either grow your appetite for all things texty, or put you off completely. I'm still hungry, so here we go:

## 1. Transform XML to XML
A common task for me is to convert a word processor document into the kind of XML this project uses. The starting point is to get collaborators to use styles in Word. If you provide everyone with a .dotx model document, where you have defined the styles you need, and some instructions, there's an actual chance you'll get neatly formatted Word documents back. Direct formatting instead of style usage will produce messy files (that still look great, but *only* in Word, not when you investigate the resulting code). I start off by converting the document to TEI XML using OxGarage Conversion (https://oxgarage.tei-c.org/). After that, I run transform_xml.py on it.

Another common scenario is to receive XML files exported from Transkribus. Transkribus is a great platform which is immensely useful to projects where manucripts (and even printed texts) have to be transcribed. But even though you can export as TEI, the XML is not the way this project wants ut, and there's a lot of Transkribus functionality, such as every line in the original image being connected to the corresponding line of text. This is great when inside the Transkribus UI, but not once exported, so I remove all of that with my script. This way editors can use Transkribus to get texts transcribed, and the continue to work on them efter the export without having to correct/change any of the code.

### 1. a) transform_xml.py
An XML to XML transformation using Beautiful Soup. Also a lot of string replacement with re and replace in order to firstly get rid of tabs, extra spaces and newlines, then add newlines as preferred and finally fix common text problems caused by OCR programs, editors or otherwise present in the source files.

## 2. Transform an EPUB to XML
Google Book has digitized a lot of obscure 19th century books that are really hard to find anywhere else. Just what this project needs! However, the EPUBs are messy and the content is of course in many different files. In this project, each text consists of just one file. This script gets the EPUB files in the right order and outputs a single file of nice XML.

### 2. a) transform_epub.py
This script transforms a Google Books EPUB into a single XML document, transforms the tags using Beautiful Soup and gets rid of unnecessary clutter and useless info. The string replacement is similar to the previous script.

## 3. Transform XML to HTML
This project uses the generic digital edition platform (https://github.com/slsfi/digital_edition_documentation/wiki), which includes a web site. The edition project which I'm currently working on publishes the works of the Finnish author and politician Leo Mechelin (1839–1914). The edition contains thousands of texts, which will be published on the website and to some extent also as e-books and in print. The main purpose of the project is to make historical texts and archive material accessible online by digitizing, transcribing and translating documents and by presenting them in a meaningful context.

There's about a handful of projects using the digital edition platform, but this is the first one where XML files are transformed into HTML using Python. The other projects are using XSLT. However, the XSLT is messy and contains 13 years of legacy and quite a bit of hard coding. I never liked working with XSLT and I found it difficult to find solutions to problems. In my opinion, Python and Beautiful Soup are so much easier to handle, so I definitely knew that was the way I was going to create the HTML for this project. I'm grateful to Jonas Lillqvist (jonlil), who used this method for making EPUBS and inspired me to give it a go.

### 3. a) replaces_xslt.py
This script transforms XML documents into HTML for the project's website. The site has several different text types that all have their one transformation. This one works only for text type "est" (established text, or reading text on the digital edition platform). The reading text is the main version of a text and meant to be easy to read, ignoring a lot of manuscript features. This version of the script produces HTML specific to the platform. In the long run, all HTML on the site needs refactoring in order to be i.e. more accessible, but until now priority nr 1 for me has been to just get the transformation to produce a sensible result that works well enough. Also, this script is for easy testing; the script for the site is slightly different but the transformation is the same. It just doesn't fetch and output files in the same way.

### 3. b) transform_ms.py
This transformation works only for text type "ms" (manuscript/transcription on the digital edition platform). The transcription is the original version of a text, a manuscript. It has some specific manuscript features, such as deletions and additions to the text being shown (deletions are not present in the reading text column). Apart from that, it's the same as above.

### 3. c) transform_ms_normalized.py
This transformation works only for text type "ms normalized" (normalized manuscript/transcription on the digital edition platform). The transcription is the original version of a text, a manuscript. But this view of it shows the final stage of all changes made to the text by the author, such as deleted text being actually deleted and not visible. Apart from that, it's the same as above.

