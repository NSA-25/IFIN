import json
import bs4
import requests
import time
import os
import pymarc

iterations_max = 40
link_catalog = "http://library.nipne.ro/alipac/MBDUPWIVPCCZPHGBTOQY-00025/find-simple?C1=%28&V1=*&C2=%29&F1=WRD&A1=N&x=0&y=0"
# link_catalog2 = "http://library.nipne.ro/alipac/HJIRTZMKXAOWNVPIAMWT-00031/find-simple?C1=%28&V1=*&C2=%29&F1=WRD&A1=N&x=0&y=0"
link_optiuni = "http://library.nipne.ro/alipac/VZIHMJUYVZXTEZGOJXEK-00013/option-display"

link_id = "PAPGCGZNWGMJYNQWRTUB-00026"
link_iterator = 1
link_raw_record = f"http://library.nipne.ro/alipac/{link_id}/full-set?NUM={link_iterator}&FRM=002"

directory = 'records_10000'

iterator_start = 56782 # From which record should the web scrapping begin?
iterator_end = 200 # How many records to process

# driver = webdriver.Firefox("C:\WebDriver")

#all possible attributes found in records
all_attributes = {}

#title, author, year
compressed_data = []

#all attributes, all records
full_data = []

records_number_desired = 1

records_number_read = 0

sleep_time = 3 #sleep time before the next action is taken, used on extracting records

def parse_html_from_link(link):
    return bs4.BeautifulSoup(requests.get(link).content, "html.parser")

# def modify_options():

"""    
Read a single simple record from a table row in a HTML file on IFIN catalog site.

Args:
    tr: A BeautifulSoup table row object containing data for a book record.
Returns:
    None
Prints:
    The author, title, year, counts, and locations of a book record.
"""
def read_record(tr):
    author = tr.findAll("td")[3].text
    title = tr.findAll("td")[4].find("a").text
    year = tr.findAll("td")[5].text
    counts = tr.findAll("td")[6].text
    locations = tr.findAll("td")[7].text
    print(author, title, year, counts, locations)

"""
Parses the trs into a dictionary representing a MARC record.
The dictionary contains fields, subfields and their respective values.
This functions is used by read_write_records(): to extract raw records from the IFIN catalog.
It also writes the records in the 'records' directory with the structure record_record number on website

Parameters:
    trs (list): A list of Beautiful Soup elements representing a table row.

Returns:
    None
"""
def read_raw_record(trs):
    record = {}
    previous_field = None
    for tr in trs:
        field, subfield, value = tr.findAll("td")
        field, subfield, value = field.text.strip(), subfield.text.strip(), value.text.strip()
        if field == "":
            record[previous_field][subfield] = value
        else:
            previous_field = field
            if subfield == "":
                record[field] = value
            else:
                record[field] = {}
                record[field][subfield] = value
    with open(f"records/record{link_iterator}.json", "w") as f:
        f.write(json.dumps(record))
        # print(f"field:{field.strip()} subfield:{field.strip()} value:{value.strip()}\n")

"""
A way to view the raw record html
tbody 2 -> mai multe tr-uri
tr 0 -  td 0 - content text (cheie)
        td 1 - context text (subcheie)
        td 2 - context text (valoare)

---date irelevante---

tr 1 - td 0 - content text (cheie)
...
campuri speciale: a ******,
"""

"""
Read and write MARC records from the raw record sections on IFIN catalog.
link_id needs to be regenerated if the function is called again after stopping
for a long time. To be copied from the link.

Args:
    None

Returns:
    None
"""
def read_write_records():
    records_number_read = 0
    link_iterator = iterator_start
    for _ in range(iterator_end):
        link_raw_record = f"http://library.nipne.ro/alipac/{link_id}/full-set?NUM={link_iterator}&FRM=002"
        html = parse_html_from_link(link_raw_record)
        trs = html.findAll("tbody")[2].findAll("tr")
        read_raw_record(trs)
        print(f"Current record: {link_iterator}\trecords read: {records_number_read}")
        records_number_read += 1
        link_iterator += 1
        time.sleep(sleep_time)

"""
Reads a JSON file containing a raw record and returns a dictionary of fields present in the file.

Args:
- file (str): The file path of the JSON file to be read.

Returns:
- A dictionary where each key represents a field in the record and each value is a set of the subfields
present in that field. If a field has no subfields, its value is an empty set.
"""

def find_fields_file(file):
    with open(file, "r") as f:
        json_data = json.load(f)
    fields = {}
    for key in json_data:
        if isinstance(json_data[key], dict):
            subkeys = {subkey for subkey in json_data[key]}
            fields[key] = subkeys
        else:
            fields[key] = set()
    f.close()
    return fields

"""
Given a folder containing JSON files, this function finds and returns a set
of all the fields (tags and subfields) that are present in the files.

Args:
    folder (str): The name of the folder containing the JSON files.

Returns:
    A dictionary where each key is a tag (e.g. "245"), and the value is a set
    of all the subfields (e.g. "a", "b", "c", etc.) that are present in the
    files.
"""

def find_fields(folder):
    all_fields = {}
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        fields = find_fields_file(file_path)
        for key in fields:
            if key in all_fields:
                all_fields[key] = all_fields[key].union(fields[key])
            else:
                all_fields[key] = fields[key]
    return all_fields

#making a better JSON, removing L subfields (not in MARC21), removing some special characters in values(".", "\")
"""
Reads in each JSON file in the specified folder, rewrites it in a more MARC style.
The input folder should contain files generated by read_write_record.

Parameters:
    folder (str): the name of the folder containing the JSON files to be corrected.
    output_folder (str): the name of the folder where the corrected JSON files will be saved.
    changelog_ (str, optional): the name of the changelog file. Defaults to None.
Returns:
    None
"""
def correct_records(folder, output_folder, changelog_ = None):
    invalid_chars = ['.', '\\', '/']

    # create a changelog file if one was not provided
    changelog = None
    if not changelog_:
        changelog = f"{folder}_changelog"
    c = open(changelog, "w", encoding="utf-8") #encoding avoids a few bugs

    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    for filename in file_list:
        c.write(f"{filename}_changes: ")
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r") as f:
            json_data = json.load(f)
        f.close()
        output = {
            "leader": json_data["LDR"],
            "fields": []
        }
        for field, value in json_data.items():
            indicators = []
            if len(field) == 3:
                indicators = [" ", " "]
            elif len(field) == 4:
                indicators = [field[3], " "]
                c.write(f"{field}->{field[:-1]} ")
                field = field[:-1]
            elif len(field) == 5:
                indicators = [field[3], field[4]]
                c.write(f"{field}->{field[:-2]} ")
                field = field[:-2]
            field_dict = {
                field: {
                    "subfields": [],
                    "indicators": [],
                    "tag": field
                }
            }
            field_dict[field]["indicators"] = indicators
            if isinstance(value, dict):
                for subfield, subvalue in value.items():
                    if subfield != "L":
                        if subvalue[-1:] in invalid_chars:
                            last_char = subvalue[-1:]
                            subvalue = subvalue[:-1]
                            c.write(f" {subvalue}: illegal character '{last_char}'")
                        field_dict[field]["subfields"].append({"code": subfield, "value": subvalue})
                    else:
                        field_dict[field]["value"] = None
                        c.write(f"Removed L:{subvalue} ")
            else:
                field_dict[field]["value"] = value
            output["fields"].append(field_dict)
        c.write("\n")
        g = open(f"{output_folder}/{filename}", "w")
        g.write(json.dumps(output))
        g.close()
    c.close()

"""
Returns the number of occurrences of each field and subfield in all files in the folder.
To be used on the extracted version of the JSONs (not the ones generated by the correcting function)

Args:
    folder (str): The name of the folder containing the JSON files.

Returns:
    tuple: A tuple containing two dictionaries:
        The first dictionary contains the number of occurrences of each field.
        The second dictionary contains, for each field, a dictionary with the number of occurrences of each subfield.
"""
def find_fields_occurences(folder):
    occurences_keys = {}
    occurences_subkeys = {}
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        fields = find_fields_file(file_path)
        for key in fields:
            if key in occurences_keys:
                occurences_keys[key] += 1
                for subkey in fields[key]:
                    if subkey in occurences_subkeys[key]:
                        occurences_subkeys[key][subkey] += 1
                    else:
                        occurences_subkeys[key][subkey] = 1
            else:
                occurences_keys[key] = 1
                occurences_subkeys[key] = dict()
                for subkey in fields[key]:
                    occurences_subkeys[key][subkey] = 1
    return occurences_keys, occurences_subkeys


"""
Find the count and locations of a field in the JSON files in a given folder.
To be used on the extracted version of the JSONs (not the ones generated by the correcting function)

Args:
    folder (str): The name of the folder containing the JSON files.
    field (str): The field to search for.

Returns:
    A tuple containing:
        locations (list): A sorted list of the locations where the field appears.
        count (int): The total count of the field in the JSON files.
"""
def find_field_count_locations(folder, field):
    locations = []
    count = 0
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r") as f:
            json_data = json.load(f)
        for key in json_data:
            if key == field:
                count += 1
                locations.append(int(filename[6:-5]))
        f.close()
    return sorted(locations), count

"""
Count the number of files for each language in which the data is written.

Parameters:
    folder (str): The name of the folder where the JSON files are located.

Returns:
    dict: A dictionary with the language names as keys and the counts as values.
"""
def group_by_lang(folder):
    languages = {}
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r") as f:
            json_data = json.load(f)
            if json_data['LNG'] in languages:
                languages[json_data['LNG']] += 1
            else:
                languages[json_data['LNG']] = 1
        f.close()
    return languages

"""
Creates folders for each language present in the given folder.

Args:
    folder (str): name of the folder containing the files to be sorted by language.

Returns:
    None
"""

def create_lang_folders(folder):
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    iter = 1
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r") as f:
            json_data = json.load(f)
            if not os.path.exists(f"records_languages/records_{json_data['LNG']}"):
                os.makedirs(f"records_languages/records_{json_data['LNG']}")
            with open(f"records_languages/records_{json_data['LNG']}/record{iter}.json", "w") as f:
                f.write(json.dumps(json_data))
        iter += 1
        f.close()

#basic MARC reader
def read_marc(file):
    with open(file, 'rb') as f:
        reader = pymarc.MARCReader(f)
        for record in reader:
            print(record)

"""
This function converts a MARC JSON record to a MARC binary record.
Arguments must be filename.json, filename.mrc; valid for the corrected versions (records_all_corrected)

Parameters:
    file_in: string representing the name of the input file (must be in JSON format).
    file_out: optional string representing the name of the output file (will be in MARC binary format). If not provided, a default name will be generated.

Returns:
    None
"""
def json_to_marc(file_in, file_out = None):
    with open(file_in, 'r') as f:
        json_data = json.load(f)
    record = pymarc.Record(force_utf8=True) #Some record have weird characters (eg record 10228 - u00f3)
    record.leader = json_data['leader']
    for field_data in json_data['fields']:
        field_tag = list(field_data.keys())[0]
        if field_tag in ['IDN', 'FMT', 'LDR', 'LNG']:
            continue
        field = pymarc.Field (
            tag=field_tag,
            indicators=field_data[field_tag]['indicators'],
            subfields=[]
        )
        if field_data[field_tag]['subfields'] == []:
            field.data = field_data[field_tag]['value']
        else:
            for subfield in field_data[field_tag]['subfields']:
                field.add_subfield(subfield['code'], subfield['value'])
        record.add_field(field)
    if file_out:
        with open(file_out, 'wb') as f:
            writer = pymarc.MARCWriter(f)
            writer.write(record)
            writer.close()
    else:
        with open(f"{file_in[:len(file_in)-5]}_out.mrc", 'wb') as f:
            writer = pymarc.MARCWriter(f)
            writer.write(record)
            writer.close()

#basic converter from .mrc to .xml
def mrc_to_marcxml(file, file_out):
    with open(file, 'rb') as f:
        reader = pymarc.MARCReader(f)
        writer = pymarc.XMLWriter(open(file_out, 'wb'))
        for record in reader:
            writer.write(record)
        writer.close()

#merges all the json files in a folder
def merge_json(folder, output_file):
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    file_list = os.listdir(folder_path)
    merged_data = []
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        with open(file_path) as f:
            data = json.load(f)
            merged_data.append(data)
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(merged_data, f)
    else:
        with open(f"merged_{folder}", 'w') as f:
            json.dump(merged_data, f)

if __name__ == '__main__':
    # folder_path = os.path.join(os.path.dirname(__file__), "records_marc")
    # file_list = os.listdir(folder_path)
    # for filename in file_list:
    #     mrc_to_marcxml(f"records_marc/{filename}", f"records_marcxml/{filename[:-4]}.xml")

    # merge_json("records_all_corrected", "all_records.json")
    #     print(filename)
        # json_to_marc(f"records_all_corrected/{filename}", f"records_marc/{filename[:-5]}.mrc")

    # correct_records("records_all", "records_all_corrected")

    # cnt = 0
    # for path in os.scandir("records_languages/records_rum"):
    #     cnt += 1
    # print(cnt)

    # create_lang_folders("records_all")

    print(find_field_count_locations("records_all", "041"))

    # keys_occ, subkeys_occ = find_fields_occurences('records_all')
    # sorted_dict = {k: v for k, v in sorted(keys_occ.items(), key=lambda item: item[1])}
    # sorted_dict_sub = dict()
    # for key in sorted_dict.keys():
    #     sorted_dict_sub[key] = {k: v for k, v in sorted(subkeys_occ[key].items(), key=lambda item: item[1])}
    # print(test_it)
    # print(sorted_dict)
    # with open("sorted_keys.json", "w") as f:
    #     f.write(json.dumps(sorted_dict))
    # with open("sorted_subkeys.json", "w") as f:
    #     f.write(json.dumps(sorted_dict_sub))
    # print(sorted_dict_sub)

    # print(open_library_get())
    # write_marc_one("converted_record.json")

    # fields = find_fields('records_10000')
    # fields2 = find_fields('records_20000')
    # fields3 = find_fields('records_30000')
    # fields4 = find_fields('records_40000')
    # fields5 = find_fields('records_50000')
    # fields6 = find_fields('records_60000')
    # for key in fields2:
    #     if key in fields:
    #         fields[key] = fields[key].union(fields2[key])
    #     else:
    #         fields[key] = fields2[key]
    # for key in fields3:
    #     if key in fields:
    #         fields[key] = fields[key].union(fields3[key])
    #     else:
    #         fields[key] = fields3[key]
    # for key in fields4:
    #     if key in fields:
    #         fields[key] = fields[key].union(fields4[key])
    #     else:
    #         fields[key] = fields4[key]
    # for key in fields5:
    #     if key in fields:
    #         fields[key] = fields[key].union(fields5[key])
    #     else:
    #         fields[key] = fields5[key]
    # for key in fields6:
    #     if key in fields:
    #         fields[key] = fields[key].union(fields6[key])
    #     else:
    #         fields[key] = fields6[key]
    # for key in fields:
    #     fields[key] = [subkey for subkey in fields[key]]
    # with open("fields.json", "w") as f:
    #     f.write(json.dumps(fields))
    # print(fields)

