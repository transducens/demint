from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
from transformers import BitsAndBytesConfig # For 4-bit or 8-bit quantization
import gc
import concurrent.futures

# Importing the interface IChat from the chat_interface module within the app.llm package.
from .chat_interface import IChat

# List of model identifiers that are supported by this class.
supported_models = ["google/gemma-1.1-2b-it", "google/gemma-1.1-7b-it"]


class GemmaChat(IChat):
    """
    A class for interacting with a conversational language model, inheriting from IChat interface.
    It handles model loading, input processing, and response generation.
    """

    def __init__(self, model_id="google/gemma-1.1-2b-it"):
        """
        Initializes the GemmaChat class with a model specified by its ID. The default model is "google/gemma-1.1-2b-it".
        Raises an exception if an unsupported model ID is provided.
        """
        # Validates if the provided model ID is supported, raises ValueError if not.
        super().__init__(model_id)

        # Setup device for model computations (GPU if available, otherwise CPU).
        self.__device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Device detected: ", self.__device)

        # Defines data type for tensors based on the availability of CUDA.
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        # 4-bit quantization
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True, 
            bnb_4bit_use_double_quant=True, 
            bnb_4bit_compute_type=torch_dtype,
            llm_int8_enable_fp16_cpu_offload=True)

        # Loading the LLM
        try: 
            self.__tokenizer = AutoTokenizer.from_pretrained(model_id)
            if torch.cuda.is_available():
                self.__model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    device_map=self.__device,
                    #attn_implementation="flash_attention_2",
                    quantization_config=quantization_config
                )
            else:
                self.__model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    device_map=self.__device,
                    torch_dtype=torch_dtype)
            
            self.__model_id = model_id
            print(f"Model loaded: {model_id}")
        except Exception as e:
            print(f"Failed to load model '{model_id}': {e}")
            raise


    def __clean_model_response(self, response_text):
        """
        Processes the raw response text from the model, removing unnecessary tokens that signify turns or sequence ends,
        making the response more suitable for human reading.
        """
        # Predefined tokens used to indicate the beginning and end of the model's turn.
        start_token = "<start_of_turn>model"
        end_tokens = ["<end_of_turn>", "<eos>"]

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

    def get_answer(self, content, max_new_tokens=150):
        """
        Generates a response from the model for the provided input content.
        Utilizes the loaded model and tokenizer to process and generate the response.
        """
        print(f"get_answer from LLM GEMMA {self.__model_id} started")
        start_time = time.time()

        # Create the prompt from user content.
        chat = [{"role": "user", "content": content}]
        prompt = self.__tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)

        # Encode the prompt to tensor, send to appropriate device.
        input_ids = self.__tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to(self.__device)

        try:
            outputs = self.__model.generate(input_ids=input_ids, max_new_tokens=max_new_tokens)
        except Exception as e:
            print(f"Failed to generate response: {e}")
            return "I'm sorry, I'm having trouble generating a response right now."


        # Decode the output tensors to text.
        response_text = self.__tokenizer.decode(outputs[0])
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answer from LLM finished. Time taken to get answer from LLM: {elapsed_time} seconds")
        return self.__clean_model_response(response_text)
    
    # Deprecated method
    def get_answer_threads(self, contents, max_new_tokens=150):
        """
        Generates responses from the model for the provided input contents.
        Utilizes the loaded model and tokenizer to process and generate the responses.
        """
        print(f"get_answer for {len(contents)} petitions from LLM GEMMA {self.__model_id} started")
        start_time = time.time()
        def generate_response(content):
            """
            Helper function to generate a single response.
            """

            # Create the prompt from user content.
            chat = [{"role": "user", "content": content}]
            prompt = self.__tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)

            # Encode the prompt to tensor, send to appropriate device.
            input_ids = self.__tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to(self.__device)

            try:
                outputs = self.__model.generate(input_ids=input_ids, max_new_tokens=max_new_tokens)
            except Exception as e:
                print(f"Failed to generate response: {e}")
                return "I'm sorry, I'm having trouble generating a response right now."

            # Decode the output tensors to text.
            response_text = self.__tokenizer.decode(outputs[0])
            return self.__clean_model_response(response_text)

        # Use ThreadPoolExecutor to process contents in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map the generate_response function to each content
            results = list(executor.map(generate_response, contents))

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answer for {len(contents)} petitions from LLM finished. Time taken to get answer from LLM: {elapsed_time} seconds")

        return results

    def get_answer_batch(self, contents, max_new_tokens=150):
        """
        Generates responses from the model for the provided input contents in a batch.
        Utilizes the loaded model and tokenizer to process and generate the responses.
        """
        print(f"get_answers from LLM GEMMA {self.__model_id} started")
        start_time = time.time()

        # Create prompts from user contents.
        chats = [{"role": "user", "content": content} for content in contents]
        prompts = [self.__tokenizer.apply_chat_template([chat], tokenize=False, add_generation_prompt=True) for chat in chats]

        # Encode all prompts in a single batch, send to appropriate device.
        input_ids_batch = self.__tokenizer(prompts, add_special_tokens=False, return_tensors="pt", padding=True).input_ids.to(self.__device)

        try:
            outputs = self.__model.generate(input_ids=input_ids_batch, max_new_tokens=max_new_tokens)
        except Exception as e:
            print(f"Failed to generate responses: {e}")
            return ["I'm sorry, I'm having trouble generating a response right now."] * len(contents)

        # Decode the output tensors to text for each input.
        responses = [self.__tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answers from LLM finished. Time taken to get answers from LLM: {elapsed_time} seconds")
        
        return [self.__clean_model_response(response) for response in responses]

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

    def unload_model(self):
        """Unload the model to free up GPU VRAM."""
        if self.__model:
            del self.__model
            self.__model = None
        
        if self.__tokenizer:
            del self.__tokenizer
            self.__tokenizer = None
        
        # Free up any remaining memory
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("Model unloaded and GPU memory freed.")