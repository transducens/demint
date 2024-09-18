from app.llm.ChatFactory import ChatFactory

#from app.study_plan_creator import StudyPlanCreator


class EnglishTutor:
    def __init__(self, llm_model_name="gpt-4-turbo"):
        # LLM
        self.__llm_model_name = llm_model_name
        self.__chat_llm = None
        self.__chat_factory = ChatFactory()
        self.__chat_history = []


    def __get_chat_llm(self):
        if self.__chat_llm is None:
            self.__chat_llm = self.__chat_factory.get_instance(self.__llm_model_name)

        return self.__chat_llm
    
    def get_chat_llm(self):
        return self.__llm_model_name


    def get_current_llm_model_id(self):
        if self.__chat_llm is None:
            return None

        return self.__chat_llm.get_my_name()


    # ====================
    # = Chat LLM Region
    # ====================
    def set_chat_llm(self, llm_id):
        self.__llm_model_name = llm_id
        self.__chat_llm = None

    def get_answer(self, content, max_new_tokens=250):
        chat_llm = self.__get_chat_llm()
        return chat_llm.get_answer(content, max_new_tokens)

    @staticmethod
    def get_available_llm():
        return ChatFactory.get_supported_llm_ids()

    def update_chat_history(self, text):
        return self.__chat_history.extend(text)

    def get_chat_history(self):
        return self.__chat_history


