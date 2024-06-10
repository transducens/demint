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
    def __init__(self, llm_model, rag_engine, max_new_tokens=250):
        self.cache_files_paths = {
            'raw_sentence_collection': prefix + 'cache/raw_sentence_collection.json',
            'explained_sentences': prefix + 'cache/explained_sentences.json',
            'errant_all_errors':  prefix+'cache/errant_all_evaluation.json',
            'errant_detailed_errors':  prefix+'cache/errant_detailed_evaluation.json',
            'errant_corrected_errors':  prefix+'cache/errant_corrected_evaluation.json',
            'errant_simple_errors':  prefix+'cache/errant_simple_evaluation.json',
        }

        self.__chat_llm = llm_model
        self.__max_new_tokens = max_new_tokens

        self.__file_manager = FileManager()
        self.__splitter = SentenceSplitter(language='en')
        self.__grammar_checker = GrammarChecker(public_api=False)

        self.__rag_engine = rag_engine

    def create_study_plan(self, speaker_context: dict):
        print("create_study_plan is started...")

        raw_sentence_collection = self.__file_manager.read_from_json_file(self.cache_files_paths['raw_sentence_collection'])
        if raw_sentence_collection is None:
            print("raw_sentence_collection is processing...")
            raw_sentence_collection = self.prepare_sentence_collection(speaker_context)
            self.__file_manager.save_to_json_file(self.cache_files_paths['raw_sentence_collection'], raw_sentence_collection)

        explained_sentences = self.__file_manager.read_from_json_file(self.cache_files_paths['explained_sentences'])
        if explained_sentences is None:
            print("explain_sentences is processing...")
            errant_all_errors, errant_detailed_errors, errant_corrected_errors, errant_simple_errors, explained_sentences = self.explain_sentences(raw_sentence_collection)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_all_errors'],
                                                  errant_all_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_detailed_errors'],
                                                  errant_detailed_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_corrected_errors'],
                                                  errant_corrected_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['explained_sentences'],
                                                  explained_sentences)

            sorted_errant_simple_errors = sorted(errant_simple_errors.items(), key=lambda item: len(item[1]), reverse=True)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_simple_errors'], sorted_errant_simple_errors)

        return explained_sentences

    # ====================
    # = Grammar Checker
    # ====================
    def prepare_sentence_collection(self, speaker_context: dict):
        raw_sentence_collection = []
        index = 1
        for speaker in speaker_context.keys():
            print("Speaker started: ", speaker)
            sentences = self.__splitter.split(speaker_context[speaker])
            print("Count of sentences: ", len(sentences))
            for sentence in sentences:
                    raw_sentence_collection.append({
                        'index': index,
                        'speaker': speaker,
                        'original_sentence': sentence
                    })
                    index += 1

        return raw_sentence_collection

    def explain_sentences(self, raw_sentence_collection: list, lang='en'):
        annotator = errant.load(lang)

        explained_sentences = {}
        detailed_errors = {}
        corrected_errors = {}
        simple_errors = {}

        all_errors = []
        for evaluation in raw_sentence_collection:
            index = evaluation['index']
            original_sentence = evaluation['original_sentence']

            lt_errors = self.__grammar_checker.check(original_sentence)
            t5_checked_sentence = self.__grammar_checker.t5_check_sentence(original_sentence)

            if original_sentence == t5_checked_sentence:
                continue

            if original_sentence not in explained_sentences:
               explained_sentences[original_sentence] = []

            print(f'====================== original_sentence {index} ======================')
            print(original_sentence)
            print(f'---T5---')
            print(t5_checked_sentence)
            print(f'---LLM---')
            final_prompt = (
                f"You are an English teacher. Please explain the errors that were corrected in the following sentence:\n\n"
                f"Original: {original_sentence}\n"
                f"Corrected: {t5_checked_sentence}\n\n"
                f"List and explain the errors found in the original sentence and how they were corrected in the revised sentence."
            )
            llm_explained = self.__chat_llm.get_answer(final_prompt)
            print(llm_explained)
            print(f'---LT---')
            print(lt_errors)
            print('---ERRANT---')

            annotated_original_sentence = annotator.parse(original_sentence)
            annotated_t5_checked_sentence = annotator.parse(t5_checked_sentence)
            annotations = annotator.annotate(annotated_original_sentence, annotated_t5_checked_sentence)

            error_description_list = []
            for e in annotations:
                error_type = e.type

                if error_type.split(':')[1] in ['OTHER']:
                    continue

                corrected_text = e.c_str
                original_text = e.o_str

                final_prompt = (
                    f"Please explain the errors that were found as briefly as possible, focusing only on the main idea and the broken rule in the English language:\n\n"
                    f"{e}\n"
                )

                errant_llm_explained = self.__chat_llm.get_answer(final_prompt)
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

                print(errant_llm_explained)
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

            explained_sentences[original_sentence].append({
                'index': evaluation['index'],
                'speaker': evaluation['speaker'],
                't5_checked_sentence': t5_checked_sentence,
                'llm_explanation': llm_explained,
                'language_tool': lt_errors,
                'errant': error_description_list,
            })

        return all_errors, detailed_errors, corrected_errors, simple_errors, explained_sentences

if __name__ == '__main__':
    llm_modelId = "google/gemma-1.1-7b-it"  # "google/gemma-1.1-2b-it"
    file_manager = FileManager()
    diarization = file_manager.read_from_json_file("../cache/diarization_result_test.json")
    chat_llm = ChatFactory.get_instance(llm_modelId)
    rag_engine = RAGFactory().get_instance("ragatouille")
    creator = StudyPlanCreator(chat_llm, rag_engine)
    speakers_context = AudioExtractor().get_diarization_grouped_by_speaker(diarization)
    study_plan = creator.create_study_plan(speakers_context)
