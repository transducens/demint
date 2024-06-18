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

def obtain_errors(__file_manager, __grammar_checker_lt, __grammar_checker_t5, __is_logging_enabled, lang='en'):
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

        #if index not in explained_sentences:
        #   explained_sentences[index] = []

        #final_prompt = (
        #    f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
        #    f"Original: {original_sentence}\n"
        #    f"Corrected: {t5_checked_sentence}\n\n"
        #    f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
        #)

        #llm_explained = __chat_llm.get_answer(final_prompt)
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

            #final_prompt = (
            #    f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
            #    f"{e}\n"
            #)

            #errant_llm_explained = __chat_llm.get_answer(final_prompt)

            #rag = []
            #if __rag_engine is not None:
            #    rag = __rag_engine.search(errant_llm_explained, 1)

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
                #'llm_explanation': errant_llm_explained,
                #'rag': rag,
            }

            #print(errant_llm_explained)
            error_description_list.append(error_description)

        explained_sentences[index] = {
            'speaker': evaluation['speaker'],
            'sentence' : original_sentence,
            't5_checked_sentence': t5_checked_sentence,
            #'llm_explanation': llm_explained,
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

def explain_sentences(__file_manager, __chat_llm):
    explained_sentences = __file_manager.read_from_json_file('app/new_cache/errant_sentences.json')

    print(type(explained_sentences))
    keysList = list(explained_sentences.keys())

    for new_index in keysList:
        sentence = explained_sentences[new_index]
        original_sentence = sentence['sentence']
        t5_checked_sentence = sentence['t5_checked_sentence']

        final_prompt = (
            f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
            f"Original: {original_sentence}\n"
            f"Corrected: {t5_checked_sentence}\n\n"
            f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
        )

        llm_explained = __chat_llm.get_answer(final_prompt)
        lt_errors = sentence['language_tool']

        error_description_list = []
        for error in sentence["errant"]:
            error_type = error['error_type']

            original_text = error['original_text']
            corrected_text = error['corrected_text']

            final_prompt = (
                f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
                f"{error}\n"
            )

            errant_llm_explained = __chat_llm.get_answer(final_prompt)

            error_description = {
                'index': new_index,
                'speaker': sentence['speaker'],
                'sentence': original_sentence,
                'corrected_sentence': t5_checked_sentence,
                'o_start': error['o_start'],
                'o_end': error['o_end'],
                'original_text': original_text,
                'c_start': error['c_start'],
                'c_end': error['c_start'],
                'corrected_text': corrected_text,
                'error_type': error_type,
                'llm_explanation': errant_llm_explained,
                #'rag': rag,
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

    __file_manager.save_to_json_file('app/new_cache/explained_sentences.json', explained_sentences)

    return

def rag_sentences(__file_manager, __rag_engine):
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

        explained_sentences[index] = {
            'speaker': sentence['speaker'],
            'sentence' : original_sentence,
            't5_checked_sentence': t5_checked_sentence,
            'llm_explanation': llm_explained,
            'language_tool': lt_errors,
            'errant': error_description_list,
        }

    __file_manager.save_to_json_file('app/new_cache/rag_sentences.json', explained_sentences)

    return

"""if __name__ == '__main__':
    __file_manager = FileManager()
    raw_sentence_collection = prepare_sorted_sentence_collection(__file_manager, speaker_context)"""