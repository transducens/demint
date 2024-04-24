from abc import ABC, abstractmethod


class IChat(ABC):
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
