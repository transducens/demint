from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import time

from app.llm.chat_interface import IChat

supported_models = ["microsoft/Phi-3-mini-4k-instruct"]


class PhiChat(IChat):
    """
    A chat class for interacting with a conversational language model.

    Attributes:
        __tokenizer (AutoTokenizer): The tokenizer for the specified model.
        __pipe (pipeline): The pipeline for text generation using the causal language model.
    """

    def __init__(self, model_id="microsoft/Phi-3-mini-4k-instruct"):
        """
        Initializes the Chat class with a specified conversational model.

        Args:
            model_id (str): Identifier for the model to load.
        """
        super().__init__(model_id)
        self.__device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Device detected: ", self.__device)

        self.__tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.__model = AutoModelForCausalLM.from_pretrained(model_id,
                                                            device_map=self.__device,
                                                            torch_dtype="auto",
                                                            trust_remote_code=True)
        self.__pipe = pipeline("text-generation",
                               model=self.__model,
                               tokenizer=self.__tokenizer)

    def __clean_model_response(self, response_text):
        """
        Processes the raw response text from the model, removing unnecessary tokens that signify turns or sequence ends,
        making the response more suitable for human reading.
        """
        # Predefined tokens used to indicate the beginning and end of the model's turn.
        start_token = "<|assistant|>"
        end_tokens = ["<|end|>"]

        # Remove the start token from the response if present.
        start_index = response_text.find(start_token)
        if start_index != -1:
            response_text = response_text[start_index + len(start_token):]

        # Remove any end tokens from the response if present.
        for token in end_tokens:
            end_index = response_text.find(token)
            if end_index != -1:
                response_text = response_text[:end_index].strip()

        return response_text

    def get_answer(self, content, max_new_tokens=500):
        """
        Generates a response to the input content using the loaded model.

        Args:
            content: user query
            max_new_tokens (int): The maximum number of new tokens to generate (default is 500).

        Returns:
            str: The generated response text.
        """
        print("get_answer from LLM started")
        start_time = time.time()

        prompt = [
            {"role": "system",
             "content": "You are a helpful English Tutor. "
                        "Please provide safe, ethical and accurate information to the user."},
            {"role": "user", "content": content},
        ]

        generation_args = {
            "max_new_tokens": max_new_tokens,
            "return_full_text": False,
            "temperature": 0.0,
            "do_sample": False
        }

        response = self.__pipe(prompt, **generation_args)
        response_text = self.__clean_model_response(response[0]['generated_text'])

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answer from LLM finished. Time taken to get answer from LLM: {elapsed_time} seconds")
        return response_text

    def get_my_name(self):
        """
        Returns the model identifier.
        """
        return self.__model_id

    @staticmethod
    def get_supported_models():
        """
        Returns the list of supported models for the PhiChat class.

        Returns:
            list: A list of supported model identifiers.
        """
        return supported_models
