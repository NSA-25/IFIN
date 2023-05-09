import requests
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from io import BytesIO
import pymarc

query = "Advances in space plasma physics"
start_record = "1"
maximum_records = "1000"

url = f"http://lx2.loc.gov:210/lcdb?version=2&operation=searchRetrieve&query={query}&startRecord={start_record}&maximumRecords={maximum_records}&recordSchema=marcxml"
response = requests.get(url)

root = ET.fromstring(response.content)

records = []
for record in root.iter("{http://www.loc.gov/MARC21/slim}record"):
    records.append(ET.tostring(record))

title_scores = []
for record in records:
    #bytesIo - file-like object needed for parse_xml_to_array
    marc_record = pymarc.parse_xml_to_array(BytesIO(record))[0]
    title = marc_record.title()
    #compare the searched title to the book title
    score = SequenceMatcher(None, query.lower(), title.lower()).ratio()
    title_scores.append((title, score))

title_scores.sort(key=lambda x: x[1], reverse=True)

for title, score in title_scores:
    print(f"Title: {title} - Score: {score}")

most_similar_record = pymarc.parse_xml_to_array(BytesIO(records[0]))[0]
title = most_similar_record.title()
author = most_similar_record.author()
publication_date = most_similar_record.pubyear()

print(f"\nMost similar record:")
print(f"Title: {title}")
print(f"Author: {author}")
print(f"Publication date: {publication_date}")
