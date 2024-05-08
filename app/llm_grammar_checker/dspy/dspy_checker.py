import os
import dspy
import dsp
from dspy.evaluate import Evaluate
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

from app.llm_grammar_checker.dspy.dspy_predict import PredictorSEC

#llama = dspy.OllamaLocal(model='llama3')

llama = dspy.HFClientTGI(model="google/gemma-1.1-2b-it", port=8083, url="http://localhost")
dspy.settings.configure(lm=llama)

compile_turn_on = True
compile_file_name = 'SECPredictor.json'


def corrected_sentence_match(example, pred, trace=None):
    # print(f"Start====================")
    # print(pred)
    # print(f"example.corrected_sentence:{example.corrected_sentence}")
    # print(f"pred.corrected_sentence:{pred['corrected_sentence']}")
    # print(dsp.answer_match(pred['corrected_sentence'], [example.corrected_sentence], frac=0.8))
    # print(f"End====================")
    return (dsp.answer_match(pred['corrected_sentence'], [example.explanation], frac=0.8) and
            dsp.answer_match(pred['explanation'], [example.explanation], frac=0.8))


# SEC (Sentence Error Correction)
class DSPYModule:
    def __init__(self):
        self.predictorSEC = PredictorSEC()

        if os.path.exists(compile_file_name):
            self.predictorSEC.load(compile_file_name)

    def compile(self):
        train_sentences = [
            ("She don't know what to do next.", "She doesn't know what to do next.",
             "The original sentence used 'don't' with a singular subject, which is incorrect. The correct verb form for the third person singular is 'doesn't'."),
            ("The team is needing a new coach for the next season.", "The team needs a new coach for the next season.",
             "The original sentence used 'is needing', which is not standard because 'need' typically does not use the continuous form. 'Needs' is the correct form here."),
            ("She suggested that he goes to the doctor.", "She suggested that he go to the doctor.",
             "The original sentence used 'goes' after 'suggested that', which should be followed by the subjunctive mood 'go' instead of 'goes'."),
            ("Me and him went to the market yesterday.", "He and I went to the market yesterday.",
             "The original sentence incorrectly used 'Me and him' as the subject. The correct form is 'He and I' to serve as the grammatical subjects."),
            ("There's many solutions to this problem.", "There are many solutions to this problem.",
             "The original sentence used 'There's' (there is) with a plural noun 'solutions'. The correct form is 'There are' to agree with the plural noun."),
            ("The scientific community continues to make significant advancements.",
             "The scientific community continues to make significant advancements.",
             "No errors were found in this sentence."),
            ("Cultural diversity enriches our society in many ways.",
             "Cultural diversity enriches our society in many ways.", "No errors were found in this sentence."),
            ("Renewable energy sources are essential for sustainable development.",
             "Renewable energy sources are essential for sustainable development.",
             "No errors were found in this sentence.")
        ]

        train = [
            dspy.Example(
                original_sentence=original_sentence,
                corrected_sentence=corrected_sentence,
                explanation=explanation
            ).with_inputs('original_sentence') for original_sentence, corrected_sentence, explanation in train_sentences
        ]

        config = dict(num_candidate_programs=1, num_threads=1)
        optimizer = BootstrapFewShotWithRandomSearch(metric=corrected_sentence_match, **config)
        sec_compiled = optimizer.compile(PredictorSEC(), trainset=train)
        sec_compiled.save(compile_file_name)


    def evaluate(self):
        print("Evaluating the model on the development set STARTED")
        dev_sentences = [
            ("He have been working here for three years.", "He has been working here for three years.",
             "The original sentence incorrectly used 'have' with a singular subject 'He'. The correct form is 'has' for third person singular."),
            ("We was happy to see them.", "We were happy to see them.",
             "The original sentence used 'was' with the plural subject 'We'. The correct form is 'were' for plural subjects."),
            ("You eats too much candy.", "You eat too much candy.",
             "The original sentence incorrectly used 'eats' with the pronoun 'You'. The correct form is 'eat' for second person."),
            ("This dogs are very friendly.", "These dogs are very friendly.",
             "The original sentence used 'This' with a plural noun 'dogs'. The correct demonstrative pronoun for plural nouns is 'These'."),
            ("She do not like to read books.", "She does not like to read books.",
             "The original sentence used 'do not' with a singular subject 'She'. The correct form is 'does not' for third person singular.")
        ]

        dev = [
            dspy.Example(
                original_sentence=original_sentence,
                corrected_sentence=corrected_sentence,
                explanation=explanation
            ).with_inputs('original_sentence') for original_sentence, corrected_sentence, explanation in dev_sentences
        ]

        NUM_THREADS = 4
        evaluate_hotpot = Evaluate(devset=dev, metric=corrected_sentence_match, num_threads=NUM_THREADS,
                                   display_progress=True, display_table=15)
        evaluate_hotpot(self.predictorSEC)
        print("Evaluating the model on the development set FINISHED")



    def predict(self, original_sentence: str):
        return self.predictorSEC(original_sentence=original_sentence)



dspyModule = DSPYModule()
sample_sentence = "He have been working here for three years."
result = dspyModule.predict(original_sentence=sample_sentence)

print("BEFORE compile")
print("Original Sentence:", sample_sentence)
print("-----------------------")
print("Corrected Sentence:", result['corrected_sentence'])
print("-----------------------")
print("Explanation:", result['explanation'])

dspyModule.compile()

sample_sentence = "She do not like to read books."
result = dspyModule.predict(original_sentence=sample_sentence)

print("AFTER compile")
print("Original Sentence:", sample_sentence)
print("-----------------------")
print("Corrected Sentence:", result['corrected_sentence'])
print("-----------------------")
print("Explanation:", result['explanation'])