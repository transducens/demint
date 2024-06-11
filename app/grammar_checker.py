import language_tool_python as lt
from app.gec.gector_large import predict as gl
import gec.language_tool.predict as lt

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
        "GECTOR_2024",
        "LT_API",
        "LT_SERVER"
    }

    def __init__(self, gec_model="GECTOR_2024"):
        if gec_model=="LT_API":
            print("Using language tool public API.")
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif gec_model=="LT_SERVER":
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif gec_model=="GECTOR_2024":
            print("Using GECToR-2024")
            self.__tool = gl

    def correct_sentences(self, sentences):
        self.__tool.correct_sentences(sentences)

