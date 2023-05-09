import json
import pymarc

with open('xml_record.json', 'r') as f:
    json_data = json.load(f)

record = pymarc.Record()

for field in json_data['controlfield']:
    tag = field['@tag']
    value = field['#text']
    record.add_field(pymarc.Field(tag=tag, data=value))

for field in json_data['datafield']:
    tag = field['@tag']
    subfields = []
    for subfield in field['subfield']:
        code = subfield['@code']
        value = subfield['#text']
        subfields.append(code)
        subfields.append(value)
    if 'indicators' in field:
        indicators = field['indicators']
    else:
        indicators = [' ', ' ']
    record.add_field(pymarc.Field(tag=tag, indicators=indicators, subfields=subfields))

marcxml = pymarc.record_to_xml(record)

with open('record.xml', 'w') as f:
    f.write(marcxml)