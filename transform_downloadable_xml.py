# The website features an option to download texts as xml.
# This script thus transforms the project's original xml documents
# into downloadable xml. 
# The downloadable text type is "est" (reading text).
# The text can be downloaded either in Swedish or in Finnish,
# and the metadata is translated accordingly before being 
# inserted into the teiHeader element of the (to-be) xml file.

# This is the script version for the website, so unlike the 
# other transformation scripts in this repo, you can't use it 
# directly as such, as this transformation gets called upon by
# the corresponding API endpoint. But you can try out live examples on e.g.:
# https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est/sv
# or
# https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est/fi
# where the first number is the collection id, the second number is the text id,
# and the last part of the url is the text language.

import re
import os
from bs4 import BeautifulSoup

db_usr = os.environ.get("")
db_pass = os.environ.get("")
db_host = os.environ.get("")
db_db = os.environ.get("")

SOURCE_FOLDER = "./"

# read an xml file and return its content as a soup object
def read_xml(filename):
    with open(SOURCE_FOLDER + "/" + filename, "r", encoding="utf-8-sig") as source_file:
        file_content = source_file.read()
        # check for hyphens + line breaks
        # if they are present, replace them
        # before the file's content is made into a 
        # BeautifulSoup object
        # the (-|¬|­) below looks for hyphen minus, not sign
        # and (invisible) soft hyphen
        # there may also be some tags involved
        # also check spacing around page breaks
        search_string = re.compile(r"(-|¬|­)(</hi>|</supplied>)?<lb/>")
        match_string = re.search(search_string, file_content)
        if match_string:
            file_content = replace_hyphens(file_content)
        search_string = re.compile(r"(<pb.*?/>)")
        match_string = re.search(search_string, file_content)
        if match_string:
            file_content = edit_page_breaks(file_content)
        # when there are several completely deleted lines of text
        # or a deletion spanning a line break
        # there may be files with one <del> per line of text,
        # but it's ok to have a <del> spanning several lines
        # so let's replace those chopped up <del>:s
        search_string = re.compile(r"</del><lb/>\n<del>")
        file_content = search_string.sub("<lb/>\n", file_content)
        old_soup = BeautifulSoup(file_content, "xml")
    return old_soup

# hyphens followed by line breaks are not to be present
# in the reading texts
# they originate from the transcriptions for the manuscript column,
# where each line of text is equivalent to the original manuscript's
# line, including its possible hyphens
# a hyphen + <lb/> may or may not be followed by newlines and <pb/>-tags
# the <pb/>-tag should not be preceded by space, and always followed
# by space unless inside a word or between text dividing elements
# in order not to create space(s) inside words, we have to take this
# into account
def replace_hyphens(file_content):
    # the (-|­) below checks for either hyphen minus or a soft hyphen
    # (invisible here), and removes the line break
    # we also have to check for certain tags around the hyphen
    # if there are two <hi> tags in the word, one for each line:
    # merge them
    search_string = re.compile(r"(-|­)<lb/>\n*(<pb.*?/>)\n*")
    file_content = search_string.sub(r"\2", file_content)
    search_string = re.compile(r"(-|­)<lb/>\n*")
    file_content = search_string.sub("", file_content)
    search_string = re.compile(r"(-|­)</hi><lb/>\n*(<pb.*?/>)\n*<hi>")
    file_content = search_string.sub(r"\2", file_content)
    search_string = re.compile(r"(-|­)</hi><lb/>\n*<hi>")
    file_content = search_string.sub("", file_content)
    search_string = re.compile(r"(-|­)(</supplied>)<lb/>\n*")
    file_content = search_string.sub(r"\2", file_content)
    # the ¬ (not sign) in the transcriptions represents a hyphen which is
    # not to disappear, at this point we can replace it with a true hyphen
    # and remove the line break
    # we also have to check for certain tags around the hyphen
    # if there are two <hi> tags in the word, one for each line:
    # merge them
    search_string = re.compile(r"¬<lb/>\n*(<pb.*?/>)\n*")
    file_content = search_string.sub(r"-\1", file_content)
    search_string = re.compile(r"¬<lb/>\n*")
    file_content = search_string.sub("-", file_content)
    search_string = re.compile(r"¬</hi><lb/>\n*(<pb.*?/>)\n*<hi>")
    file_content = search_string.sub(r"-\1", file_content)
    search_string = re.compile(r"¬</hi><lb/>\n*<hi>")
    file_content = search_string.sub("-", file_content)
    search_string = re.compile(r"¬(</supplied>)<lb/>\n*")
    file_content = search_string.sub(r"-\1", file_content)
    # in this case, we should also add a space
    # (cases like "<hi>Väst-</hi> och <hi>Öst-Finland</hi>")
    search_string = re.compile(r"¬</hi><lb/>\n*")
    file_content = search_string.sub("-</hi> ", file_content)
    # the – (en dash) is normally to be followed by space after removing
    # the line break, unless the dash is part of a word and there's no
    # space between the dash and the preceding character
    # if the latter is the case: remove the line break now
    search_string = re.compile(r"(\w)–<lb/>\n*(<pb.*?/>)\n*")
    file_content = search_string.sub(r"\1–\2", file_content)
    search_string = re.compile(r"(\w)–<lb/>\n*")
    file_content = search_string.sub(r"\1–", file_content)
    return file_content

# when newlines preceding <pb/> are removed and <pb/>-tags
# followed by a newline and a word get a trailing space at this point,
# the transformations of <lb/> and <pb/> work correctly later on
def edit_page_breaks(file_content):
    search_string = re.compile(r"\n(<pb.*?/>)")
    file_content = search_string.sub(r"\1", file_content)
    search_string = re.compile(r"(<pb.*?/>)\n(\w)")
    file_content = search_string.sub(r"\1 \2", file_content)
    return file_content

def content_template():
    xml_template = '''
    <TEI>
    <teiHeader>
    <fileDesc>
    <titleStmt>
    <title></title>
    <respStmt>
    </respStmt>
    </titleStmt>
    <publicationStmt>
    <publisher>Leo Mechelin – Pro lege</publisher>
    </publicationStmt>
    <sourceDesc>
    </sourceDesc>
    </fileDesc>
    </teiHeader>
    <text>
    <body>
    </body>
    </text>
    </TEI>
    '''
    return BeautifulSoup(xml_template, "xml")

# get body from source xml and combine with template
# go through certain elements, attributes and values
# and transform them
def transform_xml(old_soup, language, bibl_data):
    xml_body = old_soup.find("body")
    new_soup = content_template()
    new_soup.body.append(xml_body)
    new_soup.body.unwrap()
    # store the text's metadata in the teiHeader 
    # in a way conforming to TEI as much as possible
    if bibl_data is not None:
        publication_title = bibl_data["publication_title"]
        publication_subtitle = bibl_data["publication_subtitle"]
        published_by = bibl_data["published_by"]
        document_type = bibl_data["document_type"]
        original_language = bibl_data["original_language"]
        orig_lang_abbr = bibl_data["orig_lang_abbr"]
        publication_date = bibl_data["publication_date"]
        author = bibl_data["author"]
        sender = bibl_data["sender"]
        recipient = bibl_data["recipient"]
        translations = bibl_data["translations"]
        new_soup.teiHeader["xml:lang"] = language
        new_soup.title.append(publication_title)
        if publication_subtitle is not None:
            new_tag = new_soup.new_tag("title")
            new_soup.title.append("\n")
            new_soup.title.insert_after(new_tag)
            new_tag["type"] = "sub"
            new_tag.append(publication_subtitle)
            new_tag.insert_after("\n")
        if translations != []:
            for translation in translations:
                translated_lang = translation["translated_into"]
                if language == "sv":
                    if "svenska" in translated_lang:
                        new_tag = new_soup.new_tag("resp")
                        new_soup.respStmt.append(new_tag)
                        new_tag.append("översättning till svenska")
                        new_tag.insert_after("\n")
                        translators = translation["translators"]
                        for translator in translators:
                            new_tag = new_soup.new_tag("name")
                            new_soup.respStmt.append(new_tag)
                            new_tag.append(translator)
                            new_tag.insert_after("\n")
                        break
                    else:
                        continue
                if language == "fi":
                    if translated_lang == "suomeksi":
                        new_tag = new_soup.new_tag("resp")
                        new_soup.respStmt.append(new_tag)
                        new_tag.append("suomentanut")
                        new_tag.insert_after("\n")
                        translators = translation["translators"]
                        for translator in translators:
                            new_tag = new_soup.new_tag("name")
                            new_soup.respStmt.append(new_tag)
                            new_tag.append(translator)
                            new_tag.insert_after("\n")
                        break
                    else:
                        continue
        new_tag = new_soup.new_tag("bibl")
        new_soup.sourceDesc.append(new_tag)
        new_tag.append("\n")
        if author != []:
            for person in author:
                new_tag = new_soup.new_tag("author")
                new_soup.bibl.append(new_tag)
                new_tag.append(person)
                new_tag.insert_after("\n")
        elif sender != []:
            for person in sender:
                new_tag = new_soup.new_tag("author")
                new_soup.bibl.append(new_tag)
                new_tag.append(person)
                new_tag.insert_after("\n")
        if recipient != []:
            for person in recipient:
                new_tag = new_soup.new_tag("recipient")
                new_soup.bibl.append(new_tag)
                new_tag.append(person)
                new_tag.insert_after("\n")
        if published_by is not None:
                new_tag = new_soup.new_tag("publisher")
                new_soup.bibl.append(new_tag)
                new_tag.append(published_by)
                new_tag.insert_after("\n")
        new_tag = new_soup.new_tag("date")
        new_soup.bibl.append(new_tag)
        new_tag.append(publication_date)
        new_tag.insert_after("\n")
        new_tag = new_soup.new_tag("docType")
        new_soup.bibl.append(new_tag)
        new_tag.append(document_type)
        new_tag.insert_after("\n")
        new_tag = new_soup.new_tag("textLang")
        new_soup.bibl.append(new_tag)
        if language == "sv":
            new_tag.append("Dokumentets originalspråk: ")
        if language == "fi":
            new_tag.append("Dokumentin alkuperäiskieli: ")
        new_tag.append(original_language)
        new_tag.insert_after("\n")
        i = 0
        for orig_lang in orig_lang_abbr:
            if i == 0:
                new_tag["mainLang"] = orig_lang
                if len(orig_lang_abbr) == 1:
                    break
            if i == 1:
                new_tag["otherLangs"] = orig_lang
            if i > 1:
                new_tag["otherLangs"] += " "
                new_tag["otherLangs"] += orig_lang
            i += 1
    # we need the div_type_value of the first <div>
    # in order to transform <p> right
    # also, add this text's language value to the top <div>
    element = new_soup.find("div")
    if element is not None:
        if "type" in element.attrs:
            div_type_value = element["type"]
        element["xml:lang"] = language
    # transform <p> 
    elements = new_soup.find_all("p")
    if len(elements) > 0:
        p_number = 0
        for element in elements:
            # no need to check for the following unless a letter
            if div_type_value == "letter":
            # first paragraph in a letter after the opener
            # shouldn't be indented
                if element.previous_sibling:
                    if element.previous_sibling.name == "opener" or (element.previous_sibling.previous_sibling and element.previous_sibling.previous_sibling.name == "opener") and "rend" not in element.attrs:
                        element["rend"] = ["noIndent"]
                # first paragraph in a postscript shouldn't be indented
                if element.parent.name == "postscript":
                    if not element.previous_sibling or element.previous_sibling.name != "p" and "rend" not in element.attrs:
                        element["rend"] = ["noIndent"]
            if div_type_value == "misc" or div_type_value == "article" or div_type_value == "hansard":
                # first paragraph in the document shouldn't be indented
                if p_number == 0 and "rend" not in element.attrs:
                    element["rend"] = ["noIndent"]
            p_number += 1
    # transform <lb/>
    elements = new_soup.find_all("lb")
    if len(elements) > 0:
        for element in elements:
            # @break="yes" means we really should have a line break
            if "break" in element.attrs:
                continue
            # if <lb/> is followed by <pb/>, don't replace <lb/>
            # with a space as below
            # the edit_page_breaks function helps handling this space issue
            elif element.next_sibling and element.next_sibling.name == "pb":
                element.decompose()
            # replace <lb/> (line break in a manuscript) with a space,
            # since this is a reading text where the content of a <p>
            # isn't divided into lines of text, as in the ms
            # the reading text should be reflowable
            else:
                element.replace_with(" ")
    # transform <pb/> so that all pb:s are uniform in terms of
    # attribute + value for type of pb
    elements = new_soup.find_all("pb")
    if len(elements) > 0:
        for element in elements:
            if "type" not in element.attrs:
                element["type"] = "orig"
    body = new_soup.find("body")
    div = new_soup.find("div")
    # if there is no text content in the source xml
    # just return an empty string
    if len(body.get_text(strip = True)) == 0:
        xml_string = ""
    elif div is not None and len(div.get_text(strip = True)) == 0:
        xml_string = ""
    else:
        xml_string = str(new_soup)
    return xml_string

def transform(file, language, bibl_data):
    old_soup = read_xml(file)
    xml_string = transform_xml(old_soup, language, bibl_data)
    return xml_string