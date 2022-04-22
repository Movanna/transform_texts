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

from pathlib import Path
import psycopg2
import re
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import NamedStyle, Font, Alignment, Border, Side, PatternFill
from openpyxl.formatting.rule import ColorScaleRule, Rule
from openpyxl.styles.differential import DifferentialStyle

conn_db = psycopg2.connect(
    host="",
    database="",
    user="",
    port="",
    password=""
)
cursor = conn_db.cursor()

COLLECTIONS = [1, 2, 3, 4]
SOURCE_FOLDER = "C:/../GitHub/leomechelin_files/documents/Delutgava_"
EXCEL_FOLDER = "documents/statistik/"

# create path object for folder from given filepath string
# save all paths to files found in this folder or subfolders in a list
def create_file_list(source_folder):
    path = Path(source_folder)
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
        fetch_query = """SELECT publication_group_id, text, original_publication_date, original_language FROM publication, translation_text WHERE publication.id = %s AND translation_text.language = %s AND publication.translation_id = translation_text.translation_id AND field_name = %s"""
        field_name = "name"
        values_to_insert = (publication_id, language, field_name)
    # these publications always have a manuscript file
    else:
        fetch_query = """SELECT publication_group_id, publication_manuscript.name, publication.original_publication_date, publication_manuscript.original_language FROM publication, publication_manuscript WHERE publication.id = %s AND publication_manuscript.original_language LIKE %s AND publication.id = publication_id"""
        # language value for these publications may contain several
        # languages, but files only have one registered language per file
        check_language = "%" + language + "%"
        values_to_insert = (publication_id, check_language)
    cursor.execute(fetch_query, values_to_insert)
    db_data = cursor.fetchone()
    (group_id, title, date, original_language) = db_data
    # if this file is the original language version of the files
    # for this publication, it can't be a translation
    # we need to separate these files from the ones that are meant
    # to be translated but just haven't been translated yet
    # later on, we'll replace this translator value with
    # a specific cell colour in our Excel report
    if original_language == language or language in original_language:
        translator = ("X", "X")
    else:
        # fetch the translator for this text, if there is one
        fetch_query = """SELECT last_name, first_name FROM contributor, contribution WHERE contributor.id = contribution.contributor_id AND contribution.publication_id = %s AND text_language = %s"""
        values_to_insert = (publication_id, language)
        cursor.execute(fetch_query, values_to_insert)
        translator = cursor.fetchone()
    if translator is not None:
        db_data = db_data + translator
    else:
        db_data = db_data + (None, None)
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
    (group_id, title, date, original_language, translator_last_name, translator_first_name) = db_data
    # add the translator's name, or if there isn't a translator
    # leave this slot empty
    if translator_last_name is not None:
        translator = translator_last_name + ", " + translator_first_name
    else:
        translator = ""
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
    publication_info.append(translator)
    publication_info.append(url)
    publication_info.append(file_path)
    stats_list.append(publication_info)
    return stats_list

def sort_stats_list(stats_list):
    # sort the list by these criteria:
    # main folder, subfolder, correspondent folder, date, group, id, language
    stats_list_1 = stats_list.copy()
    stats_list_1.sort(key = lambda row: (row[7], row[8], row[9], row[3], row[1], row[0], row[2]))
    return stats_list_1

# style the Excel sheets using openpyxl
# and replace some values with a certain style
def style_spreadsheet(spreadsheet_file_path):
    # open the newly created workbook
    workbook = openpyxl.load_workbook(filename = spreadsheet_file_path)
    # header style
    header = NamedStyle(name = "header")
    header.font = Font(bold = True, color = "081354")
    header.border = Border(bottom = Side(border_style = "thin"))
    header.alignment = Alignment(horizontal = "center", vertical = "center")
    # table style
    table_font = Font(color = "081354")
    table_border = Border(bottom = Side(border_style = "thin"))
    # loop through the sheets
    for name in workbook.sheetnames:
        sheet = workbook[name]
        # first row is the header, style it differently
        header_row = sheet[1]
        for cell in header_row:
            cell.style = header
        # loop through translator values and replace value
        # "X, X" (which means that this is the original language file)
        # with a pattern fill, so you can easily spot those rows
        # knowing they don't lack the translator since they're originals
        r = 2
        for row in sheet.iter_rows():
            cell = sheet.cell(row = r, column = 11)
            for cell in row:
                if cell.value == "X, X":
                    cell.value = ""
                    cell.fill = PatternFill(fill_type = "lightTrellis")
                    r += 1
        # set column width and styles for the different types of sheets
        if len(sheet.title) < 10:
            sheet.column_dimensions["D"].width = 3
            sheet.column_dimensions["D"].width = 3
            sheet.column_dimensions["D"].width = 3
            sheet.column_dimensions["D"].width = 11
            sheet.column_dimensions["E"].width = 50
            sheet.column_dimensions["F"].width = 13
            sheet.column_dimensions["G"].width = 13
            sheet.column_dimensions["H"].width = 13
            sheet.column_dimensions["I"].width = 18
            sheet.column_dimensions["J"].width = 23
            sheet.column_dimensions["K"].width = 19
            sheet.column_dimensions["L"].width = 20
            sheet.column_dimensions["M"].width = 20
            # add gradient colours depending on value of column
            # "printed pages", ranging from orange for files
            # with no content length, through yellow to green
            color_scale_rule = ColorScaleRule(start_type = "num", start_value = 0, start_color = "FF9933",  mid_type = "num", mid_value = 5, mid_color = "FFF033", end_type = "num", end_value = 300, end_color = "97FF33")
            sheet.conditional_formatting.add("G2:G3500", color_scale_rule)
        elif len(sheet.title) > 30:
            sheet.column_dimensions["A"].width = 30
            sheet.column_dimensions["B"].width = 20
            sheet.column_dimensions["C"].width = 20
            sheet.column_dimensions["D"].width = 20
        else:
            sheet.column_dimensions["A"].width = 20
            sheet.column_dimensions["B"].width = 20
            sheet.column_dimensions["C"].width = 20
            sheet.column_dimensions["D"].width = 20
            # style cells in column A as long as they're not blank 
            diff_style = DifferentialStyle(border = table_border, font = table_font)
            rule = Rule(type="expression", dxf = diff_style)
            rule.formula = ["NOT(ISBLANK(A2:A100))"]
            sheet.conditional_formatting.add("A2:A100", rule)
        # make header row of each sheet stick when scrolling
        sheet.freeze_panes = "N2"
    workbook.save(spreadsheet_file_path)
    print("Workbook updated with styles.")


def main():
    for collection_id in COLLECTIONS:
        source_folder = SOURCE_FOLDER + str(collection_id)
        file_list = create_file_list(source_folder)
        stats_list = []
        for file in file_list:
            file_data, publication_id, language = extract_info_from_filename(file)
            db_data = fetch_db_data(publication_id, language)
            xml_soup = read_xml(file)
            content_length, pages = check_content(xml_soup)
            url = construct_url(publication_id, collection_id)
            stats_list = construct_list(file_data, publication_id, language, db_data, content_length, pages, url, stats_list)
        stats_list_sorted = sort_stats_list(stats_list)
        # use Pandas to create spreadsheet data and pivot tables
        df = pd.DataFrame(stats_list_sorted, columns = ["id", "grupp", "språk", "datum", "titel", "teckenmängd", "tryckta sidor", "genre", "undermapp", "korrespondent", "översättare", "länk", "fil"])
        # table_1 has both subtotals and totals, which we have to get
        # by concatenating two slightly different pivot tables
        piv_1 = df.pivot_table(index = ["genre", "språk"], values= "tryckta sidor", aggfunc="sum", margins = True, margins_name = "summa")
        piv_2 = piv_1.query("genre != 'summa'").groupby(level = 0).sum().assign(språk = "totalt").set_index("språk", append = True)
        table_1 = pd.concat([piv_1, piv_2]).sort_index()
        table_2 = pd.pivot_table(df, values = "tryckta sidor", index = "språk", aggfunc = "sum", margins = True, margins_name = "summa")
        # table_3 is only for collections that contain letters
        # it's a pivot table of the total number of pages for the
        # different language versions of a correspondent's letters
        df_filtered = df.query("genre == 'Brev'")
        try:
            table_3 = pd.pivot_table(df_filtered, values = "tryckta sidor", index = ["korrespondent", "språk"], columns = "undermapp", aggfunc = "sum", margins = True, margins_name = "summa")
        except:
            table_3 = None
        # construct the sheet names
        # there are 3 or 4 sheets for each collection
        df_sheet_name = "utg. " + str(collection_id)
        table_1_sheet_name = "utg. " + str(collection_id) + ", sidor per genre"
        table_2_sheet_name = "utg. " + str(collection_id) + ", sidor per språk"
        table_3_sheet_name = "utg. " + str(collection_id) + ", sidor per korrespondent"
        # use current month for constructing the workbook title
        # since this is a monthly report
        file_date = datetime.datetime.now()
        file_date = file_date.strftime("%m") + "_" + file_date.strftime("%Y")
        spreadsheet_file_path = EXCEL_FOLDER + "Rapport_" + file_date + ".xlsx"
        # check if the Excel workbook has already been created
        # if it has, append to the existing one
        path = Path(spreadsheet_file_path)
        if path.is_file():
            with pd.ExcelWriter(spreadsheet_file_path, engine = "openpyxl", mode = "a") as writer:
                df.to_excel(writer, sheet_name = df_sheet_name, index = False)
                table_1.to_excel(writer, sheet_name = table_1_sheet_name)
                table_2.to_excel(writer, sheet_name = table_2_sheet_name)
                if table_3 is not None:
                    table_3.to_excel(writer, sheet_name = table_3_sheet_name)
        else:
            with pd.ExcelWriter(spreadsheet_file_path, engine = "openpyxl") as writer:
                df.to_excel(writer, sheet_name = df_sheet_name, index = False)
                table_1.to_excel(writer, sheet_name = table_1_sheet_name)
                table_2.to_excel(writer, sheet_name = table_2_sheet_name)
                if table_3 is not None:
                    table_3.to_excel(writer, sheet_name = table_3_sheet_name)
    print("Workbook " + str(spreadsheet_file_path) + " created.")
    style_spreadsheet(spreadsheet_file_path)

main()