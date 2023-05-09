from pymarc import MARCReader
with open('converted_record_out.mrc', 'rb') as fh:
    reader = MARCReader(fh)
    for record in reader:
        print(record)