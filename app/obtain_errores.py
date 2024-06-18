import errant
import os

from .audio_extractor import AudioExtractor

from .prepare_sentences import prepare_sorted_sentence_collection
def obtain_errors(__file_manager, __grammar_checker_lt, __grammar_checker_t5, __is_logging_enabled, lang='en'):
    if not os.path.isfile('app/new_cache/raw_sorted_sentence_collection.json'):
        diarization = __file_manager.read_from_json_file("../cache/diarization_result_test.json")
        speakers_context = AudioExtractor().process_diarizated_text(diarization)
        prepare_sorted_sentence_collection(__file_manager, speakers_context)

    raw_sentence_collection = __file_manager.read_from_json_file('app/new_cache/raw_sorted_sentence_collection.json')
    
    annotator = errant.load(lang)

    explained_sentences = {}
    detailed_errors = {}
    corrected_errors = {}
    simple_errors = {}

    all_errors = []
    for evaluation in raw_sentence_collection:
        index = evaluation['index']
            
        original_sentence = evaluation['original_sentence']

        lt_errors = __grammar_checker_lt.check(original_sentence)
        t5_checked_sentence = __grammar_checker_t5.correct_sentences([original_sentence])[0]

        if original_sentence == t5_checked_sentence:
            continue

        lt_errors = __grammar_checker_lt.check(original_sentence)

        annotated_original_sentence = annotator.parse(original_sentence)
        annotated_t5_checked_sentence = annotator.parse(t5_checked_sentence)
        annotations = annotator.annotate(annotated_original_sentence, annotated_t5_checked_sentence)            

        error_description_list = []
        for e in annotations:
            print(e)
            print(type(e))
            error_type = e.type

            original_text = e.o_str
            corrected_text = e.c_str

            error_description = {
                'index': index,
                'speaker': evaluation['speaker'],
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
            
            error_description_list.append(error_description)

        explained_sentences[index] = {
            'speaker': evaluation['speaker'],
            'sentence' : original_sentence,
            't5_checked_sentence': t5_checked_sentence,
            'language_tool': lt_errors,
            'errant': error_description_list,
        }

        if __is_logging_enabled and len(explained_sentences[original_sentence]) > 1:
            print(f'====================== original_sentence {index} ======================')
            print(explained_sentences[original_sentence])

        if __is_logging_enabled and len(explained_sentences[original_sentence]) > 1:
            print(f'====================== original_sentence {index} ======================')
            print(explained_sentences[original_sentence])

    __file_manager.save_to_json_file('app/new_cache/errant_sentences.json', explained_sentences)

    return all_errors, detailed_errors, corrected_errors, simple_errors, explained_sentences