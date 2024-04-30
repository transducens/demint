from abc import ABC, abstractmethod


class IChat(ABC):
    def __init__(self, model_id):
        if model_id not in self.get_supported_models():
            raise ValueError(
                f"model_id '{model_id}' is not supported. Please use one of the following: {', '.join(self.get_supported_models())}")

        self.__model_id = model_id
        print(f"Model loaded: {model_id}")

    @abstractmethod
    def get_answer(self, content, max_new_tokens=150):
        pass

    @staticmethod
    @abstractmethod
    def get_supported_models():
        pass

    @abstractmethod
    def get_my_name(self):
        pass

    def get_model_id(self):
        return self.__model_id
