# This script transforms xml documents into html for the website.
# Works only for text type "ms normalized" (manuscripts/transcription)
# but without the manuscript changes visible, just the end
# result of the applied changes, such as all text tagged <del> gone.

import re
import os
from bs4 import BeautifulSoup

SOURCE_FOLDER = "documents/xml"
OUTPUT_FOLDER = "documents/html"

# loop through xml source files in folder and append to list
def get_source_file_paths():
    file_list = []
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".xml"):
            file_list.append(filename)
    return file_list

# read an xml file and return its content as a soup object
def read_xml(filename):
    with open (SOURCE_FOLDER + "/" + filename, "r", encoding="utf-8-sig") as source_file:
        file_content = source_file.read()
        # check for hyphens + line breaks
        # if they are present, replace them
        # before the file's content is made into a 
        # BeautifulSoup object
        # the (¬|­) below checks for either a not sign or
        # an (invisible) soft hyphen
        search_string = re.compile(r"(¬|­)<lb/>")
        match_string = re.search(search_string, file_content)
        if match_string:
            file_content = replace_hyphens(file_content)
        xml_soup = BeautifulSoup(file_content, "xml")
    print("We have old soup.")
    return xml_soup

# in the transcriptions for the manuscript column,
# each line of text is equivalent to the original manuscript's line,
# including its possible hyphens
# in the transcriptions, either hyphen minus or soft hyphen has been
# used as the kind of hyphen which is to disappear in the reading text,
# and the ¬ (not sign) has been used for a hyphen which is never to disappear
# let's make all hyphens uniform, and visible, by using only hyphen minus
# the (¬|­) below checks for either a not sign or an (invisible) soft hyphen
def replace_hyphens(file_content):
    search_string = re.compile(r"(¬|­)<lb/>")
    file_content = search_string.sub("-<lb/>", file_content)
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
    # transform <div> and @type of divs to @class
    elements = html_soup.find_all("div")
    if len(elements) > 0:
        for element in elements:
            if "type" in element.attrs:
                div_type_value = element["type"]
                element["class"] = div_type_value
                del element["type"]
                # these are subgroups to the @type="hansard" div
                # for the transformation of <p> we need
                # the top div value
                if div_type_value == "LM_written" or div_type_value == "LM_discussion" or div_type_value == "written" or div_type_value == "discussion":
                    div_type_value = "hansard"
    # transform <p> 
    elements = html_soup.find_all("p")
    if len(elements) > 0:
        for element in elements:
            if "rend" in element.attrs:
                rend_value = element["rend"]
                element["class"] = rend_value
                del element["rend"]
            if "type" in element.attrs:
                type_value = element["type"]
                element["class"] = type_value
                del element["type"]
    # transform <lb/>
    # in the transcriptions for the manuscript column, each line
    # of text is equivalent to the original manuscript's line
    # and the lines within a <p> ends with <lb/>
    elements = html_soup.find_all("lb")
    if len(elements) > 0:
        for element in elements:
            # @break="yes" is for preserving a line break
            # in the reading text
            if "break" in element.attrs:
                del element["break"]
            element.name = "br"
    # transform <pb/> 
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
    elements = html_soup.find_all("head")
    if len(elements) > 0:
        for element in elements:
            if "type" in element.attrs:
                type_value = element["type"]
                if type_value == "title":
                    element.name = "h1"
                    element["class"] = "title"
                if type_value == "section":
                    element.name = "h2"
                    element["class"] = "section"
                if type_value == "subchapter":
                    element.name = "h3"
                    element["class"] = "sub"
                if type_value == "subchapter2":
                    element.name = "h4"
                    element["class"] = "sub2"
                del element["type"]
            # in the xml files, the table header is placed inside
            # <table>; in html we need the header outside
            # of the table element
            elif element.parent.name == "table":
                new_header = html_soup.new_tag("h3")
                element.parent.insert_before(new_header)
                table_header = element.string.extract()
                element.extract()
                new_header.insert(0, table_header)
            # don't transform html tag <head>, just the xml <head>
            elif element.parent.name == "html":
                continue
            # <head> without attribute: chapter heading
            else:
                element.name = "h2"
                element["class"] = "chapter"
    # transform <row> (in <table>)
    # also transform cells in a row with @role="label"
    elements = html_soup.find_all("row")
    if len(elements) > 0:
        for element in elements:
            # @role="label" means cells are to be <th>, not <td>
            if "role" in element.attrs:
                for child in element.children:
                    child.name = "th"
                del element["role"]
            element.name = "tr"
    # transform <cell> (in <row> in <table>)
    elements = html_soup.find_all("cell")
    if len(elements) > 0:
        for element in elements:
            element.name = "td"
    # transform <list>
    elements = html_soup.find_all("list")
    if len(element) > 0:
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
                else:
                    element["class"] = element["rend"]
                    element.name = "em"
                del element["rend"]
            else:
                element.name = "em"
    # transform <milestone>
    elements = html_soup.find_all("milestone")
    if len(elements) > 0:
        for element in elements:
            element.name = "hr"
            if element["type"] == "editorial":
                element["class"] = "space"
            if element["type"] == "bar":
                element["class"] = "bar"
            del element["type"]
    # transform <anchor>
    # more is needed here!
    elements = html_soup.find_all("anchor")
    if len(elements) > 0:
        for element in elements:
            element.name = "a"
    # transform <choice>
    elements = html_soup.find_all("choice")
    if len(elements) > 0:
        for element in elements:
            for child in element.children:
                if child.name == "orig" or child.name == "reg":
                    element.unwrap()
                    break            
                else:
                    element.name = "span"
                    element["class"] = ["tooltiptrigger"]
                    element["class"].append("ttAbbreviations")
                    element["class"].append("abbr")
    # transform <orig>
    elements = html_soup.find_all("orig")
    if len(elements) > 0:
        for element in elements:
            element.unwrap()
    # transform <reg>
    elements = html_soup.find_all("reg")
    if len(elements) > 0:
        for element in elements:
            element.decompose()
    # transform <abbr>
    elements = html_soup.find_all("abbr")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            element["class"] = "abbr"
    # transform <expan>
    elements = html_soup.find_all("expan")
    if len(elements) > 0:
        for element in elements:
            element.name = "span"
            element["class"] = ["tooltip"]
            element["class"].append("ttAbbreviations")
    # transform <foreign>
    elements = html_soup.find_all("foreign")
    if len(elements) > 0:
        for element in elements:
            element.unwrap()
    # transform <note>
    elements = html_soup.find_all("note")
    if len(elements) > 0:
        for element in elements:
            # transform footnotes
            if ("id" and "n") in element.attrs:
                element.name = "span"
                note_content = element.get_text()
                element.clear()
                element["class"] = ["footnoteindicator"]
                element["class"].append("tooltiptrigger")
                element["class"].append("ttFoot")
                # this should be @data-id, but the platform adds
                # the "data-"-part
                note_id = element.get("id")
                element.insert(0, element.get("n"))
                del element["n"]
                comment_outer_span = html_soup.new_tag("span")
                comment_outer_span["class"] = ["tooltip"]
                comment_outer_span["class"].append("ttFoot")
                comment_inner_span = html_soup.new_tag("span")
                comment_inner_span["class"] = "ttFixed"
                # this should be @data-id, but the platform adds
                # the "data-"-part
                comment_inner_span["id"] = note_id
                comment_inner_span.string = note_content
                comment_outer_span.insert(0, comment_inner_span)
                element.insert_after(comment_outer_span)
            # transform editors' explanations
            else:
                element.name = "img"
                element["class"] = ["tooltiptrigger"]
                element["class"].append("comment")
                element["class"].append("ttComment")
                element["src"] = "images/asterix.svg"
                note_content = element.get_text()
                element.clear()
                comment_span = html_soup.new_tag("span")
                comment_span["class"] = ["tooltip"]
                comment_span["class"].append("ttComment")
                comment_span["class"].append("teiComment")
                comment_span["class"].append("noteText")
                comment_span.string = note_content
                element.insert_after(comment_span)
    # transform <persName>
    elements = html_soup.find_all("persName")
    if len(elements) > 0:
        for element in elements:
            element.unwrap()
    # transform <supplied>
    elements = html_soup.find_all("supplied")
    if len(elements) > 0:
        for element in elements:
            element.decompose()
    # transform <xref>
    elements = html_soup.find_all("xref")
    if len(elements) > 0:
        for element in elements:
            element.name = "a"
            if "type" in element.attrs:
                element["class"] = ["xreference"]
                if element["type"] == "introduction": 
                    element["class"].append("ref_introduction")
                if element["type"] == "readingtext": 
                    element["class"].append("ref_readingtext")
                # nonexistant in platform?
                if element["type"] == "manuscript": 
                    element["class"].append("ref_manuscript")
                del element["type"]
            if "id" in element.attrs:
                xref_id = element.get("id")
                element["href"] = xref_id
                del element["id"]
    # transform <opener>
    elements = html_soup.find_all("opener")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = "opener"
    # transform <closer>
    elements = html_soup.find_all("closer")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = "closer"
    # transform <postscript>
    elements = html_soup.find_all("postscript")
    if len(elements) > 0:
        for element in elements:
            element.name = "div"
            element["class"] = "postscript"
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
    # transform <add>
    elements = html_soup.find_all("add")
    if len(elements) > 0:
        for element in elements:
            element.unwrap()
    # transform <del>
    # the tag and its contents shouldn't be present
    # in the normalized manuscript view
    elements = html_soup.find_all("del")
    if len(elements) > 0:
        for element in elements:
            element.decompose()
    # transform <gap>
    elements = html_soup.find_all("gap")
    if len(elements) > 0:
        for element in elements:
            # @reason="overstrike" equals <del> in normalized view
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
                element.insert(1, explanatory_span)
    # transform <unclear>
    elements = html_soup.find_all("unclear")
    if len(elements) > 0:
        for element in elements:
            unclear_content = element.get_text()
            element.clear()
            element.name = "span"
            element["class"] = ["unclear"]
            element["class"].append("tooltiptrigger")
            element["class"].append("ttMs")
            element.insert(0, unclear_content)
            # insert explanatory text in tooltip span
            explanatory_span = html_soup.new_tag("span")
            explanatory_span["class"] = ["tooltip"]
            explanatory_span["class"].append("ttMs")
            explanatory_span.insert(0, "svårtytt")
            element.insert_after(explanatory_span)
    html_soup = prevent_empty_paragraphs(html_soup)
    html_string = str(html_soup)
    # remove tabs
    search_string = re.compile(r"\t")
    html_string = search_string.sub("", html_string)
    # remove lines consisting only of <br/> (and possibly whitespace)
    search_string = re.compile(r"^ *(<br/>) *$", re.MULTILINE)
    html_string = search_string.sub("", html_string)
    # replace double/triple/etc. spaces
    search_string = re.compile(r"\s{2,}")
    html_string = search_string.sub(" ", html_string)
    # remove space before punctuation marks
    # situations like "word ," may happen when removing
    # deletions from the text, and we need to tidy this up
    search_string = re.compile(r"\s+(,|;|\.|:|\?|!)")
    html_string = search_string.sub(r"\1", html_string)
    # content of element p shouldn't start/end with space
    search_string = re.compile(r"(<p.*?>) ?")
    html_string = search_string.sub(r"\1", html_string)
    search_string = re.compile(r" (</p>)")
    html_string = search_string.sub(r"\1", html_string)
    print("We have new soup.")
    return html_string

# delete paragraphs that have no content
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
            if len(element.get_text(strip=True)) == 0:
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