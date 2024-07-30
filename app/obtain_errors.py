import errant
import os

from app.file_manager import FileManager
import app.prepare_sentences as prepare_sentences
from app.grammar_checker import GrammarChecker


input_directory = "./cache/raw_sorted_sentence_collection"
output_directories = {
    'errant_all_errors':                './cache/errant_all_evaluation',
    'errant_detailed_errors':           './cache/errant_detailed_evaluation',
    'errant_corrected_errors':          './cache/errant_corrected_evaluation',
    'errant_simple_errors':             './cache/errant_simple_evaluation',       
}


# TODO add the other formats
def obtain_errors(file_manager, grammar_checker_t5, lang='en', input_path="", output_path=""):
    if not os.path.isfile(input_path):
        print(f"{input_path} is not found.")
        print(f"Processing {input_path}")
        prepare_sentences.main()

    raw_sentence_collection = file_manager.read_from_json_file(input_path)
    if raw_sentence_collection is None:
        print(f"Error: {input_path} not found.")
        return None
    
    annotator = errant.load(lang)

    detailed_errors = {}
    corrected_errors = {}
    simple_errors = {}

    all_errors = []
    for index, value in raw_sentence_collection.items(): 
        original_sentence = value['original_sentence']

        #lt_errors = grammar_checker_lt.check(original_sentence)
        t5_checked_sentence = grammar_checker_t5.correct_sentences([original_sentence])[0]

        if original_sentence == t5_checked_sentence:
            continue

        #lt_errors = grammar_checker_lt.check(original_sentence)

        annotated_original_sentence = annotator.parse(original_sentence)
        annotated_t5_checked_sentence = annotator.parse(t5_checked_sentence)
        annotations = annotator.annotate(annotated_original_sentence, annotated_t5_checked_sentence)            

        for e in annotations:
            print(e)
            error_type = e.type

            original_text = e.o_str
            corrected_text = e.c_str

            error_description = {
                'index': index,
                'speaker': value['speaker'],
                'original_sentence': original_sentence,
                'corrected_sentence': t5_checked_sentence,
                'o_start': e.o_start,
                'o_end': e.o_end,
                'original_text': original_text,
                'c_start': e.c_start,
                'c_end': e.c_end,
                'corrected_text': corrected_text,
                'error_type': error_type,
            }
            
            all_errors.append(error_description)

        #explained_sentences[index] = {
        #    'speaker': evaluation['speaker'],
        #    'sentence' : original_sentence,
        #    't5_checked_sentence': t5_checked_sentence,
        #    'language_tool': lt_errors,
        #    'errant': error_description_list,
        #}

    file_manager.save_to_json_file(output_path, all_errors)

    return all_errors, detailed_errors, corrected_errors, simple_errors

def obtain_errors_of_directory(
        file_manager: FileManager,
        grammar_checker_t5: GrammarChecker,
        lang='en',
        sentence_collection_directory="cache/raw_sorted_sentence_collection", 
        errant_directory="cache/errant_all_evaluation", 
    ):
    # Loop through the files in the directory
    for sentence_collection_file in os.listdir(sentence_collection_directory):
        if sentence_collection_file[0] == ".":
            continue

        sentence_collection_path = os.path.join(sentence_collection_directory, sentence_collection_file)
        errant_evaluation_path = os.path.join(errant_directory, sentence_collection_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(sentence_collection_path):
            print(f"Found diarized transcript file: {sentence_collection_path}")

            obtain_errors(
                file_manager, 
                grammar_checker_t5, 
                'en', 
                sentence_collection_path, 
                errant_evaluation_path)


def main():
    global input_directory, output_directories
    file_manager = FileManager()
    grammar_checker_t5 = GrammarChecker(gec_model="T5")

    obtain_errors_of_directory(
        file_manager, 
        grammar_checker_t5, 
        'en', 
        input_directory, 
        output_directories['errant_all_errors'])


if __name__ == '__main__':
    main()