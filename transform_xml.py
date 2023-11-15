# This script transforms XML documents into more suitably
# formatted ones. It's tailored for documents that are 
# either exported from Transkribus or converted from word 
# processor documents with TEIGarage Conversion.

# It also adds expansions to unexpanded abbreviations in 
# the texts: either to abbreviations encoded as 
# <choice><abbr>Dr</abbr><expan/></choice>
# or not encoded at all (option CHECK_UNTAGGED_ABBREVIATIONS).
# For this we need the abbr_dictionary created by
# create_abbr_dictionary.py.

import re
import os
from bs4 import BeautifulSoup
import json

SOURCE_FOLDER = "documents/bad_xml"
OUTPUT_FOLDER = "documents/good_xml"
# document_type includes: letter, article, misc
DOCUMENT_TYPE = "article"
# if True: look for unencoded abbreviations and
# surround them with the needed tags as well as
# add the likely expansions
CHECK_UNTAGGED_ABBREVIATIONS = True
# if True: correct falsely inserted <p> elements
# due to Transkribus often interpreting (shorter) 
# lines of text as separate paragraphs, even though 
# they aren't
CORRECT_P = False

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

# get dictionary content from file
def read_dict_from_file(filename):
    with open(filename, encoding="utf-8-sig") as source_file:
        json_content = json.load(source_file)
        return json_content

# get body from source xml and combine with template
# go through certain elements, attributes and values
# and transform them
def transform_xml(old_soup, abbr_dictionary):
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
            if hi.attrs == {} and DOCUMENT_TYPE != "article":
                hi["rend"] = "raised"
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
                if value == "Lisätty_marginaaliin":
                    del hi["rend"]
                    hi["type"] = "marginalia"
                    hi.name = "add"
            if "xml:space" in hi.attrs:
                del hi["xml:space"]
            if "style" in hi.attrs:
                value = hi["style"]
                match_string = re.search("super", value)
                if match_string:
                    hi["rend"] = "raised"
                    del hi["style"]
                elif value == "text-decoration: underline;":
                    del hi["style"]
                else:
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
    choices = new_soup.find_all("choice")
    # it's easy to mark up abbreviations in Transkribus
    # this gets exported as <choice><abbr>Tit.</abbr><expan/></choice>
    # if we have a recorded expansion for the abbreviation:
    # add this expansion 
    if len(choices) > 0:
        # by handling one <choice> at a time we can get <abbr>
        # and <expan> as a pair
        for choice in choices:
            for child in choice.children:
                # we don't want to change <abbr> in any way,
                # we just need its content in order to check
                # the abbr_dictionary for a possible expansion
                if child.name == "abbr":
                    abbr = child
                    abbr_content = str(abbr)
                    abbr_content = abbr_content.replace("<abbr>", "")
                    abbr_content = abbr_content.replace("</abbr>", "")
                    if abbr_content in abbr_dictionary.keys():
                        expan_content = abbr_dictionary[abbr_content]
                        # now get the <expan> to update
                        for child in choice.children:
                            # only add content to an empty <expan>
                            if child.name == "expan" and len(child.contents) == 0:
                                child.insert(0, expan_content)
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
def tidy_up_xml(xml_string, false_l, abbr_dictionary):
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
    # for numbers over 999 that have normal space or comma as separator:
    # replace those separators with Narrow No-Break Space
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3&#x202F;\5", xml_string)
    search_string = re.compile(r"(\d{1,3})( |,)(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\3", xml_string)
    # add Narrow No-Break Space in numbers over 999 without separator
    # numbers between 1500 and 1914 in this material
    # are most likely years and shouldn't contain any space,
    # so leave them out of the replacement
    search_string = re.compile(r"(\d{1,3})(\d{3,})(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\2&#x202F;\3", xml_string)
    search_string = re.compile(r"(\d{2,3})(\d{3,})")
    xml_string = search_string.sub(r"\1&#x202F;\2", xml_string)
    search_string = re.compile(r"\d{4,}")
    result = re.findall(search_string, xml_string)
    for match in result:
        if int(match) < 1500 or int(match) > 1914:
            match_replacement = match[:1] + "&#x202F;" + match[1:]
            xml_string = xml_string.replace(match, match_replacement, 1)
    # the asterisk stands for a footnote
    search_string = re.compile(r" *\*\) *")
    xml_string = search_string.sub("<note id=\"\" n=\"*)\"></note>", xml_string)
    # replace certain characters
    search_string = re.compile(r"&quot;")
    xml_string = search_string.sub("”", xml_string)
    search_string = re.compile(r"&apos;")
    xml_string = search_string.sub("’", xml_string)
    search_string = re.compile(r"º")
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
    # (MULTILINE matches at the beginning of the string
    # and at the beginning of each line)
    search_string = re.compile(r"^ +<", re.MULTILINE)
    xml_string = search_string.sub("<", xml_string)
    if DOCUMENT_TYPE == "article":
    # there shouldn't be line breaks like these in articles
        search_string = re.compile(r"-<lb/>\n")
        xml_string = search_string.sub("", xml_string)
        search_string = re.compile(r"<lb/>\n")
        xml_string = search_string.sub(" ", xml_string)
    # when there are several deleted lines of text,
    # exports from Transkribus contain one <del> per line,
    # but it's ok to have a <del> spanning several lines
    # so let's replace those chopped up <del>:s
    # the same goes for <add>
    search_string = re.compile(r"</del><lb/>\n<del>")
    xml_string = search_string.sub("<lb/>\n", xml_string)
    search_string = re.compile(r"</add><lb/>\n<add>")
    xml_string = search_string.sub("<lb/>\n", xml_string)
    if CORRECT_P is True:
        # Transkribus changed its text regions algorithm
        # and now "recognizes" <p>:s everywhere
        # this is of no help to us, so we're better off 
        # without these wrongly recognized <p>:s altogether
        # we need the line breaks inserted though, so unwrap
        # doesn't work, just ordinary replacement
        search_string = re.compile(r"</p>\n<p>")
        xml_string = search_string.sub("<lb/>\n", xml_string)
        search_string = re.compile(r"(</p>\n)(<pb .+?/>)(\n<p>)")
        xml_string = search_string.sub(r"<lb/>\n\2\n", xml_string)
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
    # do not allow soft hyphen (&shy;), use only hyphen minus
    # (or the not sign for hyphens that are to be transformed 
    # differently later on for html and download xml on the site)
    # first check for hyphen minus combined with soft 
    # (and often invisible, depending on your text/code editor) hyphen,
    # as these cases have appeared in the material
    xml_string = xml_string.replace("-­", "-")
    xml_string = xml_string.replace("­-", "-")
    xml_string = xml_string.replace("­", "-")
    if CHECK_UNTAGGED_ABBREVIATIONS is True:
        xml_string = replace_untagged_abbreviations(xml_string, abbr_dictionary)
    print("XML tidied.")
    return xml_string

# if abbreviations haven't been encoded but we still want to
# add likely expansions to them: use this option
def replace_untagged_abbreviations(xml_string, abbr_dictionary):
    # certain words should only be given expans if they have
    # been encoded as abbrs, otherwise they probably aren't
    # abbrs but just ordinary words that can't be expanded
    # keep these words in this list
    do_not_expand = ["afsigt", "allmän", "art", "des", "f.", "fr", "följ", "Följ", "för", "för.", "först", "först.", "G.", "gen", "H.", "hand.", "just", "L", "L.", "m", "M", "min", "min.", "mån", "ord", "ord.", "R", "R.", "regn", "regn.", "rest", "rest.", "s", "s.", "S", "t.", "tills", "upp", "upp.", "v.", "väg."]
    # these are all the recorded abbrs that we hav en expan for
    abbr_list = abbr_dictionary.keys()
    for abbreviation in abbr_list:
        if abbreviation in do_not_expand:
            continue
        # prevent abbrs containing a dot from being treated as regex
        # otherwise e.g. abbr "Fr." matches "Fri" in the text
        abbreviation_in_text = re.sub(r"\.", "\.", abbreviation)
        # by adding some sontext to the abbr we can specify 
        # what a word should look like and make sure that parts
        # of words or already tagged words don't get tagged 
        search_string = re.compile(r"(\s|^|»|”|\()" + abbreviation_in_text + r"(\s|\.|,|\?|!|»|”|:|;|\)|<lb/>|</p>)", re.MULTILINE)
        result = search_string.search(xml_string)
        if result is not None:
            # get the expan for this abbr and substitute this
            # part of the text
            expansion = abbr_dictionary[abbreviation]
            xml_string = search_string.sub(r"\1" + "<choice><abbr>" + abbreviation + "</abbr><expan>" + expansion + "</expan></choice>" r"\2", xml_string)
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
        abbr_dictionary = read_dict_from_file("dictionaries/abbr_dictionary.json")
        new_soup, false_l = transform_xml(old_soup, abbr_dictionary)
        tidy_xml_string = tidy_up_xml(str(new_soup), false_l, abbr_dictionary)
        write_to_file(tidy_xml_string, file)
        print(file + " created.")

main()