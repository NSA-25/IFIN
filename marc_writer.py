import json
from pymarc import MARCWriter, Record, Field

with open('converted_record.json', 'r') as f:
    json_data = json.load(f)

record = Record()

record.leader = json_data['leader']

for field in json_data['fields']:
    for tag, subfields in field.items():
        if isinstance(subfields, str):
            record.add_field(Field(tag=tag, indicators=[" ", " "], data=subfields))
        else:
            subfields_list = []
            for code, value in subfields.items():
                subfields_list.append(code)
                subfields_list.append(value)
            record.add_field(Field(tag=tag, indicators=[" ", " "], subfields=subfields_list))

with open('output2.mrc', 'wb') as f:
    writer = MARCWriter(f)
    writer.write(record)
    writer.close()