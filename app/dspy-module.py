import os
import dspy
import dsp
from dspy.evaluate import Evaluate
from dspy.teleprompt import BootstrapFewShot, BootstrapFewShotWithRandomSearch, BootstrapFinetune


llama = dspy.OllamaLocal(model='llama3')
dspy.settings.configure(lm=llama)


def corrected_sentence_exact_match(example, pred, trace=None):
    print(dsp.answer_match(pred.corrected_sentence, [example.corrected_sentence], frac=0.8))
    return dsp.answer_match(pred.corrected_sentence, [example.corrected_sentence], frac=0.8)


class SignatureSEC(dspy.Signature):
    """
    Correct grammatical errors in sentences and provide explanations for the corrections.

    This signature defines a model where:
    - The input is an original sentence with a grammatical error.
    - The output is a corrected sentence without the grammatical error.
    - A short explanation describes why the original sentence was incorrect and why the correction is necessary.
    """
    original_sentence = dspy.InputField(desc="The original sentence that contains grammatical errors.")
    corrected_sentence = dspy.OutputField(
        desc="Corrected version of the original sentence, free of grammatical errors.")
    explanation = dspy.OutputField(desc="Short explanation of the correction, typically between 10 and 15 words, "
                                        "explaining the grammatical error and its correction.")


# SEC (Sentence Error Correction)
class SEC(dspy.Module):  # let's define a new module
    def __init__(self):
        super().__init__()
        # here we declare the chain of thought submodule, so we can later compile it (e.g., teach it a prompt)
        self.module = dspy.Predict(SignatureSEC)

    def forward(self, original_sentence):
        return self.module(original_sentence=original_sentence)


class DSPYModule:
    def __init__(self):
        self.predictorSEC = SEC()

        if not os.path.exists('/dspy/SEC.json'):
            self.__compile()

        self.predictorSEC.load('/dspy/SEC.json')

    def __compile(self):
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
        optimizer = BootstrapFewShotWithRandomSearch(metric=corrected_sentence_exact_match, **config)
        sec_compiled = optimizer.compile(SEC(), trainset=train)
        sec_compiled.save('/dspy/SEC.json')

    def predict(self, original_sentence: str):
        print(f"original_sentence: {original_sentence}")
        return self.predictorSEC(original_sentence=original_sentence)


dspyModule = DSPYModule()
sample_sentence = "She don't know what to do next."
result = dspyModule.predict(original_sentence=sample_sentence)

print("Original Sentence:", sample_sentence)
print("-----------------------")
print("Corrected Sentence:", result['corrected_sentence'])
print("-----------------------")
print("Explanation:", result['explanation'])
