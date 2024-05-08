from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
from accelerate import disk_offload

# Importing the interface IChat from the chat_interface module within the app.llm package.
from app.llm.chat_interface import IChat

# List of model identifiers that are supported by this class.
supported_models = ["meta-llama/Meta-Llama-3-8B-Instruct"]


class LLamaChat(IChat):
    """
    A class for interacting with a conversational language model, inheriting from IChat interface.
    It handles model loading, input processing, and response generation.
    """

    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct"):
        """
        Initializes the GemmaChat class with a model specified by its ID. The default model is "meta-llama/Meta-Llama-3-8B-Instruct".
        Raises an exception if an unsupported model ID is provided.
        """
        # Validates if the provided model ID is supported, raises ValueError if not.
        super().__init__(model_id)

        # Setup device for model computations (GPU if available, otherwise CPU).
        self.__device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Device detected: ", self.__device)

        # Load tokenizer and model using the specified model ID, adjusting for the computed torch_dtype.
        self.__tokenizer = AutoTokenizer.from_pretrained(model_id)

        self.__model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True).to(self.__device)

    def get_answer(self, content, max_new_tokens=150, system_prompt="You are english teacher!"):
        """
        Generates a response from the model for the provided input content.
        Utilizes the loaded model and tokenizer to process and generate the response.
        """
        print("get_answer from LLM started")
        start_time = time.time()

        # Create the prompt from user content.
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]

        # Encode the prompt to tensor, send to appropriate device.
        input_ids = self.__tokenizer.apply_chat_template(messages,
                                                         add_special_tokens=False,
                                                         return_tensors="pt"
                                                         ).to(self.__model.device)

        terminators = [
            self.__tokenizer.eos_token_id,
            self.__tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        outputs = self.__model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=terminators,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            pad_token_id=self.__tokenizer.eos_token_id
        )

        # Generate response using the model.
        response = outputs[0][input_ids.shape[-1]:]
        # Decode the output tensors to text.
        response_text = self.__tokenizer.decode(response, skip_special_tokens=True)
        print(f"response_text: {response_text}")

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answer from LLM finished. Time taken to get answer from LLM: {elapsed_time} seconds")
        return response_text

    def get_my_name(self):
        """
        Returns the model identifier currently used by this GemmaChat instance.
        """
        return self.get_model_id()

    @staticmethod
    def get_supported_models():
        """
        Provides a list of model identifiers that are supported by the GemmaChat class.
        """
        return supported_models
