# This script transforms xml documents into html for the website.
# Used for text type "est" (reading text, the main edited text)
# as well as for title pages and introductions.

import re
import os
from bs4 import BeautifulSoup
import html
import copy

SOURCE_FOLDER = "documents/xml"
OUTPUT_FOLDER = "documents/html"
# the script version used on the website gets the text language
# value from the site, in this version we set it here
# it only affects the @lang value for the top div
# and the heading for the list of footnotes
LANGUAGE = "fi"

# loop through xml source files in folder and append to list
def get_source_file_paths():
    file_list = []
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".xml"):
            file_list.append(filename)
    return file_list

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
        # this makes the transformation of <add> containing <del> 
        # work better later on
        search_string = re.compile(r"</del><lb/>\n<del>")
        file_content = search_string.sub("<lb/>\n", file_content)
        xml_soup = BeautifulSoup(file_content, "xml")
    print("We have old soup.")
    return xml_soup

# hyphens followed by line breaks are not to be present
# in the reading texts
# they originate from the transcriptions for the manuscript/transcription column,
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

def create_html_template():
    html_doc = '''
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title></title>
        </head>
        <body></body>
    </html>
    '''
    html_soup = BeautifulSoup(html_doc, "lxml")
    return html_soup

def create_html_file(xml_soup):
    html_soup = create_html_template()
    # transfer title from xml header to html head 
    html_soup.head.title.string = xml_soup.teiHeader.title.get_text()
    # transfer xml body to html body, and get rid of xml body tag
    xml_body = xml_soup.body
    html_soup.body.append(xml_body)
    html_soup.body.body.unwrap()
    return html_soup

# go through the xml elements, attributes and values
# and transform them as needed
def transform_tags(html_soup):
    # <div> is transformed towards the end of this function
    # and not here, but we still need the div_type_value
    # of the first <div>, in order to transform <p> right
    # also add this text's language value to the top <div>
    element = html_soup.find("div")
    if "type" in element.attrs:
        div_type_value = element["type"]
        element["lang"] = LANGUAGE
    # transform <p> 
    elements = html_soup.find_all("p")
    if len(elements) > 0:
        p_number = 0
        for element in elements:
            # no need to check for the following unless a letter
            if div_type_value == "letter":
            # first paragraph in a letter after the opener
            # shouldn't be indented
                if element.previous_sibling:
                    if element.previous_sibling.name == "opener" or (element.previous_sibling.previous_sibling and element.previous_sibling.previous_sibling.name == "opener") and "rend" not in element.attrs:
                        element["class"] = ["noIndent"]
                # first paragraph in a postscript shouldn't be indented
                if element.parent.name == "postscript":
                    if not element.previous_sibling or element.previous_sibling.name != "p" and "rend" not in element.attrs:
                        element["class"] = ["noIndent"]
            if div_type_value == "misc" or div_type_value == "article" or div_type_value == "hansard":
                # first paragraph in the document shouldn't be indented
                if p_number == 0 and "rend" not in element.attrs:
                    element["class"] = ["noIndent"]
            if "rend" in element.attrs:
                rend_value = element["rend"]
                element["class"] = [rend_value]
                del element["rend"]
            else:
                rend_value = None
            # type values: subtitle, motto
            if "type" in element.attrs:
                type_value = element["type"]
                element["class"] = [type_value]
                # "tei" is a required class value in reading texts for these p:s
                # otherwise some inherent styles won't work
                if div_type_value != "title_page" and div_type_value != "introduction":
                    element["class"].append("tei")
                if type_value == "subtitle":
                    # as specified in Digital Publishing WAI-ARIA Module 1.1
                    element["role"] = "doc-subtitle"
                del element["type"]
            else:
                type_value = None
            # we'll style all p elements in the body text of the
            # reading text column to have space between them
            # (and no indent)
            if not type_value and rend_value:
                element["class"].append("spaced")
            if not type_value and not rend_value:
                element["class"] = "spaced"
            p_number += 1
    # transform <lb/>
    elements = html_soup.find_all("lb")
    if len(elements) > 0:
        for element in elements:
            # @break="yes" means we really should have a line break
            if "break" in element.attrs:
                del element["break"]
                element.name = "br"
            # if <lb/> is followed by <pb/>, don't add space
            # the edit_page_breaks function handled this space issue already
            elif element.next_sibling and element.next_sibling.name == "pb":
                element.decompose()
            # replace <lb/> (line break in a transcription/manuscript) with a space,
            # since this is a reading text where the content of a <p>
            # isn't divided into lines of text, as in the ms
            else:
                element.replace_with(" ")
    # transform <pb/>
    # a possible trailing space was already handled by
    # the edit_page_breaks function
    elements = html_soup.find_all("pb")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            # insert the page number
            if "n" in element.attrs:
                n_value = element["n"]
                element.insert(0, "|" + n_value + "|")
                del element["n"]
            if "type" in element.attrs:
                type_value = element["type"]
                if type_value == "orig":
                    element["class"] = "pb_orig"
                    del element["type"]
            # if there's no @type, use this class
            else:
                element["class"] = "pb_orig"
    # transform <lg> (poem stanza)
    elements = html_soup.find_all("lg")
    if len(elements) > 0:
        for element in elements:
            element.name = "p"
            element["class"] = "lg"
    # transform <l> (poem line): each <l> will be a span
    elements = html_soup.find_all("l")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            # treat class value as list item in case you have to
            # append more classes
            element["class"] = ["l"]
            # add rend value as another class
            if "rend" in element.attrs:
                element["class"].append(element.get("rend"))
                del element["rend"]
            # insert line break after line span
            line_break = html_soup.new_tag("br")
            element.insert_after(line_break)
    # transform <head>
    # the platform provides <h1> and <h2> for each collection text page
    # (i.e. each publication, or text with different adherent translations/transcriptions)
    # <h1> contains the title of the text, automatically fetched from toc
    # each column is an <article> with the column type (e.g. Transcription) as <h2>
    # therefore the hierarchy of a text of type "est" should always start with <h3>
    # for title and introduction pages there are no pre-provided headings,
    # so these text types should always start with <h1>
    elements = html_soup.find_all("head")
    if len(elements) > 0:
        for element in elements:
            if "type" in element.attrs:
                type_value = element["type"]
                if type_value == "title":
                    element["class"] = ["title"]
                    if div_type_value != "title_page" and div_type_value != "introduction":
                        element.name = "h3"
                        element["class"].append("tei")
                    else:
                        element.name = "h1"
                if type_value == "section":
                    element["class"] = ["section"]
                    if div_type_value != "title_page" and div_type_value != "introduction":
                        element.name = "h4"
                        element["class"].append("tei")
                    else:
                        element.name = "h2"
                if type_value == "subchapter":
                    element["class"] = ["sub"]
                    if div_type_value != "title_page" and div_type_value != "introduction":
                        element.name = "h5"
                        element["class"].append("tei")
                    else:
                        element.name = "h3"
                if type_value == "subchapter2":
                    element["class"] = ["sub2"]
                    if div_type_value != "title_page" and div_type_value != "introduction":
                        element.name = "h6"
                        element["class"].append("tei")
                    else:
                        element.name = "h4"
                if type_value == "subchapter3":
                    element["class"] = ["sub3"]
                    if div_type_value != "title_page" and div_type_value != "introduction":
                        element.name = "h6"
                        element["class"].append("tei")
                    else:
                        element.name = "h5"
                del element["type"]
            # table headers should be <caption>
            elif element.parent.name == "table":
                element.name = "caption"
            # in the xml files, the list header is placed inside
            # <list>; in html we need the header outside
            # of the list element
            # but not as part of the <h> hierarchy
            elif element.parent.name == "list":
                new_header = html_soup.new_tag("p")
                new_header["class"] = ["list_header"]
                new_header["class"].append("tei")
                element.parent.insert_before(new_header)
                list_header = element.extract()
                new_header.insert(0, list_header)
                list_header = element.unwrap()
            # don't transform html tag <head>, just the xml <head>
            elif element.parent.name == "html":
                continue
            # <head> without attribute: chapter heading
            else:
                element["class"] = ["chapter"]
                if div_type_value != "title_page" and div_type_value != "introduction":
                    element.name = "h4"
                    element["class"].append("tei")
                else:
                    element.name = "h2"
    # transform <cell> (in <row> in <table>)
    # also transform cells in a row with @role="label"
    elements = html_soup.find_all("cell")
    if len(elements) > 0:
        for element in elements:
            # <row role="label"> means its cells are to be <th>, not <td>
            if element.parent.name == "row" and "role" in element.parent.attrs:
                element.name = "th"
                element["scope"] = "col"
            else:
                element.name = "td"
            if "rend" in element.attrs:
                element["class"] = "right"
                del element["rend"]
    # transform <row> (in <table>)
    elements = html_soup.find_all("row")
    if len(elements) > 0:
        for element in elements:
            if "role" in element.attrs:
                del element["role"]
            element.name = "tr"
    # transform <list>
    elements = html_soup.find_all("list")
    if len(elements) > 0:
        for element in elements:
            element.name = "ul"
    # transform <item>
    elements = html_soup.find_all("item")
    if len(elements) > 0:
        for element in elements:
            element.name = "li"   
    # transform <hi>       
    elements = html_soup.find_all("hi")
    if len(elements) > 0:
        for element in elements:
            if "rend" in element.attrs:
                if element["rend"] == "raised":
                    element.name = "sup"
                elif element["rend"] == "sub":
                    element.name = "sub"
                elif element.parent.name == "h1" or element.parent.name == "h2" or element.parent.name == "h3" or element.parent.name == "h4" or element.parent.name == "h5" or element.parent.name == "h6":
                    element.unwrap()
                else:
                    element["class"] = element["rend"]
                    element.name = "em"
                del element["rend"]
            else:
                if element.parent.name == "h1" or element.parent.name == "h2" or element.parent.name == "h3" or element.parent.name == "h4" or element.parent.name == "h5" or element.parent.name == "h6":
                    element.unwrap()
                else:
                    element.name = "i"
    # transform <milestone>
    elements = html_soup.find_all("milestone")
    if len(elements) > 0:
        for element in elements:
            element.name = "hr"
            if element["type"] == "editorial":
                element["class"] = "space"
            if element["type"] == "bar":
                element["class"] = "milestoneBar"
            del element["type"]
    # transform <anchor>
    elements = html_soup.find_all("anchor")
    if len(elements) > 0:
        for element in elements:
            element.name = "a"
            if "id" in element.attrs:
                id_value = element["id"]
                element["name"] = id_value
                element["class"] = ["anchor"]
                element["class"].append(id_value)
                del element["id"]
    # transform <choice>
    elements = html_soup.find_all("choice")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            element["class"] = ["tooltiptrigger"]
            for child in element.children:
                # transform child <orig> as part of the
                # <choice>-transformation
                if child.name == "orig":
                    element["class"].append("ttChanges")
                    element["class"].append("choice")
                    orig_span = child
                    orig_span.name = "span"
                    orig_span["class"] = ["tooltip"]
                    orig_span["class"].append("ttChanges")
                    # insert explanatory text in tooltip span
                    orig_span.insert(0, "original: ")
                    element.insert_after(orig_span)
                # transform child <expan> as part of the
                # <choice>-transformation
                # if <expan> is empty: unwrap both <expan>
                # and <choice>
                if child.name == "expan":
                    expan_contents = child.get_text()
                    if len(expan_contents) > 0:
                        element["class"].append("ttAbbreviations")
                        element["class"].append("abbr")
                        expan_span = child
                        expan_span.name = "span"
                        expan_span["class"] = ["tooltip"]
                        expan_span["class"].append("ttAbbreviations")
                        element.insert_after(expan_span)
                    else:
                        child.unwrap()
                        element.unwrap()
    # transform <reg>
    elements = html_soup.find_all("reg")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            del element["resp"]
            element["class"] = ["corr"]
            # @type="empty" means there is no corrected word to show
            if "type" in element.attrs:
                element["class"].append("corr_hide")
                empty_symbol = "&#8864;"
                empty_symbol = html.unescape(empty_symbol)
                element.insert(0, empty_symbol)
                del element["type"]
    # transform <abbr>
    elements = html_soup.find_all("abbr")
    if len(elements) > 0:
        for element in elements:
            # if parent <choice> has been transformed to this,
            # then <abbr> should be transformed too
            if element.parent.name == "span" and element.parent.attrs == {"class": ["tooltiptrigger", "ttAbbreviations", "abbr"]}:
                element.name = "span"
                element["class"] = "abbr"
            # if parent <choice> has been transformed to this,
            # then there was no sibling <expan> to <abbr>
            # and there's no meaning to keep the tooltiptrigger
            # and no use for <abbr>, only for its contents
            elif element.parent.name == "span" and element.parent.attrs == {"class": ["tooltiptrigger"]}:
                element.parent.unwrap()
                element.unwrap()
            # if there's no transformed parent <choice>,
            # then <abbr>'s sibling <expan> had no content
            # and <choice> has already been unwrapped as part
            # of that transformation
            # no use for <abbr>, only for its contents
            else:
                element.unwrap()
    # transform <foreign>
    elements = html_soup.find_all("foreign")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            element["class"] = ["tooltiptrigger"]
            element["class"].append("ttLang")
            language_span = html_soup.new_tag("span")
            language_span["class"] = ["tooltip"]
            language_span["class"].append("ttLang")
            language_span.insert(0, element.get("xml:lang"))
            element.insert_after(language_span)
            del element["xml:lang"]
    # transform <persName>
    elements = html_soup.find_all("persName")
    if len(elements) > 0:
        for element in elements:
            if "corresp" in element.attrs:
                corresp_value = element.get("corresp")
                if corresp_value.isdigit():
                    element["data-id"] = corresp_value
                    element.name = "span"
                    element["class"] = ["person"]
                    element["class"].append("tooltiptrigger")
                    element["class"].append("ttPerson")
                    del element["corresp"]
                else:
                    element.unwrap()
            else:
                element.unwrap()
    # transform <supplied>, add describing tooltip
    elements = html_soup.find_all("supplied")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            if "resp" in element.attrs:
                del element["resp"]
            element["class"] = ["choice"]
            element["class"].append("tooltiptrigger")
            element["class"].append("ttChanges")
            # in reading texts, supplied @type="gap" doesn't
            # differ from the ordinary supplied without attribute,
            # but @type="editorial" has its own class
            if "type" in element.attrs:
                if element["type"] == "gap":
                    element["class"].append("corr")
                if element["type"] == "editorial":
                    element["class"].append("editorial")
                del element["type"]
            else:
                element["class"].append("corr")
            explanatory_span = html_soup.new_tag("span")
            explanatory_span["class"] = ["tooltip"]
            explanatory_span["class"].append("ttChanges")
            # insert explanatory text in tooltip span
            explanatory_span.insert(0, "tillagt av utgivaren")
            element.insert_after(explanatory_span)
    # transform <xref>
    elements = html_soup.find_all("xref")
    if len(elements) > 0:
        for element in elements:
            # the type attribute is required, and either id or target
            # depending on the type of link
            if "type" in element.attrs and ("id" in element.attrs or "target" in element.attrs):
                xref_type = element.get("type")
                # we need a valid type value
                if xref_type == "":
                    element.unwrap()
                    continue
                element.name = "a"
                element["class"] = ["xreference"]
                # link to other texts on the site
                if (xref_type == "introduction" or xref_type == "readingtext") and "id" in element.attrs:
                    # id means a link to another text on the site
                    # in XML given as collection_id + "_" + publication_id 
                    # (+ possibly "_" and a pos-value)
                    xref_id = element.get("id")
                    # we need an id value
                    if xref_id == "":
                        element.unwrap()
                        continue
                    else:
                        xref_id = xref_id.replace("_", " ")
                        element["href"] = xref_id
                        del element["id"]
                    if xref_type == "introduction":
                        element["class"].append("ref_introduction")
                    if xref_type == "readingtext": 
                        element["class"].append("ref_readingtext")
                    del element["type"]
                # link to external site
                if xref_type == "ext" and "target" in element.attrs:
                    xref_target = element.get("target")
                    # we need an url
                    if xref_target == "":
                        element.unwrap()
                        continue
                    element["class"].append("ref_external")
                    del element["type"]
                    element["href"] = xref_target
                    del element["target"]
                # in case the type was paired with the wrong attribute (id/target)
                # e.g. type="readingtext" and target=""
                if not "href" in element.attrs:
                    element.unwrap()
            else:
                element.unwrap()
    # transform <address>
    elements = html_soup.find_all("address")
    if len(elements) > 0:
        for element in elements:
            element.name = "p"
            element["class"] = "address"
    # transform <dateline>
    elements = html_soup.find_all("dateline")
    if len(elements) > 0:
        for element in elements:
            element.name = "p"
            element["class"] = "dateline"
    # transform <salute>
    elements = html_soup.find_all("salute")
    if len(elements) > 0:
        for element in elements:
            element.name = "p"
            element["class"] = "salute"
    # transform <signed>
    elements = html_soup.find_all("signed")
    if len(elements) > 0:
        for element in elements:
            element.name = "p"
            element["class"] = "signed"
    # transform <del>
    # the tag and its contents shouldn't be present in reading text
    elements = html_soup.find_all("del")
    if len(elements) > 0:
        for element in elements:
            element.decompose()
    # transform <add>, add describing tooltip
    elements = html_soup.find_all("add")
    if len(elements) > 0:
        # nested <add> elements may cause problems: 
        # if the parent <add> is decomposed, the child <add> will be
        # None, and can't be iterated over
        # avoid this by decomposing after the iterations over elements
        elements_to_decompose = []
        for element in elements:
            # @type="later" and its contents shouldn't be present
            # in reading text
            # @type="moved" or no @type should just be unwrapped
            # @type="marginalia" is for additions that don't really
            # have a perfect place in the main text, so we might want to
            # highlight them in some way
            if "type" in element.attrs and element["type"] == "later":
                 elements_to_decompose.append(element)
            # if <add> is empty (due to it having contained only a <del>
            # which at this point has been decomposed): get rid of this <add>
            elif "type" in element.attrs and element["type"] == "marginalia":
                if len(element.contents) == 0: 
                    elements_to_decompose.append(element)
                else:
                    element.name = "span"
                    element["class"] = ["add"]
                    element["class"].append("marginalia")
                    element["class"].append("tooltiptrigger")
                    element["class"].append("ttMs")
                    del element["type"]
                    # insert explanatory text in tooltip span
                    explanatory_span = html_soup.new_tag("span")
                    explanatory_span["class"] = ["tooltip"]
                    explanatory_span["class"].append("ttMs")
                    explanatory_span.insert(0, "tillagt i marginalen")
                    element.insert_after(explanatory_span)
            else:
                element.unwrap()
        for element in elements_to_decompose:
            element.decompose()
    # transform <gap>, add describing tooltip
    elements = html_soup.find_all("gap")
    if len(elements) > 0:
        for element in elements:
            # @reason="overstrike" equals <del> in reading text
            if "reason" in element.attrs:
                element.decompose()
            else:
                element.name = "span"
                element["class"] = ["gap"]
                element["class"].append("tooltiptrigger")
                element["class"].append("ttMs")
                explanatory_span = html_soup.new_tag("span")
                explanatory_span["class"] = ["tooltip"]
                explanatory_span["class"].append("ttMs")
                # insert explanatory text in tooltip span
                explanatory_span.insert(0, "oläsligt")
                element.insert(0, "[...]")
                element.insert_after(explanatory_span)
    # transform <unclear>, add describing tooltip
    elements = html_soup.find_all("unclear")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            element["class"] = ["unclear"]
            element["class"].append("tooltiptrigger")
            element["class"].append("ttMs")
            # insert explanatory text in tooltip span
            explanatory_span = html_soup.new_tag("span")
            explanatory_span["class"] = ["tooltip"]
            explanatory_span["class"].append("ttMs")
            explanatory_span.insert(0, "svårtytt")
            element.insert_after(explanatory_span)
    # transform <div> and @type of divs
    # also handle footnotes <note> for each <div>
    elements = html_soup.find_all("div")
    if len(elements) > 0:
        for element in elements:
            if "type" in element.attrs:
                div_type_value = element["type"]
                if div_type_value == "chapter" or div_type_value == "section":
                    element.name = "section"
                else:
                    element["class"] = [div_type_value]
                    element["class"].append("tei")
                del element["type"]
                # these are subgroups to the hansard div
                # for the transformation of <p> we need
                # the top <div> value
                if div_type_value == "LM_written" or div_type_value == "LM_discussion" or div_type_value == "written" or div_type_value == "discussion":
                    div_type_value = "hansard" 
                # transform footnotes separately for each <div>
                # so that we can have different footnote lists
                # one list per <div>
                # if there's just one <div>, and it has content:
                # transform all of its notes
                if len(elements) == 1 and len(element.contents) > 1:
                    notes = html_soup.find_all("note")
                    if len(notes) > 0:
                        transform_footnotes(notes, html_soup)
                # if there's more than one <div>, and the <div>
                # we're looking at right now has content:
                # transform the notes of its (possible) subdivs separately
                elif len(elements) > 1 and len(element.contents) > 1:
                    for child in element.children:
                        if child.name == "div" and "type" in child.attrs:
                            notes = child.find_all("note")
                            if len(notes) > 0:
                                transform_footnotes(notes, html_soup)
                    # if there are notes both to the top div and to
                    # a subdiv, this fixes the notes for the top div
                    notes = html_soup.find_all("note")
                    if len(notes) > 0:
                        transform_footnotes(notes, html_soup)
                # files that only contain a template with an empty
                # div should get their own div class
                # this empty div will later on get transformed to an empty string 
                elif len(element.get_text(strip = True)) == 0:
                    div_type_value = "empty"
                    element["class"] = div_type_value
                else:
                    transform_footnotes(notes, html_soup)                    
            # <div> should always have @type, otherwise I have
            # no idea what it stands for and can't do anything
            # with it
            else:
                element.unwrap()
    # transform <note> if it's not a footnote but is used for
    # editors' explanations
    # footnotes were already transformed in
    # function transform_footnotes
    editorial_notes = html_soup.find_all("note")
    if len(elements) > 0:
        for editorial_note in editorial_notes:
            # editors' explanations have no attributes
            # this is the tooltip transformation, we need two new tags
            if editorial_note.attrs == {}:
                note_marker = html_soup.new_tag("img")
                note_marker["class"] = ["tooltiptrigger"]
                note_marker["class"].append("comment")
                note_marker["class"].append("ttComment")
                note_marker["tabindex"] = ["0"]
                note_marker["src"] = "images/asterisk.svg"
                html_editorial_note = html_soup.new_tag("span")
                html_editorial_note["class"] = ["tooltip"]
                html_editorial_note["class"].append("ttComment")
                html_editorial_note["class"].append("teiComment")
                html_editorial_note["class"].append("noteText")
                # we can't just use .get_text() for getting the note contents,
                # because we need to preserve all the tags in the note text,
                # such as <xref>
                # by replacing <note> with the new html_editorial_note tag,
                # we get the new span on its right place in the tree
                # and can use it to get the other new tag in place
                # but html_editorial_note has no content until we add the old
                # content back (old note tag + its content saved in editorial_note_content)
                # since we used the old tag just to conveniently keep all note
                # contents together, we finally have to unwrap editorial_note_content,
                # getting rid of that old tag
                editorial_note_content = editorial_note.replace_with(html_editorial_note)
                html_editorial_note.insert_before(note_marker)
                html_editorial_note.insert(0, editorial_note_content)
                editorial_note_content.unwrap()
    # transform <opener>
    elements = html_soup.find_all("opener")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = ["opener"]
            element["class"].append("tei")
    # transform <closer>
    elements = html_soup.find_all("closer")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = ["closer"]
            element["class"].append("tei")
    # transform <postscript>
    elements = html_soup.find_all("postscript")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = ["postscript"]
            element["class"].append("tei")
    # transform <table> by wrapping it in a specific <div>
    # do this after the general div transformation in order to
    # avoid this div being transformed twice, since it's not an
    # xml <div> but an html <div> added only for the purpose of
    # being able to style tables with a vertical scrollbar
    elements = html_soup.find_all("table")
    if len(elements) > 0:
        for element in elements:
            new_div = html_soup.new_tag("div")
            new_div["class"] = ["table-wrapper"]
            new_div["class"].append("tei")
            element.wrap(new_div)
    # files with no text content, consisting of just an empty <div>,
    # should return an empty string
    # this will produce a message on the site, explaining that
    # there's no text to show
    element = html_soup.find("div")
    if len(element) > 0 and element["class"] == "empty":
            html_string = ""
    # if there's no <div> at all in the file, this file's content
    # is not according to the rules for this project and should be ignored
    elif len(element) == 0:
        html_string = ""
    else:
        html_soup = prevent_empty_paragraphs(html_soup)
        html_string = str(html_soup)
        # make <a/> into <a></a> since it's not one of the
        # self-closing tags in html
        # the lxml parser and BS seem to make all empty elements
        # self-closing, with the trailing slash
        search_string = re.compile(r"(<a class.*?name.*?)/>")
        html_string = search_string.sub(r"\1></a>", html_string)
        # remove tabs
        search_string = re.compile(r"\t")
        html_string = search_string.sub("", html_string)
        # remove lines consisting only of <br/> (and possibly whitespace)
        search_string = re.compile(r"^ *(<br/>) *$", re.MULTILINE)
        html_string = search_string.sub("", html_string)
        # replace double/triple/etc. spaces
        search_string = re.compile(r"\s{2,}")
        html_string = search_string.sub(" ", html_string)
        # remove space before punctuation marks (unless ...)
        # situations like "word ," may happen when removing
        # deletions from the text, and we need to tidy this up
        search_string = re.compile(r"\s+(,|;|\.[^\.]|:|\?|!)")
        html_string = search_string.sub(r"\1", html_string)
        # content of element p shouldn't start/end with space
        search_string = re.compile(r"(<p.*?>) ?")
        html_string = search_string.sub(r"\1", html_string)
        search_string = re.compile(r" (</p>)")
        html_string = search_string.sub(r"\1", html_string)
    print("We have new soup.")
    return html_string

def transform_footnotes(notes, html_soup):
    # transform footnotes
    # a footnote will be transformed twice;
    # once for the tooltip and once for a list
    # of footnotes at the end of each text div
    # <note> tags other than footnotes are transformed
    # directly in transform_tags
    i = 0
    for note in notes:
        # sometimes editors forget to put @id in the <note>
        # if it still has @n, it's got to be a footnote
        # let's add the id so the transformation works
        if "n" in note.attrs and "id" not in note.attrs:
            id_value = i + 1
            id_value = "ftn" + str(id_value)
            note["id"] = id_value
        if "id" in note.attrs and "n" in note.attrs:
            # we need to keep a copy of the original <note>
            # for the second transformation
            original_note = copy.copy(note)
            # this is the tooltip transformation, we need three new tags
            note_id = note.get("id")
            # on the website it's possible to have a Swedish and a 
            # Finnish text next to each other, but if their footnotes 
            # have identical id:s the tooltips won't work as intended, 
            # showing content in the wrong language if the user chooses
            # a tooltip first in one text and then in the other
            # therefore we need to change the id:s for notes in one of 
            # the languages
            if LANGUAGE == "fi":
                note_nr = re.findall(r"\d+", note_id)
                if len(note_nr) > 0:
                    note_nr = int(note_nr[0])
                    note_nr += 500
                    note_id = "ftn" + str(note_nr)
            note_symbol = note.get("n")
            html_note = html_soup.new_tag("span")
            html_note["class"] = ["footnoteindicator"]
            html_note["class"].append("tooltiptrigger")
            html_note["class"].append("ttFoot")
            html_note["tabindex"] = ["0"]
            html_note["data-id"] = note_id
            html_note.insert(0, note_symbol)
            note_outer_span = html_soup.new_tag("span")
            note_outer_span["class"] = ["tooltip"]
            note_outer_span["class"].append("ttFoot")
            note_inner_span = html_soup.new_tag("span")
            note_inner_span["class"] = "ttFixed"
            note_inner_span["data-id"] = note_id
            # we can't just use .get_text() for getting the note contents,
            # because we need to preserve all the tags in the note text,
            # such as <persName> or <xref>
            # by replacing <note> with the new note_inner_span tag,
            # we get the new span on its right place in the tree
            # and can use it to get the other new tags in place
            # but note_inner_span has no content until we add the old
            # content back (old note tag + its content saved in note_content)
            # since we used the old tag just to conveniently keep all note
            # contents together, we finally have to unwrap note_content,
            # getting rid of that old tag
            note_content = note.replace_with(note_inner_span)
            note_inner_span.insert_before(html_note)
            note_inner_span.insert(0, note_content)
            note_inner_span.wrap(note_outer_span)
            note_content.unwrap()
            # this is the footnote list transformation:
            # <section><p></p><ol><li><p><a></a></p></li></ol></section>
            # if this is the first note in this <div>:
            # create the section and the list
            if i == 0:
                note_section = html_soup.new_tag("section")
                note_section["role"] = "doc-endnotes"
                for tag in html_note.parents:
                    if tag.name == "div":
                        tag.append("\n")
                        tag.append(note_section)
                        break
                # choose a heading for the list of notes
                # depending on language
                # reading texts can only have either sv or fi
                note_heading = html_soup.new_tag("p")
                if LANGUAGE == "sv":
                    note_heading.string = "Noter"
                else:
                    note_heading.string = "Viitteet"
                note_heading["class"] = "noIndent"
                note_section.append(note_heading)
                note_section.append("\n")
                note_list = html_soup.new_tag("ol")
                note_list["class"] = "footnotesList"
                note_section.append(note_list)
                note_list.append("\n")
            listed_note = html_soup.new_tag("li")
            listed_note["data-id"] = note_id
            listed_note["class"] = "footnoteItem"
            note_list.append(listed_note)
            original_note.name = "p"
            original_note.attrs = {}
            original_note["class"] = "noIndent"
            note_reference = html_soup.new_tag("a")
            note_reference["class"] = ["xreference"]
            note_reference["class"].append("footnoteReference")
            note_reference["href"] = "#" + note_id
            note_reference["role"] = "doc-backlink"
            note_reference.append(note_symbol)
            original_note.insert(0, note_reference)
            listed_note.append(original_note)
            note_list.append("\n")
            i += 1

# delete paragraphs and headings that have no content
def prevent_empty_paragraphs(html_soup):
    # if the content of a verse line has been deleted
    # remove that empty verse line span and its trailing <br/>
    elements = html_soup.find_all(attrs={"class": "l"})
    if len(elements) > 0:
        for element in elements:
            if len(element.contents) == 0:
                if element.next_sibling and element.next_sibling.name == "br":
                    element.next_sibling.decompose()
                element.decompose()
    elements = html_soup.find_all("p")
    if len(elements) > 0:
        for element in elements:
            if len(element.get_text(strip = True)) == 0:
                element.decompose()
    # if the content of a heading <head> has been deleted
    # e.g. due to it having contained only <del> or <add type="later"> 
    # remove that empty heading
    elements = html_soup.find_all(["h3", "h4", "h5", "h6"])
    if len(elements) > 0:
        for element in elements:
            if len(element.get_text(strip = True)) == 0:
                element.decompose()
    return html_soup

# create and save the new html file in another folder
def write_string_to_file(html_string, filename):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    html_filename = filename.replace(".xml", ".html")
    output_file = open(os.path.join(OUTPUT_FOLDER, html_filename), 'w', encoding='utf8')
    output_file.write(html_string)
    output_file.close()
    return html_filename

def main():
    file_list = get_source_file_paths()
    for file in file_list:
        xml_soup = read_xml(file)
        html_soup = create_html_file(xml_soup)
        html_string = transform_tags(html_soup)
        html_filename = write_string_to_file(html_string, file)
        print(html_filename + " created.")

main()