from .gemma_chat import GemmaChat
from .llama_chat import LLamaChat
from .phi_chat import PhiChat

# Retrieve a list of all supported models
gemma_family = GemmaChat.get_supported_models()
phi_family = PhiChat.get_supported_models()
llama_family = LLamaChat.get_supported_models()


class ChatFactory:
    # A dictionary to store supported types of language model chats.
    # Currently only 'gemma' is active, others are commented out.
    _supported_llm_types = {
         'gemma': GemmaChat,
         'phi': PhiChat,
         'llama': LLamaChat,
        # 'chatGPT': OpenAIChat,
    }

    # Static method to create an instance of a language model chat based on a given model ID.
    @staticmethod
    def get_instance(llm_model_id):

        # If the model type is not determined or is not in the supported list, raise an error.
        if llm_model_id not in ChatFactory.get_supported_llm_ids():
            raise ValueError(f"Unknown LLM Model requested: {llm_model_id}")

        llm_type = None  # Initializes the variable to store the type of the model.

        # Check if the model ID provided is in the list of supported GemmaChat models.
        if llm_model_id in gemma_family:
            llm_type = 'gemma'  # Set the type to 'gemma' if found.

        # Check if the model ID provided is in the list of supported PhiChat models.
        if llm_model_id in phi_family:
            llm_type = 'phi'  # Set the type to 'phi' if found.

        if llm_model_id in llama_family:
            llm_type = 'llama'  # Set the type to 'phi' if found.

        # Create and return an instance of the chat model using the determined llm_type.
        return ChatFactory._supported_llm_types[llm_type](llm_model_id)

    # Static method to get a list of all supported LLM types.
    @staticmethod
    def get_supported_llm_types():
        return list(ChatFactory._supported_llm_types.keys())

    # Static method to get a combined list of all supported model IDs from all chat classes.
    @staticmethod
    def get_supported_llm_ids():
        llm_ids = []  # Initializes the list to store all supported model IDs.
        # Iterates over each chat class in the supported list.
        for chat in ChatFactory._supported_llm_types.values():
            # Extends the llm_ids list with the supported models of the current chat class.
            llm_ids.extend(chat.get_supported_models())

        print(llm_ids)
        return llm_ids  # Returns the list of all supported model IDs.
