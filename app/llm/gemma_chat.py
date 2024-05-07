from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
from transformers import BitsAndBytesConfig # For 4-bit or 8-bit quantization


from app.llm.chat_interface import IChat

supported_models = ["google/gemma-1.1-2b-it", "google/gemma-1.1-7b-it"]


class GemmaChat(IChat):
    """
    A chat class for interacting with a conversational language model.

    Attributes:
        __tokenizer (AutoTokenizer): The tokenizer for the specified model.
        __model (AutoModelForCausalLM): The causal language model for generating responses.
    """

    def __init__(self, model_id="google/gemma-1.1-2b-it"):
        """
        Initializes the Chat class with a specified conversational model.

        Args:
            model_id (str): Identifier for the model to load (default is "google/gemma-1.1-2b-it").
        """
        if model_id not in supported_models:
            raise ValueError(
                f"model_id '{model_id}' is not supported. Please use one of the following: {', '.join(supported_models)}")

        self.__device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Device detected: ", self.__device)

        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        # 4-bit quantization
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True, 
            bnb_4bit_use_double_quant=True, 
            bnb_4bit_compute_dtype=torch_dtype)

        # Loading the LLM
        try: 
            self.__tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.__model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map=self.__device,
                quantization_config=quantization_config)
            self.__model_id = model_id
            print(f"Model loaded: {model_id}")
        except Exception as e:
            print(f"Failed to load model '{model_id}': {e.message}")
            raise

    def __clean_model_response(self, response_text):
        """
        Cleans the model's response by removing predefined tokens that indicate the start of the model's turn and
        any service tokens indicating the end of a turn or end of sequence. This makes the response more human-readable.

        Args:
            response_text (str): The raw response text from the model.

        Returns:
            str: The cleaned response text, ready for presentation to the user.
        """
        start_token = "<start_of_turn>model"
        end_tokens = ["<end_of_turn>", "<eos>"]

        start_index = response_text.find(start_token)
        if start_index != -1:
            response_text = response_text[start_index + len(start_token):]

        for token in end_tokens:
            end_index = response_text.find(token)
            if end_index != -1:
                response_text = response_text[:end_index].strip()

        return response_text

    def get_answer(self, content, max_new_tokens=150):
        """
        Generates a response to the input content using the loaded model.

        Args:
            content (str): The input text content to generate a response to.
            max_new_tokens (int): The maximum number of new tokens to generate (default is 150).

        Returns:
            str: The generated response text.
        """
        print("get_answer from LLM started")
        start_time = time.time()

        chat = [{"role": "user", "content": content}]
        prompt = self.__tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)

        input_ids = self.__tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to(self.__device)

        try:
            outputs = self.__model.generate(input_ids=input_ids, max_new_tokens=max_new_tokens)
        except Exception as e:
            print(f"Failed to generate response: {e}")
            return "I'm sorry, I'm having trouble generating a response right now."


        response_text = self.__tokenizer.decode(outputs[0])
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answer from LLM finished. Time taken to get answer from LLM: {elapsed_time} seconds")
        return self.__clean_model_response(response_text)

    def get_my_name(self):
        return self.__model_id

    @staticmethod
    def get_supported_models():
        """
        Returns the list of supported models for the GemmaChat class.

        Returns:
            list: A list of supported model identifiers.
        """
        return supported_models

