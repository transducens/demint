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
else:
    from .file_manager import FileManager
    from .grammar_checker import GrammarChecker
    from .llm.ChatFactory import ChatFactory
    from .audio_extractor import AudioExtractor
    from .rag.RAGFactory import RAGFactory
    prefix = ""

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
            raw_sentence_collection = self.prepare_sorted_sentence_collection(speaker_context)
            self.__file_manager.save_to_json_file(self.cache_files_paths['raw_sorted_sentence_collection'], raw_sentence_collection)

        explained_sentences = self.__file_manager.read_from_json_file(self.cache_files_paths['explained_sentences'])
        if explained_sentences is None:
            print("explain_sentences is processing...")
            errant_all_errors, errant_detailed_errors, errant_corrected_errors, errant_simple_errors, explained_sentences, sentences_by_speaker_to_check = self.explain_sentences(raw_sentence_collection)
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

    # ====================
    # = Grammar Checker
    # ====================
    def prepare_sorted_sentence_collection(self, speaker_context: list):
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

        return raw_sentence_collection

    def explain_sentences(self, raw_sentence_collection: list, lang='en'):
        annotator = errant.load(lang)

        explained_sentences = {}
        sentences_by_speaker_to_check = {}
        detailed_errors = {}
        corrected_errors = {}
        simple_errors = {}

        all_errors = []
        for evaluation in raw_sentence_collection:
            index = evaluation['index']
            
            original_sentence = evaluation['original_sentence']

            lt_errors = self.__grammar_checker_lt.check(original_sentence)
            t5_checked_sentence = self.__grammar_checker_t5.correct_sentences([original_sentence])[0]

            if original_sentence == t5_checked_sentence:
                continue

            final_prompt = (
                f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
                f"Original: {original_sentence}\n"
                f"Corrected: {t5_checked_sentence}\n\n"
                f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
            )

            llm_explained = self.__chat_llm.get_answer(final_prompt)
            lt_errors = self.__grammar_checker_lt.check(original_sentence)

            annotated_original_sentence = annotator.parse(original_sentence)
            annotated_t5_checked_sentence = annotator.parse(t5_checked_sentence)
            annotations = annotator.annotate(annotated_original_sentence, annotated_t5_checked_sentence)            

            error_description_list = []
            for e in annotations:
                error_type = e.type

                corrected_text = e.c_str
                original_text = e.o_str

                final_prompt = (
                    f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
                    f"{e}\n"
                )

                errant_llm_explained = self.__chat_llm.get_answer(final_prompt)

                rag = []
                if self.__rag_engine is not None:
                    rag = self.__rag_engine.search(errant_llm_explained, 1)

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
                    'llm_explanation': errant_llm_explained,
                    'rag': rag,
                    }

                #print(errant_llm_explained)
                error_description_list.append(error_description)
                # Formato 1: { Tipo de error: Texto corregido: Texto original } - { lista de oraciones con este error }
                detailed_key = f"{error_type}|{corrected_text}|{original_text}"
                if detailed_key not in detailed_errors:
                    detailed_errors[detailed_key] = []
                detailed_errors[detailed_key].append(error_description)

                # Formato 2: { Tipo de error: Texto corregido } - { lista de oraciones с este error }
                corrected_key = f"{error_type}|{corrected_text}"
                if corrected_key not in corrected_errors:
                    corrected_errors[corrected_key] = []

                error_description['original_text'] = original_text
                corrected_errors[corrected_key].append(error_description)

                # Formato 3: { Tipo de error } - { lista de oraciones con este error }
                if error_type not in simple_errors:
                    simple_errors[error_type] = []

                error_description['corrected_key'] = corrected_key
                simple_errors[error_type].append(error_description)

                error_description['error_type'] = error_type
                all_errors.append(error_description)

            explained_sentences[index] = {
                'speaker': evaluation['speaker'],
                't5_checked_sentence': t5_checked_sentence,
                'llm_explanation': llm_explained,
                'language_tool': lt_errors,
                'errant': error_description_list,
            }

            if evaluation['speaker'] not in sentences_by_speaker_to_check:
                sentences_by_speaker_to_check[evaluation['speaker']] = []
            sentences_by_speaker_to_check[evaluation['speaker']].append(index)

            if self.__is_logging_enabled and len(explained_sentences[original_sentence]) > 1:
                print(f'====================== original_sentence {index} ======================')
                print(explained_sentences[original_sentence])

            if self.__is_logging_enabled and len(explained_sentences[original_sentence]) > 1:
                print(f'====================== original_sentence {index} ======================')
                print(explained_sentences[original_sentence])

        return all_errors, detailed_errors, corrected_errors, simple_errors, explained_sentences, sentences_by_speaker_to_check

if __name__ == '__main__':
    llm_modelId = "google/gemma-1.1-7b-it"  # "google/gemma-1.1-2b-it"
    file_manager = FileManager()
    diarization = file_manager.read_from_json_file("../cache/diarization_result_test.json")
    chat_llm = ChatFactory.get_instance(llm_modelId)
    ratatouille_rag = RAGFactory().get_instance("ragatouille")
    creator = StudyPlanCreator(chat_llm, ratatouille_rag)
    speakers_context = AudioExtractor().process_diarizated_text(diarization)
    study_plan = creator.create_study_plan(speakers_context)
