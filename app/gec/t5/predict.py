from happytransformer import HappyTextToText, TTSettings
                            

class T5_model:
    def __init__(self) -> None:
        self.__model = HappyTextToText("T5", "vennify/t5-base-grammar-correction")

    # Given a list of sentences (strings)
    # Return a list of corrected sentences (strings)
    def correct_sentences(self, sentences):
        args = TTSettings(num_beams=5, min_length=1)
        result = [self.__model.generate_text(f"grammar: {s}", args=args).text for s in sentences]
        return result


def main():
    sentences = ["I likes my cow so many , that I would give my laif for it .", "i lovely biskuits"]
    predicted_sentences = T5_model().correct_sentences(sentences)
    print(predicted_sentences)

if __name__ == "__main__":
    main()

