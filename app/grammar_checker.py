import language_tool_python


class GrammarChecker:
    def __init__(self, language='en-US', public_api=False):
        if public_api:
            self.__tool = language_tool_python.LanguageToolPublicAPI(language)
            print("Using language tool public API.")
        else:
            self.__tool = language_tool_python.LanguageTool(language)
            print("Using language tool local.")

    def check(self, text: str):
        matches = self.__tool.check(text)
        matches_dicts = [{
            'ruleId': match.ruleId,
            'message': match.message,
            'replacements': match.replacements,
            'offsetInContext': match.offsetInContext,
            'context': match.context,
            'offset': match.offset,
            'errorLength': match.errorLength,
            'category': match.category,
            'ruleIssueType': match.ruleIssueType,
            'sentence': match.sentence
        } for match in matches]
        return matches_dicts

    def correct(self, text: str):
        matches = self.__tool.check(text)
        return language_tool_python.utils.correct(text, matches)

    def check_sentences(self, sentences: list):
        all_matches = []
        for sentence in sentences:
            matches = self.check(sentence)
            if matches:
                all_matches.extend(matches)

        sorted_matches = sorted(all_matches, key=lambda x: x['ruleId'])

        return sorted_matches

    def correct_sentences(self, sentences: list):
        corrected_sentences = []
        for sentence in sentences:
            corrected = self.correct(sentence)
            corrected_sentences.extend(corrected)
        return corrected_sentences
