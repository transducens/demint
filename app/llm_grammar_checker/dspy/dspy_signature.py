import dspy

class SignatureSEC(dspy.Signature):
    """
    Correct grammatical or punctuation errors in sentences if there are ones and provide explanations for the corrections.
    """
    original_sentence = dspy.InputField(desc="The original sentence that contains errors.")
    corrected_sentence = dspy.OutputField(
        desc="Corrected version of the original sentence, free of errors.")
    explanation = dspy.OutputField(desc="Short explanation of the correction, typically between 10 and 15 words, "
                                        "explaining the error and its correction.")