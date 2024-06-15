from .chat_interface import IChat
from openai import OpenAI

supported_models = ["gpt-3.5-turbo-0125", "gpt-4o-2024-05-13", "gpt-4-turbo"]

class OpenAIChat(IChat):
    def __init__(self, model_id="gpt-3.5-turbo"):
        """
        Initializes the GemmaChat class with a model specified by its ID. The default model is "meta-llama/Meta-Llama-3-8B-Instruct".
        Raises an exception if an unsupported model ID is provided.
        """
        # Validates if the provided model ID is supported, raises ValueError if not.
        super().__init__(model_id)
        self.__openai = OpenAI()

    def get_answer(self, content, max_new_tokens=50):
        response = self.__openai .chat.completions.create(
            model=self.get_model_id(),
            messages=[
                {"role": "user", "content": content}
            ],
            max_tokens=max_new_tokens
        )

        return response.choices[0].message.content

    @staticmethod
    def get_supported_models():
        return supported_models

    def get_my_name(self):
        return self.get_model_id()