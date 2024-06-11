import language_tool_python as lt
import gec.language_tool.predict as lt
import gec.t5.predict as t5
import subprocess

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
        "GECTOR_2024",
        "LT_API",
        "LT_SERVER"
    }

    def __init__(self, gec_model="GECTOR_2024"):
        self.__gec_model=gec_model
        if gec_model=="LT_API":
            print("Using language tool public API.")
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif self.__gec_model=="LT_SERVER":
            self.__tool = lt.LT_Checker(gec_model=gec_model)
        elif self.__gec_model=="T5":
            print("Using T5")
            self.__tool = t5.T5_model()

    def correct_sentences(self, sentences):
        if self.__gec_model=="LT_API" or self.__gec_model=="LT_SERVER" or self.__gec_model=="T5":
            return self.__tool.correct_sentences(sentences)    
        
        elif self.__gec_model=="GECTOR_2024":
            print("We in")
            command = [
                "conda", "run", "-n", "gector_env",
                "python", "app/gec/gector_large/predict.py",
                "'I", "likes", "my", "cowes'",
                "'He", "do", "like", "cofe'"
            ]   #.extend(sentences)
            print(f"Command: {command}")
            result = subprocess.run(command, capture_output=True, text=True)
            print(result.stdout)
            


if __name__ == "__main__":
    tool = GrammarChecker("GECTOR_2024")
    tool.correct_sentences(["I likes my cowes", "He do like cofe"])

