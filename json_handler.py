import json
import os

def merge_jsons(folder):
    jsons = list()
    records_in_folder = os.listdir(folder)
    for file in records_in_folder:
        with open(f"{folder}/{file}", "r") as json_file:
            current_json = json.load(json_file)
            print(current_json)
            jsons.append(current_json)
    with open("records_all.json", "w") as output_file:
        json.dump(jsons, output_file)




merge_jsons("Test_folder")
