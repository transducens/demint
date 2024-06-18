import errant
from app.file_manager import FileManager

def prepare_sorted_sentence_collection(__file_manager, speaker_context: list):
    raw_sentence_collection = []
    index = 1
    print("Creating sorted sentence collection ...")
    for line in speaker_context:    # 0 time, 1 speaker, 2 sentence
        raw_sentence_collection.append({
            'index': index,
            'speaker': line[1],
            'original_sentence': line[2]
        })
        index += 1

    __file_manager.save_to_json_file('app/new_cache/raw_sorted_sentence_collection.json', raw_sentence_collection)

    return raw_sentence_collection