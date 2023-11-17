# This script transforms the project's original xml documents
# into xml for the download feature on the website.
# The downloadable text types are "est" (established text/reading text)
# and "ms" (manuscript/transcription).
# This transformation works for both types
# and produces an identical result in both cases.
# The text can be downloaded either in Swedish or in Finnish,
# and the metadata is translated accordingly before being 
# inserted into the teiHeader element of the (to-be) xml file.
# If the downloaded text is in another language than sv/fi, 
# the metadata is in Swedish.

# This is the script version for the website, so unlike the 
# other transformation scripts in this repo, you can't use it 
# directly as such, as this transformation gets called upon by
# the corresponding API endpoint. But you can try out live examples on e.g.:
# https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est-i18n/sv
# https://leomechelin.fi/api/leomechelin/text/downloadable/xml/1/594/est-i18n/fi
# https://leomechelin.fi/api/leomechelin/text/downloadable/xml/2/3807/ms/5685
# where, for est, the first number is the collection id, the second number is
# the text id, and the last part of the url is the text language.
# For ms, the first number is the collection id, the second number is
# the text id, and the last number is the ms id.

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

# when newlines preceding <pb/> are removed
# and <pb/>-tags followed by a newline and a word or a certain element
# get the newline replaced by a trailing space at this point,
# the transformations of <lb/> and <pb/> work correctly later on
# and the encoding of <pb/> is TEI conform
def edit_page_breaks(file_content):
    search_string = re.compile(r"\n(<pb.*?/>)")
    file_content = search_string.sub(r"\1", file_content)
    search_string = re.compile(r"(<pb.*?/>)\n(\w)")
    file_content = search_string.sub(r"\1 \2", file_content)
    # elements used within paragraph-like elements may be on a new line
    # due to the transcription being divided into lines of text with <lb/>
    # the <pb/> is always on its own line in this project's transcriptions
    # when getting rid of the line breaks, this has to be taken into account
    # as a page break is always to be followed (but not preceded) by a space
    # unless the page breaks in the middle of a word
    # (the latter case already handled by function replace_hyphens)
    search_string = re.compile(r"(<pb.*?/>)\n(?=(<choice|<add|<del|<persName|<xref|<anchor|<hi|<foreign|<supplied|<unclear|<gap))")
    file_content = search_string.sub(r"\1 ", file_content)
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
# add content to them and transform them
def transform_xml(old_soup, language, bibl_data, est_or_ms):
    xml_body = old_soup.find("body")
    new_soup = content_template()
    # transfer original xml body to template body
    # and unwrap duplicated body element
    new_soup.body.append(xml_body)
    new_soup.body.unwrap()
    # if there's no text content apart from the template:
    # return an empty string
    body = new_soup.find("body")
    div = new_soup.find("div")
    if len(body.get_text(strip = True)) == 0:
        xml_string = ""
        return xml_string
    elif div is not None and len(div.get_text(strip = True)) == 0:
        xml_string = ""
        return xml_string
    else:
        if bibl_data is not None:
            publication_id = bibl_data["id"]
            manuscript_id = bibl_data["manuscript_id"]
            publication_title = bibl_data["publication_title"]
            publication_subtitle = bibl_data["publication_subtitle"]
            published_by = bibl_data["published_by"]
            document_type = bibl_data["document_type"]
            original_language = bibl_data["original_language"]
            orig_lang_abbr = bibl_data["orig_lang_abbr"]
            publication_date = bibl_data["publication_date"]
            publication_archive_info = bibl_data["publication_archive_info"]
            author = bibl_data["author"]
            sender = bibl_data["sender"]
            recipient = bibl_data["recipient"]
            translations = bibl_data["translations"]
            new_soup.teiHeader["xml:lang"] = language
            new_soup.title.append(publication_title)
            if publication_subtitle is not None:
                new_tag = new_soup.new_tag("title")
                new_soup.title.insert_after(new_tag)
                new_tag["type"] = "sub"
                new_tag.append(publication_subtitle)
            if translations != []:
                for translation in translations:
                    translated_lang = translation["translated_into"]
                    if language == "sv":
                        if "svenska" in translated_lang:
                            new_tag = new_soup.new_tag("resp")
                            new_soup.respStmt.append(new_tag)
                            new_tag.append("översättning till svenska")
                            translators = translation["translators"]
                            for translator in translators:
                                new_tag = new_soup.new_tag("name")
                                new_soup.respStmt.append(new_tag)
                                new_tag.append(translator)
                            break
                        else:
                            continue
                    if language == "fi":
                        if translated_lang == "suomeksi":
                            new_tag = new_soup.new_tag("resp")
                            new_soup.respStmt.append(new_tag)
                            new_tag.append("suomentanut")
                            translators = translation["translators"]
                            for translator in translators:
                                new_tag = new_soup.new_tag("name")
                                new_soup.respStmt.append(new_tag)
                                new_tag.append(translator)
                            break
                        else:
                            continue
            new_tag = new_soup.new_tag("bibl")
            new_soup.sourceDesc.append(new_tag)
            if author != []:
                for person in author:
                    new_tag = new_soup.new_tag("author")
                    new_soup.bibl.append(new_tag)
                    new_tag.append(person)
            elif sender != []:
                for person in sender:
                    new_tag = new_soup.new_tag("sender")
                    new_soup.bibl.append(new_tag)
                    new_tag.append(person)
            if recipient != []:
                for person in recipient:
                    new_tag = new_soup.new_tag("recipient")
                    new_soup.bibl.append(new_tag)
                    new_tag.append(person)
            if published_by is not None:
                    new_tag = new_soup.new_tag("publisher")
                    new_soup.bibl.append(new_tag)
                    new_tag.append(published_by)
            new_tag = new_soup.new_tag("date")
            new_soup.bibl.append(new_tag)
            new_tag.append(publication_date)
            new_tag = new_soup.new_tag("archiveInfo")
            new_soup.bibl.append(new_tag)
            new_tag.append(publication_archive_info)
            new_tag = new_soup.new_tag("docType")
            new_soup.bibl.append(new_tag)
            new_tag.append(document_type)
            new_tag = new_soup.new_tag("textLang")
            new_soup.bibl.append(new_tag)
            if language == "sv":
                new_tag.append("Dokumentets originalspråk: ")
            if language == "fi":
                new_tag.append("Dokumentin alkuperäinen kieli: ")
            new_tag.append(original_language)
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
            new_tag = new_soup.new_tag("publicationId")
            new_soup.bibl.append(new_tag)
            new_tag.append(publication_id)
            # if this text's language value is in orig_lang_abbr
            # and its est_or_ms value is "est", then
            # this text is both manuscript/transcription and established/reading text
            # at the same time and in the same file:
            # then we can add its manuscript_id
            # if est_or_ms is "ms", then we know we should add manuscript_id 
            # if this text's language value isn't in orig_lang_abbr
            # and its est_or_ms value is "est",
            # then there's a separate manuscript file (or no manuscript file at all)
            # and we shouldn't connect that manuscript_id to this text
            if est_or_ms == "ms" or (est_or_ms == "est" and language in orig_lang_abbr and manuscript_id is not None):
                new_tag = new_soup.new_tag("manuscriptId")
                new_soup.bibl.append(new_tag)
                new_tag.append(str(manuscript_id))
        # add this text's language value to the top <div>
        element = new_soup.find("div")
        if element is not None:
            if est_or_ms == "est":
                element["xml:lang"] = language
            if est_or_ms == "ms":
                element["xml:lang"] = original_language              
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
                # replace <lb/> (an original line break in a manuscript)
                # with a space, since this transformation produces an xml file
                # which isn't divided into lines of text, as in the original
                # transcript
                else:
                    element.replace_with(" ")
        # transform <pb/> 
        elements = new_soup.find_all("pb")
        if len(elements) > 0:
            for element in elements:
                if "type" not in element.attrs:
                    element["type"] = "orig"
        xml_string = str(new_soup)
        return xml_string

def tidy_up_xml(xml_string):
    # this is what's left of the transcription line breaks
    # replace them with just a space
    search_string = re.compile(r"\s\n")
    xml_string = search_string.sub(" ", xml_string)
    # get rid of tabs, other newlines and extra spaces
    search_string = re.compile(r"\n|\t")
    xml_string = search_string.sub("", xml_string)
    search_string = re.compile(r"\s{2,}")
    xml_string = search_string.sub(" ", xml_string)
    # add newlines as preferred
    # for <TEI> and <teiHeader>:
    search_string = re.compile(r"(<TEI>|<teiHeader.*?>|<fileDesc>|<titleStmt>|</title>|<respStmt>|</resp>|</name>|</respStmt>|</titleStmt>|<publicationStmt>|</publisher>|</publicationStmt>|<sourceDesc>|<bibl>|</author>|</sender>|</recipient>|</date>|</archiveInfo>|</docType>|</textLang>|</publicationId>|</manuscriptId>|</bibl>|</sourceDesc>|</fileDesc>|</teiHeader>|</TEI>)")
    xml_string = search_string.sub(r"\1\n", xml_string)
    search_string = re.compile(r"(<TEI>)")
    xml_string = search_string.sub(r"\n\1", xml_string)
    # for <text>, <body> and text dividing elements:
    search_string = re.compile(r"(<text>|</text>|<body.*?>|</body>|<div.*?>|</div>|</head>|</p>|<lg>|</lg>|</l>|<opener>|</opener>|<closer>|</closer>|<postscript>|</postscript>|</dateline>|</address>|</salute>|</signed>|<table>|</table>|</row>|<list>|</list>|</item>|<milestone.*?/>)")
    xml_string = search_string.sub(r"\1\n", xml_string)
    # after certain page breaks:
    search_string = re.compile(r"(<pb.*?/>)(?=(<p>|<p |<po|<o|<cl|<t|<l|<r|<i|<sa|<si|<he|<da|<addr|<m))")
    xml_string = search_string.sub(r"\1\n", xml_string)
    # remove spaces at the beginning of lines
    # (MULTILINE matches at the beginning of the string
    # and at the beginning of each line)
    search_string = re.compile(r"^ +<", re.MULTILINE)
    xml_string = search_string.sub("<", xml_string)
    # in case there are some chopped up <del>:s and <add>:s
    search_string = re.compile(r"</del><del>|<add></add>")
    xml_string = search_string.sub("", xml_string)
    return xml_string

def transform(file, language, bibl_data, est_or_ms):
    old_soup = read_xml(file)
    xml_string = transform_xml(old_soup, language, bibl_data, est_or_ms)
    xml_string = tidy_up_xml(xml_string)
    return xml_string