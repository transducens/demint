import errant
import os


# Local imports
local = False
if __name__ == '__main__':
    local = True

if local:
    from file_manager import FileManager
    import prepare_sentences
    from grammar_checker import GrammarChecker
else:
    from app.file_manager import FileManager
    import app.prepare_sentences
    from app.grammar_checker import GrammarChecker


input_file="../cache/raw_sorted_sentence_collection.json"
output_files = {
    'errant_all_errors':                '../cache/errant_all_evaluation.json',
    'errant_detailed_errors':           '../cache/errant_detailed_evaluation.json',
    'errant_corrected_errors':          '../cache/errant_corrected_evaluation.json',
    'errant_simple_errors':             '../cache/errant_simple_evaluation.json',       
}


# TODO add the other formats
def obtain_errors(file_manager, grammar_checker_t5, lang='en'):
    if not os.path.isfile(input_file):
        prepare_sentences.main()

    raw_sentence_collection = file_manager.read_from_json_file(input_file)
    if raw_sentence_collection is None:
        print(f"Error: {input_file} not found.")
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
                'sentence': original_sentence,
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

    file_manager.save_to_json_file(output_files['errant_all_errors'], all_errors)

    return all_errors, detailed_errors, corrected_errors, simple_errors


def main():
    file_manager = FileManager()
    grammar_checker_t5 = GrammarChecker(gec_model="T5")

    obtain_errors(file_manager, grammar_checker_t5)


if __name__ == '__main__':
    main()