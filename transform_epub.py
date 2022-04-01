# This script transforms a Google Books epub into
# a single xml document, transforms the tags and gets
# rid of unnecessary clutter and useless info.
# There probably are many types of epubs produced
# by Google Books, but this script works well on 
# the ones I have encountered (19th century books,
# low-quality scan, low-quality e-book),
# such as:
# Storfurstendömet Finlands grundlagar jemte bihang
#
# For the project I'm working in, this is a way of
# being able to actually use that text and to enrich
# it further and make it more accessible. The resulting
# file will be used for non-commercial purposes only.
#
# This script should be run on an unzipped epub
# (change the .epub to .zip and then unzip it).
#
# The way of getting the files of the epub
# in the right order using the package file,
# function list_xhtml_file_paths,
# and the overall concept of working with epubs
# in this way I have very gratefully borrowed from
# Jonas Lillqvist (@jonaslil).
# 
# (The text content of an epub should be in xhtml files,
# but these epub content files are .xml, even though
# it's xhtml inside. If using this script on html, you
# should use another parser, such as lxml.)

import os
from bs4 import BeautifulSoup, Comment
import re

# path to unzipped epub
EPUB_FOLDER = r"C:\..\development\epub\Storfurstendömet_Finlands_grundlagar"
PACKAGE_FILE = os.path.join(EPUB_FOLDER, "OEBPS", "volume.opf")
NAVIGATION_FILE = os.path.join(EPUB_FOLDER, "OEBPS", "_page_map_.xml")
# tag that contains all the contents to be checked in a file;
# if it's <div> you'll need to change this script a bit
CONTAINER_ELEMENT = "body"
OUTPUT_FOLDER = r"C:\..\development\epub"

def read_file(filepath):
    with open(filepath, encoding="utf-8-sig") as source_file:
        content = source_file.read()
    return content

# there is a file containing a list of tags with page numbers
# and their href-values, e.g.:
# <page name="20" href="content/content-0021.xml#GBS.PA22" />
# make it into a dictionary that can be used for inserting
# the page numbers into the output xml file
def extract_page_numbers(page_soup):
    pages = page_soup.find_all("page")
    page_dict = {}
    for page in pages:
        name_value = page["name"]
        href_value = page["href"]
        search_string = re.compile(r".+#(.+)")
        href_value = search_string.sub(r"\1", href_value)
        page_dict[href_value] = name_value
    return page_dict

# template for content, could be more elaborate
def content_template():
    xml_template = '''
    <div type="article">
    </div>
    '''
    return BeautifulSoup(xml_template, "xml")

# create a list of paths of the content html files
# to ensure that the files are read in the right order,
# the script reads the itemrefs in the spine element,
# and then looks for the matching items in the manifest
def list_xhtml_file_paths(package_soup):
    spine = package_soup.find("spine")
    itemrefs = spine.find_all("itemref")
    for itemref in itemrefs:
        # get the value of the idref attribute of the itemref
        # in the spine
        idref = itemref["idref"]
        # find the item in the manifest with a matching id
        item = package_soup.find(id=idref)
        yield item["href"]

# go through the xml elements, attributes and values
# from the source file and transform them as needed
def transform_xml(container_soup, page_dict):
    elements = container_soup.find_all("div")
    if len(elements) > 0:
        for element in elements:
            if "class" in element.attrs:
                div_value = element["class"]
                if div_value == "title":
                    element.name = "head"
                    del element["class"]
                    element["type"] = "title"
                elif div_value == "author" or div_value == "notice":
                    element.decompose()
                else:
                    element.unwrap()
            else:
                element.unwrap()
    elements = container_soup.find_all("img")
    if len(elements) > 0:
        for element in elements:
            element.decompose()
    elements = container_soup.find_all("p")
    if len(elements) > 0:
        for element in elements:
            if "style" in element.attrs:
                style_value = element["style"]
                if style_value == "text-indent:1em;" or style_value == "font-size:101%;text-indent:1em;":
                    element.attrs = {}
                elif style_value == "text-align:right;":
                    element.attrs = {}
                    element["rend"] = "right"
                elif style_value == "text-align:center;":
                    element.attrs = {}
                    element["rend"] = "center"
                else:
                    element.attrs = {}
                    element["rend"] = "noIndent"
            else:
                element.attrs = {}
                element["rend"] = "noIndent"
    # <a class="page"> with @id is equivalent to a <pb/>
    elements = container_soup.find_all("a")
    if len(elements) > 0:
        for element in elements:
            if "class" not in element.attrs:
                element.decompose()
            else:
                del element["class"]
                id_value = element["id"]
                del element["id"]
                # use the newly made dictionary to get
                # the page number (value of @n)
                n_value = page_dict[id_value]
                element["n"] = n_value
                element["type"] = "orig"
                element.name = "pb"
    elements = container_soup.find_all("span")
    if len(elements) > 0:
        for element in elements:
            if "style" in element.attrs:
                del element["style"]
                element.name = "hi"
            else:
                element.unwrap()
    elements = container_soup.find_all("br")
    if len(elements) > 0:
        for element in elements:
            element.name = "lb"
            element["break"] = "yes"
    # get rid of all <!-- --> comments in the file
    comments = container_soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    return container_soup

def tidy_up_xml(xml_string):
    # get rid of tabs, extra spaces and newlines,
    search_string = re.compile(r"\n\t{1,7}|\n\s{1,30}")
    xml_string = search_string.sub(" ", xml_string)
    search_string = re.compile(r"\n|\t|\s{2,}")
    xml_string = search_string.sub("", xml_string)
    # add newlines as preferred
    search_string = re.compile(r"(<div.*?>)")
    xml_string = search_string.sub(r"\n\1\n", xml_string)
    search_string = re.compile(r"(</head>|</p>|<lg>|</lg>|</l>|<table>|</table>|</row>|<list>|</list>|</item>|</div>)")
    xml_string = search_string.sub(r"\1\n", xml_string)
    # delete space before <pb/> and <lb/>
    search_string = re.compile(r"( )((<pb|<lb) .+?/>)")
    xml_string = search_string.sub(r"\2", xml_string)
    # add newline after <pb/> if followed by p-like content
    search_string = re.compile(r"(<pb .+?/>) *(<p|<lg>|<list>|<table>)")
    xml_string = search_string.sub(r"\1\n\2", xml_string)
    # add space before ... if preceeded by a word character
    # remove space between full stops and standardize two full stops to three
    search_string = re.compile(r"(\w) *\. *\.( *\.)?")
    xml_string = search_string.sub(r"\1 ...", xml_string)
    # add Narrow No-Break Space in numbers over 999
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3&#x202F;\5", xml_string)
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3", xml_string)
    # the asterisk stands for a footnote
    search_string = re.compile(r" *\*\) *")
    xml_string = search_string.sub("<note n=\"*)\"></note>", xml_string)
    # remove extra <hi> markup
    search_string = re.compile(r" </hi><hi>")
    xml_string = search_string.sub(" ", xml_string)
    # remove extra <hi> markup
    search_string = re.compile(r"</hi><hi>")
    xml_string = search_string.sub("", xml_string)
    # fix spacing around <hi>
    search_string = re.compile(r" </hi>(\w)")
    xml_string = search_string.sub(r"</hi> \1", xml_string)
    # remove spaces at the beginning of lines
    search_string = re.compile(r"^ +<", re.MULTILINE)
    xml_string = search_string.sub("<", xml_string)
    # these paragraphs should be one, not two
    search_string = re.compile(r"</p>\n(<pb n=\"\d+\" type=\"orig\"/>)\n<p rend=\"noIndent\">")
    xml_string = search_string.sub(r"\1 ", xml_string)
    # standardize certain characters
    xml_string = xml_string.replace("„", "”")
    xml_string = xml_string.replace("‟", "”")
    xml_string = xml_string.replace("“", "”")
    xml_string = xml_string.replace("»", "”")
    xml_string = xml_string.replace("«", "”")
    xml_string = xml_string.replace("—", "–")
    xml_string = xml_string.replace("\'", "’")
    xml_string = xml_string.replace("’’", "”")
    xml_string = xml_string.replace("´", "’")
    print("XML tidied.")
    return xml_string

# save the new xml file in another folder
def write_to_file(tidy_xml_string, filename):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    output_file = open(os.path.join(OUTPUT_FOLDER, filename), "w", encoding="utf-8-sig")
    output_file.write(tidy_xml_string)
    output_file.close()

def main():
    package_soup = BeautifulSoup(read_file(PACKAGE_FILE), "xml")
    page_soup = BeautifulSoup(read_file(NAVIGATION_FILE), "xml")
    page_dict = extract_page_numbers(page_soup)
    new_soup = content_template()
    for filepath in list_xhtml_file_paths(package_soup):
        full_path = os.path.join(EPUB_FOLDER, "OEBPS", filepath)
        file_soup = BeautifulSoup(read_file(full_path), "xml")
        # find the first element with the tag name defined by CONTAINER_ELEMENT
        container_soup = file_soup.find(CONTAINER_ELEMENT)
        container_soup = transform_xml(container_soup, page_dict)
        new_soup.div.append(container_soup)
        new_soup.find(CONTAINER_ELEMENT).unwrap()
    tidy_xml_string = tidy_up_xml(str(new_soup))
    write_to_file(tidy_xml_string, "result.xml")

main()
