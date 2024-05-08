import language_tool_python as lt

###
# Errors detected by the grammar checker:
# - Category: Collocation ("COLLOCATIONS")
# - Category: Confused words ("CONFUSED_WORDS")
# - (Not included but interesant) Categoty: Creative writing ("CREATIVE_WRITING")
# - Category: Grammar ("GRAMMAR")
# - Category: Miscellaneous ("MISC") except rule IDs: (EN_COMPOUNDS, EN_CONSISTENT_APOS, EN_SIMPLE_REPLACE, REP_PASSIVE_VOICE,  REP_THANK_YOU_FOR)
# - (Inactive) (Partially) Category: Possible Typo ("TYPOS")
# - Category: Redundant Phrases ("REDUNDANCY")
# - Category: Repetitions ("REPETITIONS_STYLE")
###

class GrammarChecker:
    # Can run in public API mode or local mode (.jar server)

    def __init__(self, language='en-US', public_api=False, filter_errors=True):
        if public_api:
            self.__tool = lt.LanguageToolPublicAPI(language)
            print("Using language tool public API.")
        else:

            self.__tool = lt.LanguageTool(language, config={
                'cacheSize': 1024, # Improves performance
                'pipelineCaching': True,
            })

            print("Using language tool local.")
        self.__categories = [
            'COLLOCATIONS',
            'CONFUSED_WORDS',
            'GRAMMAR',
            'MISC',  # Partially included
            'REDUNDANCY',
            'REPETITIONS_STYLE'
        ]
        self.__avoid_rule_ids = [
            'EN_COMPOUNDS',
            'EN_CONSISTENT_APOS',
            'EN_SIMPLE_REPLACE',
            'REP_PASSIVE_VOICE',
            'REP_THANK_YOU_FOR'
        ]
        self.__filter_errors = filter_errors


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

        if self.__filter_errors:
            matches_dicts = self.filter_errors(matches_dicts)
        
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
            print(sentence)
            print()
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
    

    # Given a list of matches (dicts)
    # Return a list of matches with the category and ruleId filtered
    def filter_errors(self, matches: list):
        filtered_matches = [match for match in matches if match['category'] in self.__categories and match['ruleId'] not in self.__avoid_rule_ids]
        return filtered_matches
    

    # Close the language tool (for background .jar server)
    def close(self):
        self.__tool.close()
