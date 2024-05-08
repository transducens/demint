import dspy


class SignatureSEC(dspy.Signature):
    """
    Correct grammatical errors in sentences and provide explanations for the corrections.
    """
    original_sentence = dspy.InputField(desc="The original sentence that contains grammatical errors.")
    corrected_sentence = dspy.OutputField(
        desc="Corrected version of the original sentence, free of grammatical errors.")
    explanation = dspy.OutputField(desc="Short explanation of the correction, typically between 10 and 15 words, "
                                        "explaining the grammatical error and its correction.")