from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
import torch
from transformers import BitsAndBytesConfig # For 4-bit or 8-bit quantization
import gc


# Importing the interface IChat from the chat_interface module within the app.llm package.
from .chat_interface import IChat

# List of model identifiers that are supported by this class.
supported_models = ["meta-llama/Meta-Llama-3-8B-Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct"]


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

        # Defines data type for tensors based on the availability of CUDA.
        torch_dtype = torch.float16

        # 4-bit quantization
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True, 
            bnb_4bit_use_double_quant=True, 
            bnb_4bit_compute_dtype=torch_dtype,
        )
        
        try:
            # Load tokenizer
            self.__tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side="left")

            # Load the quantized model with the quantization configuration
            self.__model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=quantization_config,
                device_map=self.__device, # "auto",  # Maps the model across the available GPUs automatically
            )
            self.__model_id = model_id

            # Verify the model loading and print some information
            print()
            print(f"Model loaded: {self.__model_id}")
            print(self.__model)

            # Test the model that the inference works (optional)
            #self.test_model()

        except Exception as e:
            print()
            print(f"Failed to load model '{model_id}': {e}")
            raise

    def test_model(self):
            # Test the model with a simple input
            print()
            print("Testing the model with a simple input:")
            prompt = [
                {"role": "system", "content": "You are a kind assistant."},
                {"role": "user", "content": "Hello, what are you?"}
            ] # system/user/assistant
            input_ids = self.__tokenizer.apply_chat_template(
                prompt,
                #add_special_tokens=False,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.__model.device)

            terminators = [
                self.__tokenizer.eos_token_id,
                self.__tokenizer.convert_tokens_to_ids("<|eot_id|>")
            ]

            outputs = self.__model.generate(
                input_ids,
                max_new_tokens=50,
                eos_token_id=terminators,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
                pad_token_id=self.__tokenizer.eos_token_id
            ).to(self.__model.device)

            # Generate response using the model.
            response = outputs[0][input_ids.shape[-1]:]
            # Decode the output tensors to text.
            response_text = self.__tokenizer.decode(response, skip_special_tokens=True)
            print(f"response_text: {response_text}")

            print()
            print("Model testing completed successfully.")


    def get_answer(self, message, max_new_tokens=150):
        """
        Generates a response from the model for the provided input content.
        Utilizes the loaded model and tokenizer to process and generate the response.
        """
        print("get_answer from LLAMA LLM started")
        start_time = time.time()

        # Encode the prompt to tensor, send to appropriate device.
        prompt = [
                #{"role": "system", "content": "You are a kind assistant."},
                {"role": "user", "content": message}
            ] # system/user/assistant
        input_ids = self.__tokenizer.apply_chat_template(
            prompt,
            #add_special_tokens=False,
            add_generation_prompt=True,
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

    def get_answer_batch(self, contents, max_new_tokens=150):
        """
        Generates a response from the model for the provided input content.
        Utilizes the loaded model and tokenizer to process and generate the response.
        """
        print(f"get_answers_batch from LLM LLAMA {self.__model_id} started")
        start_time = time.time()

        # Create prompts from user contents.
        chats = [{"role": "user", "content": content} for content in contents]
        prompts = [self.__tokenizer.apply_chat_template([chat], tokenize=False, add_generation_prompt=True) for chat in chats]

        # Encode all prompts in a single batch, send to appropriate device.
        self.__tokenizer.pad_token = self.__tokenizer.eos_token
        input_ids_batch = self.__tokenizer(prompts, add_special_tokens=False, return_tensors="pt", padding=True).input_ids.to(self.__device)

        terminators = [
            self.__tokenizer.eos_token_id,
            self.__tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        try:
            outputs = self.__model.generate(
                input_ids=input_ids_batch, 
                max_new_tokens=max_new_tokens, 
                eos_token_id=terminators, 
                pad_token_id=self.__tokenizer.eos_token_id,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
                )
        except Exception as e:
            print(f"Failed to generate responses: {e}")
            return ["I'm sorry, I'm having trouble generating a response right now."] * len(contents)

        # Decode the output tensors to text for each input.
        responses = [self.__tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"get_answers_batch from LLM finished. Time taken to get answers from LLM: {elapsed_time} seconds")
        
        #return [self.__clean_model_response(response) for response in responses]
        return responses

    def get_answer_json(self, message, json_format, max_new_tokens=150):
        """
        Generates a response from the model for the provided input content.
        Utilizes the loaded model and tokenizer to process and generate the response.
        """
        print("get_answer from LLAMA LLM started")
        start_time = time.time()

        # Encode the prompt to tensor, send to appropriate device.
        input_ids = self.__tokenizer.apply_chat_template(message,
                                                         add_generation_prompt=True,
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