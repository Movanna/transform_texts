# This script goes through a list of encoded abbreviations 
# and their expansions and makes a dictionary out of them.
# This dictionary is later used by another script which 
# adds expansions to unexpanded abbreviations in a text.

# The starting point is a match list of all already
# existing expanded abbreviations in a large material.
# They have been encoded as <choice><abbr>Dr</abbr><expan>Doctor</expan></choice>.
# I exported this list from "Find in Files" in the 
# Oxygen XML Editor, but I couldn't use the list as such
# with BeautifulSoup since it contained XML that was not
# well-formed (matches contained context that didn't take XML
# into consideration, so tags/attributes/values were chopped off 
# right in the middle, or opening/closing tags were missing). 
# So this script first makes a new XML file containing only
# matches and well-formed XML.

# With BeautifulSoup we can then get the contents of <abbr> and <expan>
# and create the dictionary.

# This script can also easily be modified into e.g. making a
# dictionary of editors' corrections (in TEI XML encoded as
# <choice><orig>Docton</orig><corr>Doctor</corr></choice> or
# <choice><orig>e. g.</orig><reg>e.g.</reg></choice>).

import re
from bs4 import BeautifulSoup
import json

SOURCE_FILE = "documents/abbr/match_list.xml"
OUTPUT_FILE = "documents/expan/abbr_and_expan.xml"

# read an xml file and return its content
# either as a string or as as a soup object
# depending on what it's going to be used for
def read_xml(filename):
    with open (filename, "r", encoding="utf-8-sig") as source_file:
        file_content = source_file.read()
        if filename == OUTPUT_FILE:
            abbr_soup = BeautifulSoup(file_content, "xml")
            print("We have soup.")
            return abbr_soup
        else:
            return file_content

# find all <choice> containing both <abbr> and <expan>
# in the match list which also contains lots of other stuff
def find_abbr_and_expan(file_content):
    search_string = re.compile(r"<choice><abbr>.*?</abbr><expan>.*?</expan></choice>|<choice><expan>.*?</expan><abbr>.*?</abbr></choice>")
    match_string = re.findall(search_string, file_content)
    # the result is a list of strings
    # join them with a newline as separator for each match
    abbr_string = "\n"
    return abbr_string.join(match_string)

# create a new xml file containing only
# all the relevant <choice> elements
# this is the file we'll use when making the dictionary
def write_to_file(abbr_string, filename):
    with open(filename, "w", encoding="utf-8-sig") as output_file:
        output_file.write("<body>")
        output_file.write(abbr_string)
        output_file.write("</body>")
        output_file.close()
        print("Abbreviations and expansions written to file", filename)

# create the dictionary of abbreviations and their expansions
def create_abbr_dictionary(abbr_soup, abbr_dict):
    # go through each <choice> and its children <abbr> and <expan>
    choices = abbr_soup.find_all("choice")
    # just checking that every <choice> in the xml file
    # is actually used for the dictionary, hence the counter
    i = 0
    for choice in choices:
        for child in choice.children:
            # we can't just use .get_text() for getting the abbr contents,
            # because we need to preserve all the tags inside abbr,
            # such as <hi> (get_text only returns string content)
            # also, we can't use BS methods such as .unwrap() since the
            # variable abbr is no longer part of the parse tree
            # but ordinary replacement will do just as well
            # (just have to convert it from a BS tag object into a string first)
            # and we end up with the contents of <abbr>, both tags and strings
            if child.name == "abbr":
                abbr = child
                abbr_content = str(abbr)
                abbr_content = abbr_content.replace("<abbr>", "")
                abbr_content = abbr_content.replace("</abbr>", "")
            # the contents of <expan> contain no tags
            # so just get the string
            if child.name == "expan":
                expan_content = child.get_text()
                expan_content = str(expan_content)
        # now we have an abbreviation - expansion pair
        i += 1
        # if this abbreviation already exists in the dictionary:
        # check if the expansion we just found also exists
        # if it does, there's nothing to add
        # else: keep checking the expan, and if our expan
        # is a new one, add it to the dict
        # the same abbr may have several expans, e.g.
        # B.C. = Before Christ or British Columbia
        # since abbr is the key, we have to add _1 etc. to it
        # in order to be able to record new expans for it
        # I'll go through these multiple expans later
        # and decide which expan I want the other script to use
        if abbr_content in abbr_dict.keys():
            expan = abbr_dict.get(abbr_content)
            if expan == expan_content:
                continue
            else:
                x = 1
                while x < 5:
                    abbr_content = abbr_content + "_" + str(x)
                    if abbr_content in abbr_dict.keys():
                        expan = abbr_dict.get(abbr_content)
                        if expan == expan_content:
                            break
                        else:
                            x += 1
                            search_string = re.compile(r"_\d")
                            abbr_content = search_string.sub("", abbr_content)
                    else:
                        abbr_dict.update({abbr_content: expan_content})
                        break
        # if this abbreviation isn't in the dict: add it
        else:
            abbr_dict.update({abbr_content: expan_content})
    print(i)
    # sort dict by key (NB with this method uppercase and lowercase 
    # are sorted separately)
    sorted_abbr_dict = sorted(abbr_dict.items(), key = lambda item: item[0])
    sorted_abbr_dict = dict(sorted_abbr_dict)
    return sorted_abbr_dict

# save dictionary as a file
def write_dict_to_file(dictionary, filename):
    json_dict = json.dumps(dictionary, ensure_ascii=False)
    with open(filename, "w", encoding="utf-8") as output_file:
        output_file.write(json_dict)
        print("Dictionary written to file", filename)

def main():
    # read the match list
    file_content = read_xml(SOURCE_FILE)
    # find the abbreviations and their expansions
    abbr_string = find_abbr_and_expan(file_content)
    # save the abbr - expan pairs
    write_to_file(abbr_string, OUTPUT_FILE)
    # make the newly created file into a soup object
    abbr_soup = read_xml(OUTPUT_FILE)
    abbr_dict = {}
    # create and sort the dictionary
    sorted_abbr_dict = create_abbr_dictionary(abbr_soup, abbr_dict)
    write_dict_to_file(sorted_abbr_dict, "dictionaries/abbr_dictionary.json")

main()