import language_tool_python as lt


class GrammarChecker:
    # Can run in public API mode or local mode (.jar server)
    def __init__(self, language='en-US', public_api=False):
        if public_api:
            self.__tool = lt.LanguageToolPublicAPI(language)
            print("Using language tool public API.")
        else:
            self.__tool = lt.LanguageTool(language)
            print("Using language tool local.")


    # Given a text (string)
    # Return a list of matches (dicts)
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


    # Given a text (string)
    # Return a corrected text (string)
    def correct(self, text: str):
        matches = self.__tool.check(text)
        return lt.utils.correct(text, matches)


    # Given a list of sentences (strings)
    # Return a list of matches for all sentences (dicts)
    def check_sentences(self, sentences: list):
        all_matches = []
        for sentence in sentences:
            matches = self.check(sentence)
            if matches:
                all_matches.extend(matches)

        sorted_matches = sorted(all_matches, key=lambda x: x['ruleId'])

        return sorted_matches


    # Given a list of sentences (strings)
    # Return a list of corrected sentences (strings)
    def correct_sentences(self, sentences: list):
        corrected_sentences = []
        for sentence in sentences:
            corrected = self.correct(sentence)
            corrected_sentences.extend(corrected)
        return corrected_sentences
    

    # Close the language tool (background .jar server)
    def close(self):
        self.__tool.close()
