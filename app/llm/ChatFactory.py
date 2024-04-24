from app.llm.gemma_chat import GemmaChat

gemma_family = GemmaChat.get_supported_models()


class ChatFactory:
    _supported_llm_types = {
         'gemma': GemmaChat,
        #'lamma': LlamaChat,
        #'chatGPT': OpenAIChat,
        #'phi': PhiChat,
    }

    @staticmethod
    def get_instance(llm_model_id):
        llm_type = None

        if llm_model_id in gemma_family:
            llm_type = 'gemma'

        if llm_type is None or llm_type not in ChatFactory._supported_llm_types:
            raise ValueError(f"Unknown LLM Model requested: {llm_model_id}")

        return ChatFactory._supported_llm_types[llm_type](llm_model_id)

    @staticmethod
    def get_supported_llm_types():
        return list(ChatFactory._supported_llm_types.keys())

    @staticmethod
    def get_supported_llm_ids():
        llm_ids = []
        for chat in ChatFactory._supported_llm_types.values():
            llm_ids.extend(chat.get_supported_models())
        return llm_ids
