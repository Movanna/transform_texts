# This script transforms the project's original xml documents
# into txt for the download feature on the website.
# The downloadable text types are "est" (reading text, the main edited text)
# and "ms" (manuscript/transcription), and this script works for both types.

import re
from bs4 import BeautifulSoup

# read an xml file and return its content as a soup object
# also handle hyphens and line breaks
from src.transform_downloadable_xml import read_xml

def create_html_template():
    html_doc = '''
    <!DOCTYPE html>
    <html lang="sv">
    <head>
    <meta charset="UTF-8">
    <title></title>
    </head>
    <body>
    </body>
    </html>
    '''
    html_soup = BeautifulSoup(html_doc, "lxml")
    return html_soup

def create_html_soup(xml_soup):
    html_soup = create_html_template()
    # transfer xml body to html body, and get rid of xml body tag
    xml_body = xml_soup.body
    html_soup.body.append(xml_body)
    html_soup.body.body.unwrap()
    return html_soup

# go through the elements, attributes and values
# and transform them as needed
def transform_tags(html_soup, est_or_ms):
    # transform <lb/>
    # if the xml file is an ms, we should get rid of all
    # line division and the hyphenation of words in line breaks
    # most of the transformation of hyphens and line breaks
    # was already handled by read_xml, which calls different
    # other functions for doing that
    elements = html_soup.find_all("lb")
    if len(elements) > 0:
        for element in elements:
            # if <lb/> is followed by <pb/>, remove it
            if element.next_sibling and element.next_sibling.name == "pb":
                element.decompose()
            # replace <lb/> with a space
            else:
                element.replace_with(" ")
    # unwrap these elements, leave their contents
    if est_or_ms == "est":
        unwrap_elements = [
            "choice",
            "closer",
            "div",
            "expan",
            "foreign",
            "hi",
            "lg",
            "list",
            "opener",
            "persName",
            "postscript",
            "reg",
            "row",
            "supplied",
            "table",
            "unclear",
            "xref"
        ]
    if est_or_ms == "ms":
        unwrap_elements = [
            "abbr",
            "choice",
            "closer",
            "div",
            "foreign",
            "hi",
            "lg",
            "list",
            "opener",
            "orig",
            "persName",
            "postscript",
            "row",
            "table",
            "unclear",
            "xref"
        ]
    for tag in unwrap_elements:
        elements = html_soup.find_all(tag)
        if len(elements) > 0:
            for element in elements:
                element.unwrap()
    # add a space after these elements and then unwrap them,
    # leaving their contents
    # if we don't add a space the content of these elements
    # will stick together with other content, so we may get
    # "Wordword" instead of "Word word" as the result
    unwrap_and_add_space_elements = [
        "address",
        "cell",
        "dateline",
        "head",
        "item",
        "l",
        "p",
        "salute",
        "signed"
    ]
    for tag in unwrap_and_add_space_elements:
        elements = html_soup.find_all(tag)
        if len(elements) > 0:
            for element in elements:
                element.append(" ")
                element.unwrap()
    # decompose these elements, i.e. delete them and all their contents
    if est_or_ms == "est":
        decompose_elements = [
            "anchor",
            "abbr",
            "del",
            "gap",
            "milestone",
            "orig",
            "pb"
        ]
    if est_or_ms == "ms":
        decompose_elements = [
            "anchor",
            "del",
            "expan",
            "gap",
            "milestone",
            "pb",
            "reg",
            "supplied"
        ]
    for tag in decompose_elements:
        elements = html_soup.find_all(tag)
        if len(elements) > 0:
            for element in elements:
                element.decompose()
    # unwrap or decompose depending on element and attributes
    unwrap_or_decompose_elements = [
        "add",
        "note"
    ]
    for tag in unwrap_or_decompose_elements:
        elements = html_soup.find_all(tag)
        if len(elements) > 0:
            for element in elements:
                if element.name == "add":
                    if est_or_ms == "est":
                        # @type="later" and its contents shouldn't be present
                        # in the reading text,
                        # since they've often been added by archive staff
                        # and not necessarily at the time the document was written
                        if "type" in element.attrs and element["type"] == "later":
                            element.decompose()
                        else:
                            element.unwrap()
                    if est_or_ms == "ms":
                        # the output for an ms is allowed to contain later additions
                        element.unwrap()
                if element.name == "note":
                    # footnotes have attributes, editorial notes don't
                    # decompose editorial notes
                    if element.attrs != {}:
                        element.insert(0, " ")
                        element.unwrap()
                    else:
                        element.decompose()
    html_soup = html_soup.body
    html_string = str(html_soup)
    # remove <body>
    search_string = re.compile(r"<body>|</body>")
    html_string = search_string.sub("", html_string)
    # remove tabs and newlines
    search_string = re.compile(r"\t|\n")
    html_string = search_string.sub("", html_string)
    # replace double/triple/etc. spaces with single space
    search_string = re.compile(r"\s{2,}")
    html_string = search_string.sub(" ", html_string)
    # remove space before punctuation marks (unless ...)
    # situations like "word ," may happen when removing
    # deletions from the text, and we need to tidy this up
    search_string = re.compile(r"\s+(,|;|\.[^\.]|:|\?|!)")
    html_string = search_string.sub(r"\1", html_string)
    # remove leading/trailing whitespace
    html_string = html_string.strip()
    if html_string == "":
        return ""
    else:
        return html_string

def transform_to_txt(filename, est_or_ms):
    xml_soup = read_xml(filename)
    html_soup = create_html_soup(xml_soup)
    txt_content = transform_tags(html_soup, est_or_ms)
    return txt_content