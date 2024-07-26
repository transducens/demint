################################
##        DEPRECATED          ##
################################


from sentence_splitter import SentenceSplitter

local = False

if __name__ == '__main__':
    local = True

if local:
    from file_manager import FileManager
    from grammar_checker import GrammarChecker
    from llm.ChatFactory import ChatFactory
    from audio_extractor import AudioExtractor
    from rag.RAGFactory import RAGFactory
    prefix = "../"

    from error_identification import prepare_sorted_sentence_collection, explain_sentences, obtain_errors
else:
    from .file_manager import FileManager
    from .grammar_checker import GrammarChecker
    from .llm.ChatFactory import ChatFactory
    from .audio_extractor import AudioExtractor
    from .rag.RAGFactory import RAGFactory
    prefix = ""

    from .error_identification import prepare_sorted_sentence_collection, explain_sentences, obtain_errors

import errant

class StudyPlanCreator:
    def __init__(self, llm_model, rag_engine = None, max_new_tokens=250, is_logging_enabled = False):
        self.cache_files_paths = {
            'raw_sorted_sentence_collection': prefix + 'cache/raw_sorted_sentence_collection.json',
            'explained_sentences': prefix + 'cache/explained_sentences.json',
            'sentences_by_speaker_to_check': prefix + 'cache/sentences_by_speaker_to_check.json',
            'errant_all_errors':  prefix+'cache/errant_all_evaluation.json',
            'errant_detailed_errors':  prefix+'cache/errant_detailed_evaluation.json',
            'errant_corrected_errors':  prefix+'cache/errant_corrected_evaluation.json',
            'errant_simple_errors':  prefix+'cache/errant_simple_evaluation.json',
        }

        self.__chat_llm = llm_model
        self.__max_new_tokens = max_new_tokens

        self.__file_manager = FileManager()
        self.__splitter = SentenceSplitter(language='en')
        self.__grammar_checker_lt = GrammarChecker(gec_model="LT_API")
        self.__grammar_checker_t5 = GrammarChecker(gec_model="T5")

        self.__rag_engine = rag_engine
        self.__is_logging_enabled = is_logging_enabled

    def create_study_plan(self, speaker_context: list):
        print("create_study_plan is started...")

        raw_sentence_collection = self.__file_manager.read_from_json_file(self.cache_files_paths['raw_sorted_sentence_collection'])
        if raw_sentence_collection is None:
            print("raw_sorted_sentence_collection is processing...")

            raw_sentence_collection = prepare_sorted_sentence_collection(self.__file_manager, speaker_context)

            self.__file_manager.save_to_json_file(self.cache_files_paths['raw_sorted_sentence_collection'], raw_sentence_collection)

        explained_sentences = self.__file_manager.read_from_json_file(self.cache_files_paths['explained_sentences'])
        if explained_sentences is None:
            print("explain_sentences is processing...")
            errant_all_errors, errant_detailed_errors, errant_corrected_errors, errant_simple_errors, explained_sentences = obtain_errors(self.__file_manager, self.__grammar_checker_lt, self.__grammar_checker_t5, self.__chat_llm, self.__rag_engine, self.__is_logging_enabled, raw_sentence_collection)

            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_all_errors'],
                                                  errant_all_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_detailed_errors'],
                                                  errant_detailed_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_corrected_errors'],
                                                  errant_corrected_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['explained_sentences'],
                                                  explained_sentences)
            self.__file_manager.save_to_json_file(self.cache_files_paths['sentences_by_speaker_to_check'],
                                                  sentences_by_speaker_to_check)

            sorted_errant_simple_errors = sorted(errant_simple_errors.items(), key=lambda item: len(item[1]), reverse=True)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_simple_errors'], sorted_errant_simple_errors)

        return explained_sentences


if __name__ == '__main__':

    file_manager = FileManager()
    __grammar_checker_lt = GrammarChecker(gec_model="LT_API")
    __grammar_checker_t5 = GrammarChecker(gec_model="T5")

    diarization = file_manager.read_from_json_file("../cache/diarization_result_test.json")
    speakers_context = AudioExtractor().process_diarizated_text(diarization)

    llm_modelId = "google/gemma-1.1-7b-it"  # "google/gemma-1.1-2b-it"
    __chat_llm = ChatFactory.get_instance(llm_modelId)

    raw_sentence_collection = prepare_sorted_sentence_collection(file_manager, speakers_context)
    errant_all_errors, errant_detailed_errors, errant_corrected_errors, errant_simple_errors, explained_sentences = obtain_errors(file_manager, __grammar_checker_lt, __grammar_checker_t5, False)

    explain_sentences(file_manager, __chat_llm)

