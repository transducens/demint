from sentence_splitter import SentenceSplitter
import dspy

from app.llm_grammar_checker.dspy.dspy_signature import SignatureSEC
from file_manager import FileManager
from grammar_checker import GrammarChecker
from llm.ChatFactory import ChatFactory

import errant


class StudyPlanCreator:
    def __init__(self, llm_model, max_new_tokens=250):
        # TODO: to cache/llm_evaluation.json
        prefix = "../"
        prefix = ""
        self.cache_files_paths = {
            'lang_tool_errors': 'cache/lang_tool_result.json',
            'llm_evaluation': prefix+'cache/llm_evaluation.json',
            'language_tool_evaluation':  prefix+'cache/language_tool_evaluation.json',
            'errant_all_errors':  prefix+'cache/errant_all_errors.json',
            'errant_detailed_errors':  prefix+'cache/errant_detailed_errors.json',
            'errant_corrected_errors':  prefix+'cache/errant_corrected_errors.json',
            'errant_simple_errors':  prefix+'cache/errant_simple_errors.json',
        }

        self.__chat_llm = llm_model

        self.__max_new_tokens = max_new_tokens

        self.__file_manager = FileManager()
        self.__splitter = SentenceSplitter(language='en')
        self.__grammar_checker = GrammarChecker(public_api=True)

    def create_study_plan(self, speaker_context: dict):
        llm_evaluation = self.__file_manager.read_from_json_file(self.cache_files_paths['llm_evaluation'])

        if llm_evaluation is None:
            llm_evaluation = self.use_llm_model(speaker_context)
            self.__file_manager.save_to_json_file(self.cache_files_paths['llm_evaluation'], llm_evaluation)

        language_tool_evaluation = self.__file_manager.read_from_json_file(self.cache_files_paths['language_tool_evaluation'])
        if language_tool_evaluation is None:
            language_tool_evaluation = self.use_language_tool(llm_evaluation)
            self.__file_manager.save_to_json_file(self.cache_files_paths['language_tool_evaluation'],
                                                  language_tool_evaluation)

        all_errors = self.__file_manager.read_from_json_file(self.cache_files_paths['errant_all_errors'])
        detailed_errors = self.__file_manager.read_from_json_file(self.cache_files_paths['errant_detailed_errors'])
        corrected_errors = self.__file_manager.read_from_json_file(self.cache_files_paths['errant_corrected_errors'])
        simple_errors = self.__file_manager.read_from_json_file(self.cache_files_paths['errant_simple_errors'])
        if all_errors is None:
            all_errors, detailed_errors, corrected_errors, simple_errors = self.use_errant(llm_evaluation)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_all_errors'], all_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_detailed_errors'], detailed_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_corrected_errors'], corrected_errors)
            self.__file_manager.save_to_json_file(self.cache_files_paths['errant_simple_errors'], simple_errors)

        return language_tool_evaluation

    # ====================
    # = Grammar Checker
    # ====================
    # The method uses the LanguageTool API to check the grammar of the speaker's text.
    def use_llm_model(self, speaker_context: dict):
        dspyModule = dspy.Predict(SignatureSEC)

        sentence_collection = []
        index = 1
        for speaker in speaker_context.keys():
            sentences = self.__splitter.split(speaker_context[speaker])
            for sentence in sentences:
                result = dspyModule(original_sentence=sentence)
                corrected_sentence = result['corrected_sentence']
                if corrected_sentence != sentence:
                    sentence_collection.append({
                        'index': index,
                        'speaker': speaker,
                        'sentence': sentence,
                        'corrected_sentence': corrected_sentence,
                        'explanation': result['explanation']
                    })
                    index += 1

        return sentence_collection

    def use_language_tool(self, llm_evaluation: list):
        print("Language tool is processing...")
        errors_list = []
        for evaluation in llm_evaluation:

            original_sentence = evaluation['sentence']
            errors = self.__grammar_checker.check(original_sentence)

            if len(errors) == 0:
                continue

            for error in errors:
                error['index'] = evaluation['index']
                error['speaker'] = evaluation['speaker']
                error['corrected_sentence'] = evaluation['corrected_sentence']
                error['original_sentence'] = evaluation['sentence']
                error['explanation'] = evaluation['explanation']

            errors_list.extend(errors)
        return errors_list

    def use_errant(self, llm_evaluation: list, lang='en'):
        print("ERRANT is processing...")
        annotator = errant.load(lang)

        detailed_errors = {}
        corrected_errors = {}
        simple_errors = {}

        all_errors = []
        for evaluation in llm_evaluation:
            index = evaluation['index']
            original_sentence = annotator.parse(evaluation['sentence'])
            corrected_sentence = annotator.parse(evaluation['corrected_sentence'])
            annotations = annotator.annotate(original_sentence, corrected_sentence)

            for e in annotations:
                error_type = e.type

                if error_type == "R:OTHER":
                    continue

                corrected_text = e.c_str
                original_text = e.o_str

                # Formato 1: { Tipo de error: Texto corregido: Texto original } - { lista de oraciones con este error }
                detailed_key = f"{error_type}|{corrected_text}|{original_text}"
                if detailed_key not in detailed_errors:
                    detailed_errors[detailed_key] = []
                detailed_errors[detailed_key].append(index)

                # Formato 2: { Tipo de error: Texto corregido } - { lista de oraciones с este error }
                corrected_key = f"{error_type}|{corrected_text}"
                if corrected_key not in corrected_errors:
                    corrected_errors[corrected_key] = []
                corrected_errors[corrected_key].append(index)

                # Formato 3: { Tipo de error } - { lista de oraciones con este error }
                if error_type not in simple_errors:
                    simple_errors[error_type] = []
                simple_errors[error_type].append(index)

                all_errors.append({
                    'index': index,
                    'speaker': evaluation['speaker'],
                    'sentence': evaluation['sentence'],
                    'corrected_sentence': evaluation['corrected_sentence'],
                    'o_start': e.o_start,
                    'o_end': e.o_end,
                    'original_text': original_text,
                    'c_start': e.c_start,
                    'c_end': e.c_end,
                    'corrected_text': corrected_text,
                    'error_type': error_type,
                    }
                )

        return all_errors, detailed_errors, corrected_errors, simple_errors
    def get_diarization_grouped_by_speaker(self, diarization_result):
        # Loads diarization results from a file, if it exists
        speakers_context = {}  # List of the transcripts for each speaker
        for transcript in diarization_result:
            parts = transcript.split("||")
            if len(parts) > 1:
                speaker_label, text = parts[0].split("]")[1].strip(), parts[1].strip()

                if speaker_label in speakers_context:
                    speakers_context[speaker_label] += " " + text
                else:
                    speakers_context[speaker_label] = text

        return speakers_context


if __name__ == '__main__':
    llm_model = "meta-llama/Meta-Llama-3-8B-Instruct"  # "google/gemma-1.1-2b-it"
    file_manager = FileManager()
    diarization = file_manager.read_from_json_file("../cache/diarization_result_test.json")
    chat_llm = ChatFactory.get_instance(llm_model)
    creator = StudyPlanCreator(chat_llm)
    speakers_context = creator.get_diarization_grouped_by_speaker(diarization)
    study_plan = creator.create_study_plan(speakers_context)
