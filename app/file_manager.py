import json
import os


class FileManager:
    @staticmethod
    def read_from_json_file(file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        else:
            print(f"JSON file not found: {file_path}", flush=True)
        return None

    @staticmethod
    def save_to_json_file(file_path, result, mode='w'):
        if mode not in ['w', 'a']:
            mode = 'w'

        if mode == 'a' and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r+', encoding="utf-8") as file:
                try:
                    file_data = json.load(file)
                    if isinstance(file_data, list):
                        file.seek(0)
                        file_data.extend(result)
                        json.dump(file_data, file, indent=4, ensure_ascii=False)
                        file.truncate()
                    else:
                        raise ValueError("JSON file does not contain a list")
                except json.JSONDecodeError:
                    file.seek(0)
                    json.dump(result, file, indent=4, ensure_ascii=False)
                    file.truncate()
        else:
            with open(file_path, 'w', encoding="utf-8") as file:
                json.dump(result, file, indent=4, ensure_ascii=False)
