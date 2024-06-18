import os
from .grammar_checker import GrammarChecker
from .obtain_errores import obtain_errors
def rag_sentences(__file_manager, __rag_engine):
    if not os.path.isfile('app/new_cache/explained_sentences.json'):
        __grammar_checker_lt = GrammarChecker(gec_model="LT_API")
        __grammar_checker_t5 = GrammarChecker(gec_model="T5")
        obtain_errors(__file_manager, __grammar_checker_lt, __grammar_checker_t5, False)
        
    explained_sentences = __file_manager.read_from_json_file('app/new_cache/explained_sentences.json')

    keysList = list(explained_sentences.keys())

    for new_index in keysList:
        sentence = explained_sentences[new_index]
        original_sentence = sentence['sentence']
        t5_checked_sentence = sentence['t5_checked_sentence']
        llm_explained = sentence['llm_explanation']
        lt_errors = sentence['language_tool']

        error_description_list = []
        for error in sentence["errant"]:
            error_type = error['error_type']

            original_text = error['original_text']
            corrected_text = error['corrected_text']

            errant_llm_explained = error['llm_explanation']

            rag = []
            if __rag_engine is not None:
                rag = __rag_engine.search(errant_llm_explained, 5)

            error_description = {
                'index': new_index,
                'speaker': sentence['speaker'],
                'sentence': original_sentence,
                'corrected_sentence': t5_checked_sentence,
                'o_start': error['o_start'],
                'o_end': error['o_end'],
                'original_text': original_text,
                'c_start': error['c_start'],
                'c_end': error['c_end'],
                'corrected_text': corrected_text,
                'error_type': error_type,
                'llm_explanation': errant_llm_explained,
                'rag': rag,
            }

            error_description_list.append(error_description)

        explained_sentences[new_index] = {
            'speaker': sentence['speaker'],
            'sentence' : original_sentence,
            't5_checked_sentence': t5_checked_sentence,
            'llm_explanation': llm_explained,
            'language_tool': lt_errors,
            'errant': error_description_list,
        }

    __file_manager.save_to_json_file('app/new_cache/rag_sentences.json', explained_sentences)

    return