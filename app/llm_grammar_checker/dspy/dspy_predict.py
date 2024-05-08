import dspy

from app.llm_grammar_checker.dspy.dspy_signature import SignatureSEC


class PredictorSEC(dspy.Module):
    def __init__(self):
        super().__init__()
        self.module = dspy.Predict(SignatureSEC)

    def forward(self, original_sentence):
        # print("START-----------------------")
        # print("SEC-DSPy predictor starting - original_sentence: ", original_sentence)
        result = self.module(original_sentence=original_sentence)
        #print(result)
        # print("Corrected Sentence:", result['corrected_sentence'])
        # print("Explanation:", result['explanation'])
        # print("END-------------------------")
        return result
