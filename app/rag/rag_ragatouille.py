import os
from ragatouille import RAGPretrainedModel

from app.rag.rag_engine_interface import IRagEngine

index_name = 'tutor'
max_document_length = 300
split_documents = True


class RAGatouilleTutor(IRagEngine):
    def __init__(self, model_name="colbert-ir/colbertv2.0"):
        self.index_path = f".ragatouille/colbert/indexes/{index_name}/"
        self.INDEX = None
        self.__model_name = model_name

    def prepare_index(self, collection):
        if os.path.exists(self.index_path):
            print("Index ragatouille does exist. Skipping preparation index. "
                  "If you want to reindex, delete the folder .ragatoille/colbert/indexes/tutor")
            return

        print("Index ragatouille does not exist. Preparation index.")
        rag = RAGPretrainedModel.from_pretrained(self.__model_name)

        rag.index(
            collection=collection,
            index_name=index_name,
            max_document_length=max_document_length,
            split_documents=split_documents,
        )
        print("Index ragatouille preparation finished.")

    def search(self, query, k=5):
        if os.path.exists(self.index_path) is False:
            print("Index ragatouille does not exist.")
            return

        if self.INDEX is None:
            print(f"'RAGatouille INDEX' is None. Loading from index {self.index_path}.")
            self.INDEX = RAGPretrainedModel.from_index(self.index_path)

        if self.INDEX is not None:
            print(f"'RAGatouille' exists. Searching..")
            results = self.INDEX.search(query, k=k)

            output = [
                {
                    "rank": item["rank"],
                    "content": item["content"],
                }
                for item in results
            ]

            return output

    def get_index_path(self):
        return self.index_path
