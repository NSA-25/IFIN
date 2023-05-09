import pymarc

with open('output2.mrc', 'rb') as f:
    reader = pymarc.MARCReader(f)
    writer = pymarc.XMLWriter(open('file.xml','wb'))
    for record in reader:
        writer.write(record)
    writer.close()