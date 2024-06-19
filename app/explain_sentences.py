import os

# Local imports
local = False
if __name__ == '__main__':
    local = True

if local:
    from file_manager import FileManager
    from grammar_checker import GrammarChecker
    import obtain_errors
else:
    from app.file_manager import FileManager
    from app.grammar_checker import GrammarChecker
    import app.obtain_errors


input_file = "../cache/errant_all_evaluation.json"


def explain_sentences(file_manager, chat_llm):
    if not os.path.isfile(input_file):
        obtain_errors.main()

    explained_sentences = __file_manager.read_from_json_file('app/new_cache/errant_sentences.json')

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