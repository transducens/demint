from sentence_splitter import SentenceSplitter

from app.file_manager import FileManager
from app.grammar_checker import GrammarChecker


class StudyPlanCreator:
    def __init__(self, llm_model, max_new_tokens=250):
        self.cache_files_paths = {'lang_tool_errors': 'cache/lang_tool_result.json'}

        self.__chat_llm = llm_model
        self.__max_new_tokens = max_new_tokens

        self.__file_manager = FileManager()
        self.__splitter = SentenceSplitter(language='en')
        self.__grammar_checker = GrammarChecker()

    def create_study_plan(self, speaker_context: dict, speaker_id: str):
        study_plan = self.__use_language_tool(speaker_context, speaker_id)
        study_plan = self.__use_llm_model(study_plan)

        return study_plan

    # ====================
    # = Grammar Checker
    # ====================
    def __use_language_tool(self, speakers_context: dict, speaker_id: str):
        speaker_errors = []
        errors = self.__file_manager.read_from_json_file(self.cache_files_paths['lang_tool_errors'])

        if errors:
            speaker_errors = [error for error in errors if error['speakerId'] == speaker_id]

        if len(speaker_errors) > 0:
            print("Errors from Language tool loaded from file.")
        else:
            print("Language tool is processing...")
            print(f"Speaker: {speaker_id}")
            speaker_text = speakers_context[speaker_id]
            sentences = self.__splitter.split(speaker_text)

            errors = self.__grammar_checker.check_sentences(sentences)

            for error in errors:
                error['speakerId'] = speaker_id

            self.__file_manager.save_to_json_file(self.cache_files_paths['lang_tool_errors'], errors, 'a')

        return errors

    def __use_llm_model(self, study_plan: list):
        for i, error in enumerate(study_plan):
            prompt = ("The user made the following mistake in English.\n" +
                      f"{error}\n" +
                      "Explain the error directly to the user using a personal approach.\n" +
                      "Example of the answer to the user: 'I noticed that in a recent dialogue, you made a "
                      "mistake {description of the mistake}. Would you like to practice it? I'm here to help you "
                      "understand and improve.'\n'")

            study_plan[i]['llm_response'] = self.__chat_llm.get_answer(prompt, self.__max_new_tokens)

        return study_plan
