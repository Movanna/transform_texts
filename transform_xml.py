# This script transforms xml documents into more suitably
# formatted ones.

import re
import os
from bs4 import BeautifulSoup

SOURCE_FOLDER = "documents/bad_xml"
OUTPUT_FOLDER = "documents/good_xml"
# document_type includes: letter, article, misc
DOCUMENT_TYPE = "article"

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
        old_soup = BeautifulSoup(file_content, "xml")
    print("We have old soup.")
    return old_soup

# get body from source xml and combine with template
# go through certain elements, attributes and values
# and transform them
def transform_xml(old_soup):
    xml_body = old_soup.find("body")
    if DOCUMENT_TYPE == "letter":
        new_soup = letter_content_template()
        new_soup.div.opener.insert_after(xml_body)
        new_soup.body.unwrap()
    elif DOCUMENT_TYPE == "misc":
        new_soup = misc_content_template()
        new_soup.div.append(xml_body)
        new_soup.body.unwrap()
    else:
        new_soup = content_template()
        new_soup.div.append(xml_body)
        new_soup.body.unwrap()
    pbs = new_soup.find_all("pb")
    if len(pbs) > 0:
        for pb in pbs:
            if "facs" in pb.attrs:
                del pb["facs"]
            if "xml:id" in pb.attrs:
                del pb["xml:id"]
            pb["type"] = "orig"
    ps = new_soup.find_all("p")
    if len(ps) > 0:
        for p in ps:
            if "facs" in p.attrs:
                del p["facs"]
            if "style" in p.attrs:
                del p["style"]
            if "rend" in p.attrs:
                value = p["rend"]
                if value == "Quote":
                    p["rend"] = "parIndent"
                if value == "Leipäteksti_ei_sisennetty" and DOCUMENT_TYPE == "letter":
                    del p["rend"]
                    continue
                if value == "Leipäteksti_ei_sisennetty":
                    p["rend"] = "noIndent"
                if value == "footnote text":
                    p.unwrap()
                if value == "Subtitle":
                    del p["rend"]
                    p["type"] = "subtitle"
                if value == "Runo":
                    del p["rend"]
                    p.name = "lg"
                if value == "Kirjekappale":
                    p.wrap(new_soup.new_tag("opener"))
                if value == "Standard":
                    del p["rend"]
                if value == "color(#222222)":
                    del p["rend"]
    # it's possible to export prose from Transkribus OCR
    # encoded as p + lg + l
    # since it's not verse, but prose: delete l and lg
    # and set a flag, so we can combine the lines correctly
    # later on and then get rid of line breaks and hyphens
    false_l = False
    ls = new_soup.find_all("l")
    if len(ls) > 0:
        for l in ls:
            if "rend" in l.attrs:
                if l["rend"] == "indent":
                    del l["rend"]
            parent_p = l.find_parent("p")
            if parent_p:
                l.unwrap()
                false_l = True
    if false_l:
        lgs = new_soup.find_all("lg")
        for lg in lgs:
            lg.unwrap()
    lbs = new_soup.find_all("lb")
    if len(lbs) > 0:
        for lb in lbs:
            if "facs" in lb.attrs:
                del lb["facs"]
            if "n" in lb.attrs:
                del lb["n"]
    heads = new_soup.find_all("head")
    if len("head") > 0:
        for head in heads:
            if "rend" in head.attrs:
                head["type"] = head["rend"]
                del head["rend"]
            i = 0
            for parent in head.parents:
                if parent.name == "div":
                    i += 1
            if i <= 2:
                head["level"] = "1"
            if i == 3:
                head["level"] = "2"
            if i == 4:
                head["level"] = "3"
            if i == 5:
                head["level"] = "4"
    tables = new_soup.find_all("table")
    if len(tables) > 0:
        for table in tables:
            if "rend" in table.attrs:
                del table["rend"]
    cells = new_soup.find_all("cell")
    if len(cells) > 0:
        for cell in cells:
            if "style" in cell.attrs:
                del cell["style"]
            if "rend" in cell.attrs:
                value = cell["rend"]
                if value == "Body_Text background-color(FAFAFA)" or value == "Leipäteksti_ei_sisennetty background-color(FAFAFA)":
                    del cell["rend"]
    lists = new_soup.find_all("list")
    if len(lists) > 0:
        for list in lists:
            if "type" in list.attrs:
                del list["type"]
    his = new_soup.find_all("hi")
    if len(his) > 0:
        for hi in his:
            if "rend" in hi.attrs and "style" in hi.attrs:
                del hi["style"]
                value = hi["rend"]
                match_string = re.search("color", value)
                if match_string:
                    search_string = re.compile(r"\s*color\(.*\)")
                    value = search_string.sub("", value)
                    if value == "":
                        hi.unwrap()
                        continue
                    else:
                        hi["rend"] = value
                if value == "italic bold":
                    hi["rend"] = "boldItalic"
                match_string = re.search("subscript", value)
                if match_string:
                    hi["rend"] = "sub"
                match_string = re.search("underlined", value)
                if match_string:
                    del hi["rend"]
                match_string = re.search("super", value)
                if match_string:
                    hi["rend"] = "raised"
                match_string = re.search("strikethrough", value)
                if match_string:
                    del hi["rend"]
                    hi.name = "tag"
                match_string = re.search("italic", value)
                if match_string or value == "italic":
                    del hi["rend"]
                if value == "Harvennettu":
                    hi["rend"] = "expanded"
                if value == "Vieraskielinen":
                    del hi["rend"]
                    hi.name = "foreign"
                if value == "Emphasis":
                    del hi["rend"]
            if "rend" in hi.attrs:
                value = hi["rend"]
                match_string = re.search("color", value)
                if match_string:
                    search_string = re.compile(r"\s*color\(.*\)")
                    value = search_string.sub("", value)
                    if value == "":
                        hi.unwrap()
                        continue
                    else:
                        hi["rend"] = value
                if value == "italic bold":
                    hi["rend"] = "boldItalic"
                match_string = re.search("subscript", value)
                if match_string:
                    hi["rend"] = "sub"
                match_string = re.search("underlined", value)
                if match_string:
                    del hi["rend"]
                match_string = re.search("super", value)
                if match_string:
                    hi["rend"] = "raised"
                match_string = re.search("strikethrough", value)
                if match_string:
                    del hi["rend"]
                    hi.name = "tag"
                match_string = re.search("italic", value)
                if match_string or value == "italic":
                    del hi["rend"]
                if value == "Harvennettu":
                    hi["rend"] = "expanded"
                if value == "Vieraskielinen":
                    del hi["rend"]
                    hi.name = "foreign"
                if value == "Emphasis":
                    del hi["rend"]
            if "xml:space" in hi.attrs:
                del hi["xml:space"]
            if "style" in hi.attrs:
                hi.unwrap()
    segs = new_soup.find_all("seg")
    if len(segs) > 0:
        for seg in segs:
            if "xml:space" in seg.attrs:
                del seg["xml:space"]
            if "rend" in seg.attrs:
                value = seg["rend"]
                match_string = re.search("italic bold", value)
                if match_string:
                    seg["rend"] = "boldItalic"
                    seg.name = "hi"
                if value == "italic":
                    del seg["rend"]
                    seg.name = "hi"
                if value == "color(222222)":
                    seg.unwrap()
    refs = new_soup.find_all("ref")
    if len(refs) > 0:
        for ref in refs:
            if "target" in ref.attrs:
                ref["type"] = "readingtext"
                del ref["target"]
                ref["id"] = ""
                ref.name = "xref"
    abs = new_soup.find_all("ab")
    if len(abs) > 0:
        for ab in abs:
            if "facs" in ab.attrs:
                del ab["facs"]
            if "type" in ab.attrs:
                del ab["type"]
            ab.name = "p"
    notes = new_soup.find_all("note")
    if len(notes) > 0:
        for note in notes:
            if "place" in note.attrs:
                del note["place"]
            if "xml:id" in note.attrs:
                note["id"] = note["xml:id"]
                del note["xml:id"]
    supplieds = new_soup.find_all("supplied")
    if len(supplieds) > 0:
        for supplied in supplieds:
            if "reason" in supplied.attrs:
                del supplied["reason"]
    comments = new_soup.find_all("comment")
    if len(comments) > 0:
        for comment in comments:
            comment.name = "note"
    tags = new_soup.find_all("tag")
    if len(tags) > 0:
        for tag in tags:
            if tag.string is not None and (str(tag.previous_element) == str("<del><tag>" + tag.string + "</tag></del>") or str(tag.next_element) == str("<del>" + tag.string + "</del>")):
                tag.unwrap()
            else:
                tag.name = "del"
    print("We have new soup.")
    return new_soup, false_l

# the new XML files contain a template
# this one is for letters
# all templates could be more elaborate, but the resulting
# documents are anyway just temporary and file content
# will be copypasted from them into its final file elsewhere
def letter_content_template():
    xml_template = '''
    <div type="letter">
    <opener>
    <dateline></dateline>
    <salute></salute>
    </opener>
    <closer>
    <salute></salute>
    <signed></signed>
    </closer>
    </div>
    '''
    return BeautifulSoup(xml_template, "xml")

# this template is for misc publications (manuscripts, but not letters)
def misc_content_template():
    xml_template = '''
    <div type="misc">
    </div>
    '''
    return BeautifulSoup(xml_template, "xml")

# this template is for articles
def content_template():
    xml_template = '''
    <div type="article">
    </div>
    '''
    return BeautifulSoup(xml_template, "xml")

# get rid of tabs, extra spaces and newlines
# add newlines as preferred
# fix common problems caused by OCR programs, editors or
# otherwise present in source files
def tidy_up_xml(xml_string, false_l):
    # it's possible to export prose from Transkribus OCR
    # encoded as p + lg + l
    # since it's not verse, but prose:
    # we must combine the lines correctly
    # and get rid of line breaks and hyphens
    if false_l:
        search_string = re.compile(r"-\n")
        xml_string = search_string.sub("", xml_string)
        search_string = re.compile(r"\n")
        xml_string = search_string.sub(" ", xml_string)
        search_string = re.compile(r"\t{1,7}|\s{2}")
        xml_string = search_string.sub("", xml_string)
    elif DOCUMENT_TYPE == "letter" or DOCUMENT_TYPE == "misc":
        # get rid of tabs, extra spaces and newlines
        search_string = re.compile(r"\n|\t|\s{2,}")
        xml_string = search_string.sub("", xml_string)
    elif DOCUMENT_TYPE == "letter":
        search_string = re.compile(r"(</opener>|</closer>)")
        xml_string = search_string.sub(r"\1\n", xml_string)
    else:
        # get rid of tabs, extra spaces and newlines,
        # but differently from letters
        search_string = re.compile(r"\n\t{1,7}|\n\s{1,30}")
        xml_string = search_string.sub(" ", xml_string)
        search_string = re.compile(r"\n|\t|\s{2,}")
        xml_string = search_string.sub("", xml_string)
    # add newlines as preferred
    search_string = re.compile(r"(<div.*?>)")
    xml_string = search_string.sub(r"\n\1\n", xml_string)
    search_string = re.compile(r"(</head>|</p>|<lg>|</lg>|</l>|<table>|</table>|</row>|<list>|</list>|</item>|</div>)")
    xml_string = search_string.sub(r"\1\n", xml_string)
    # <p> shouldn't be followed by <lb/>
    search_string = re.compile(r"(<p .+?>|<p>)<lb/>")
    xml_string = search_string.sub(r"\1", xml_string)
    # add newline after <lb/> (and get rid of trailing space)
    search_string = re.compile(r" *<lb/> *")
    xml_string = search_string.sub("<lb/>\n", xml_string)
    if DOCUMENT_TYPE == "misc":
        # get rid of newline just before end of <p>
        search_string = re.compile(r"<lb/>\n</p>")
        xml_string = search_string.sub("</p>", xml_string)
    # these are non-wanted No-Break Spaces,
    # a result of copypaste in the source document
    search_string = re.compile(r" ")
    xml_string = search_string.sub(" ", xml_string)
    # delete space before <pb/>
    search_string = re.compile(r"( )(<pb .+?/>)")
    xml_string = search_string.sub(r"\2", xml_string)
    # add newline after <pb/> if followed by p-like content
    search_string = re.compile(r"(<pb .+?/>) *(<p|<lg>|<list>|<table>)")
    xml_string = search_string.sub(r"\1\n\2", xml_string)
    # add space before ... if preceeded by a word character
    # remove space between full stops and standardize two full stops to three
    search_string = re.compile(r"(\w) *\. *\.( *\.)?")
    xml_string = search_string.sub(r"\1 ...", xml_string)
    # let <hi> continue instead of being broken up into several <hi>:s
    search_string = re.compile(r"</hi><lb/>\n<hi>")
    xml_string = search_string.sub(r"<lb/>\n", xml_string)
    # add Narrow No-Break Space in numbers over 999
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3&#x202F;\5", xml_string)
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3", xml_string)
    # the asterisk stands for a footnote
    search_string = re.compile(r" *\*\) *")
    xml_string = search_string.sub("<note id=\"\" n=\"*)\"></note>", xml_string)
    # replace certain characters
    search_string = re.compile(r"&quot;")
    xml_string = search_string.sub("”", xml_string)
    search_string = re.compile(r"&apos;")
    xml_string = search_string.sub("’", xml_string)
    search_string = re.compile(r"º|°")
    xml_string = search_string.sub("<hi rend=\"raised\">o</hi>", xml_string)
    # there should be a non-breaking space before %
    search_string = re.compile(r"([^  ])%")
    xml_string = search_string.sub(r"\1&#x00A0;%", xml_string)
    search_string = re.compile(r" %")
    xml_string = search_string.sub(r"&#x00A0;%", xml_string)
    # content of element note shouldn't start with space
    search_string = re.compile(r"(<note .+?>) ")
    xml_string = search_string.sub(r"\1", xml_string)
    # remove spaces at the beginning of lines
    search_string = re.compile(r"^ +<", re.MULTILINE)
    xml_string = search_string.sub("<", xml_string)
    if DOCUMENT_TYPE == "article":
    # there shouldn't be line breaks like these in articles
        search_string = re.compile(r"-<lb/>\n")
        xml_string = search_string.sub("", xml_string)
        search_string = re.compile(r"<lb/>\n")
        xml_string = search_string.sub(" ", xml_string)
    # " should be used only in elements, not in element contents
    # i.e. the text of the document should use ” (&#x201d;
    # Right Double Quotation Mark) as the character for quotation
    # marks, but it's very common to use " (&#x22;) and we need
    # to replace those " without touching the ones around attribute
    # values and thus destroying the code
    # my best take on this is to first replace all tags with something
    # completely different, then replace quotation marks in the
    # remaining text, and finally put the tags back where they
    # once were
    # first find all tags and thus also the " they may contain
    search_string = re.compile(r"<.*?>")
    result = re.findall(search_string, xml_string)
    tag_replacement = "€"
    # replace all tags temporarily
    for tag in result:
        xml_string = xml_string.replace(tag, tag_replacement, 1)
    # replace the remaining ", because we now know they all
    # should be replaced
    xml_string = xml_string.replace('"', "”")
    result_2 = re.findall(tag_replacement, xml_string)
    # replace the first occurrence of the tag_replacement with
    # the first tag in the original result list, and so on
    # after this, tags are back in their places and there are
    # no " in the text, just ”
    i = 0
    for occurrence in result_2:
        xml_string = xml_string.replace(tag_replacement, result[i], 1)
        i += 1
    # remove empty <p/>
    xml_string = xml_string.replace("<p/>", "")
    # finally standardize certain other characters
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
    file_list = get_source_file_paths()
    for file in file_list:
        old_soup = read_xml(file)
        new_soup, false_l = transform_xml(old_soup)
        tidy_xml_string = tidy_up_xml(str(new_soup), false_l)
        write_to_file(tidy_xml_string, file)
        print(file + " created.")

main()