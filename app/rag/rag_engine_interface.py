from abc import ABC, abstractmethod


class IRagEngine(ABC):
    @abstractmethod
    def prepare_index(self, collection):
        pass

    @abstractmethod
    def search(self, query, k=5):
        pass
