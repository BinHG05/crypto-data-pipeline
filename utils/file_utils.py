import os
import json
from datetime import datetime

# tách logic lưu file

def save_json(data , source):
    #Lay ngay hien tai
    date_str = datetime.now().strftime("%Y-%m-%d")

    #Tao Path
    dir_path = f"data/raw/{source}/{date_str}"
    os.makedirs(dir_path , exist_ok= True)

    file_path = f"{dir_path}/data.jsonl"

    with open(file_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

    print(f"Saved data to {file_path}")