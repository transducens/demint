import language_tool_python as lt

import app.gec.language_tool.predict as lt
import app.gec.t5.predict as t5

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
    # Language Tool can run in public API mode or local mode (.jar server)
    _gec_models={
        "T5",
        "LT_API",
        "LT_SERVER"
    }

    def __init__(self, gec_model="T5"):
        self.__gec_model=gec_model
        if self.__gec_model=="LT_API":
            print("Using Language Tool API model to correct sentences", flush=True)
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif self.__gec_model=="LT_SERVER":
            print("Using Language Tool local server model to correct sentences", flush=True)
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif self.__gec_model=="T5":
            print("Using T5 model to correct sentences", flush=True)
            self.__tool = t5.T5_model()

    def correct_sentences(self, sentences):
        if self.__gec_model=="LT_API" or self.__gec_model=="LT_SERVER" or self.__gec_model=="T5":
            return self.__tool.correct_sentences(sentences)    

    def check(self, sentence):
        if(self.__gec_model=="LT_SERVER" or self.__gec_model=="LT_API"):
            return self.__tool.check(sentence)
            
    def sentence_to_quoted_list(self, sentences):
        result = []
        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue
            words[0] = f"'{words[0]}"
            words[-1] = f"{words[-1]}'"
            result.extend(words)

        return result


