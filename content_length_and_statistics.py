# This script is used for gathering statistics about
# all of the texts in this large edition.
#
# Each language version of a text has a pre-made file
# in the GitHub repository, containing a template.
# Editors can add content to any file.
# The script measures the content length of each file
# in the repo by counting the characters in the human-readable
# text (the content of the tags) using Beautiful Soup.
#
# The script combines the content length with data from
# the database and outputs ordered CSV:s containing info
# about each text.
#
# By organizing the data as pivot tables in Excel I get
# nice statistics over how many texts there are in each
# language, how long each text is, how many pages of text
# there are within each category (i.e. letters, articles),
# and which texts are still missing from the repo (content
# length 0). This would otherwise be hard to know, because
# there are thousands of texts and files and the texts mainly
# exist only as XML. Editors can now easily check which texts
# haven't yet been transcribed or translated and how long
# a certain text would be were it to be printed, without
# keeping lists themselves or updating a list each time they've
# finished a text.
#
# Sample output last in file.

from pathlib import Path
import psycopg2
import re
from bs4 import BeautifulSoup

conn_db = psycopg2.connect(
    host="",
    database="",
    user="",
    port="",
    password=""
)
cursor = conn_db.cursor()

COLLECTION_ID = 1
SOURCE_FOLDER = "C:/../GitHub/leomechelin_files/documents/Delutgava_1"

# create path object for folder from given filepath string
# save all paths to files found in this folder or subfolders in a list
def create_file_list(SOURCE_FOLDER):
    path = Path(SOURCE_FOLDER)
    file_list = []
    iterate_through_folders(path, file_list)
    return file_list

# iterate through folders recursively and append filepaths to list
def iterate_through_folders(path, file_list):
    for content in path.iterdir():
        if content.is_dir():
            iterate_through_folders(content, file_list)
        elif content.suffix == ".xml":
            file_list.append(content)

# publication_id and language are present in the file name
# folders are in the file path 
def extract_info_from_filename(file):
    file_name = file.stem
    main_folder = file.parts[8]
    if main_folder == "Brev" or main_folder == "Artiklar" or main_folder == "Lantdagen" or main_folder == "Verk" or main_folder == "Forelasningar":
        subfolder = file.parts[9]
    else:
        subfolder = None
    if main_folder == "Brev":
        correspondent_folder = file.parts[10]
    else:
        correspondent_folder = None
    # create file path string and shorten it
    file_path = file.as_posix().replace("C:/../GitHub/leomechelin_files/", "")
    file_data = (main_folder, subfolder, correspondent_folder, file_path)
    search_string = re.compile(r"(\w{2})_(\d+)$")
    match = re.search(search_string, file_name)
    language = match.group(1)
    publication_id = match.group(2)
    return file_data, publication_id, language

# get the relevant info for the publication
def fetch_db_data(publication_id, language):
    # these publications don't have separate manuscript files
    print(str(publication_id) + " " + language)
    if language == "sv" or language == "fi":
        fetch_query = """SELECT publication_group_id, text, original_publication_date FROM publication, translation_text WHERE publication.id = %s AND translation_text.language = %s AND publication.translation_id = translation_text.translation_id AND field_name = %s"""
        field_name = "name"
        values_to_insert = (publication_id, language, field_name)
    # these publications always have a manuscript file
    else:
        fetch_query = """SELECT publication_group_id, publication_manuscript.name, publication.original_publication_date FROM publication, publication_manuscript WHERE publication.id = %s AND publication_manuscript.original_language LIKE %s AND publication.id = publication_id"""
        # language value for these publications may contain several
        # languages
        language = "%" + language + "%"
        values_to_insert = (publication_id, language)
    cursor.execute(fetch_query, values_to_insert)
    db_data = cursor.fetchone()
    return db_data

# read an xml file and return its content as a soup object
def read_xml(file):
    with file.open("r", encoding="utf-8-sig") as source_file:
        file_content = source_file.read()
        xml_soup = BeautifulSoup(file_content, "xml")
    return xml_soup

# check whether there is any content in the file, apart from
# the template
# strip newlines (otherwise they'll get counted as characters)
# and use space to join the text contents of all the elements
# this probably is the most accurate way to measure the length
# without further processing the string
# the content length isn't going to be 100% right, but good enough
# also calculate the estimated page value if the text were to
# be published as a printed book
def check_content(xml_soup):
    main_div = xml_soup.body.div
    if len(main_div.get_text(strip = True)) == 0:
        content_length = 0
        pages = 0
    else:
        content_length = len(main_div.get_text(" ", strip = True))
        # we will assume there are 2 500 characters including spaces
        # on a printed page
        pages = round(content_length / 2500, 1)
    return content_length, pages

# construct the url for each publication
def construct_url(publication_id, COLLECTION_ID):
    url = "https://digital_publishing_project/publication/" + str(COLLECTION_ID) + "/text/" + str(publication_id) + "/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts"
    return url

# make a list out of the values for each publication
# add that list to the main list holding all publications' values
def construct_list(file_data, publication_id, language, db_data, content_length, pages, url, stats_list):
    publication_info = []
    (main_folder, subfolder, correspondent_folder, file_path) = file_data
    (group_id, title, date) = db_data
    if group_id is None:
        group_id = 100
    publication_info.append(publication_id)
    publication_info.append(group_id)
    publication_info.append(language)
    publication_info.append(date)
    publication_info.append(title)
    publication_info.append(content_length)
    publication_info.append(pages)
    publication_info.append(main_folder)
    publication_info.append(subfolder)
    publication_info.append(correspondent_folder)
    publication_info.append(url)
    publication_info.append(file_path)
    stats_list.append(publication_info)
    return stats_list

def sort_stats_list(stats_list):
    # sort the list by these criteria:
    # main folder, subfolder, correspondent folder, date, group, id, language
    stats_list_1 = stats_list.copy()
    stats_list_1.sort(key = lambda row: (row[7], row[8], row[9], row[3], row[1], row[0], row[2]))
    # sort the list by these criteria:
    # language, pages, date
    # the minus flips the order of the pages value, which is a float
    # from ascending to descending
    stats_list_2 = stats_list.copy()
    stats_list_2.sort(key = lambda row: (row[2], -row[6], row[3]))
    return stats_list_1, stats_list_2

# create a csv file 
def write_list_to_csv(list, filename):
    with open(filename, "w", encoding="utf-8-sig") as output_file:
        for row in list:
            for item in row:
                if item is None:
                    item = ""
                output_file.write(str(item) + ";")
            output_file.write("\n")
    print("List written to file", filename)

def main():
    file_list = create_file_list(SOURCE_FOLDER)
    stats_list = []
    for file in file_list:
        file_data, publication_id, language = extract_info_from_filename(file)
        db_data = fetch_db_data(publication_id, language)
        xml_soup = read_xml(file)
        content_length, pages = check_content(xml_soup)
        url = construct_url(publication_id, COLLECTION_ID)
        stats_list = construct_list(file_data, publication_id, language, db_data, content_length, pages, url, stats_list)
    stats_list_1, stats_list_2 = sort_stats_list(stats_list)
    write_list_to_csv(stats_list_1, "documents/statistik/stats_list_1.csv")
    write_list_to_csv(stats_list_2, "documents/statistik/stats_list_2.csv")

main()


'''
Sample output. See function construct_list for a legend for the values.
589;2;fi;1861-12-20;20.12.1861 Kronikka.;4714;1.9;Artiklar;Barometern;;https://digital_publishing_project/publication/1/text/589/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Artiklar/Barometern/1861_12_20_Kronika/1861_12_20_Kronika_fi_589.xml;
589;2;sv;1861-12-20;20.12.1861 Krönika.;4360;1.7;Artiklar;Barometern;;https://digital_publishing_project/publication/1/text/589/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Artiklar/Barometern/1861_12_20_Kronika/1861_12_20_Kronika_sv_589.xml;
509;2;de;1861-03-25;25.3.1861 Lilly Steven-Steinheil–LM;7933;3.2;Brev;Mottaget;Steven_Steinheil_Lilly;https://digital_publishing_project/publication/1/text/509/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Brev/Mottaget/Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly_de_509.xml;
509;2;fi;1861-03-25;25.3.1861 Lilly Steven-Steinheil–LM;0;0;Brev;Mottaget;Steven_Steinheil_Lilly;https://digital_publishing_project/publication/1/text/509/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Brev/Mottaget/Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly_fi_509.xml;
509;2;sv;1861-03-25;25.3.1861 Lilly Steven-Steinheil–LM;7221;2.9;Brev;Mottaget;Steven_Steinheil_Lilly;https://digital_publishing_project/publication/1/text/509/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Brev/Mottaget/Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly/1861_03_25_Steven_Steinheil_Lilly_sv_509.xml;
1191;1;sv;1856-11-24;24.11.1856 D. 24 Nov. Ändtligen är jag då 17 år!;2172;0.9;Biographica;;;https://digital_publishing_project/publication/1/text/1191/nochapter/not/infinite/nosong/searchtitle/established_sv&established_fi&facsimiles&manuscripts;documents/Delutgava_1/Biographica/1856_11_24_D_24_Nov_Andtligen_ar_jag_da_17_ar/1856_11_24_D_24_Nov_Andtligen_ar_jag_da_17_ar_sv_1191.xml;
'''
