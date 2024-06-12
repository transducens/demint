from app.rag.content_extractor import ContentExtractor
#from rag_faiss import RagFAISS
from app.rag.rag_ragatouille import RAGatouilleTutor

part_count = 400
overlap = 0.25


class RAGFactory:
    _instances = {}
    _supported_types = {
        #'faiss': RagFAISS,
        'ragatouille': RAGatouilleTutor,
    }

    @staticmethod
    def get_instance(rag_type):
        if rag_type not in RAGFactory._instances:
            if rag_type in RAGFactory._supported_types:
                instance = RAGFactory._supported_types[rag_type]()

                collection = []
                collection = ContentExtractor.get_content()
                #if rag_type == 'ragatouille':
                #    collection = ContentExtractor.get_content()
                #elif rag_type == 'faiss':
                #    collection = ContentExtractor.get_content(part_count=part_count, overlap=overlap)

                print("Preparing index...")
                instance.prepare_index(collection)
                print("Index prepared...")

                RAGFactory._instances[rag_type] = instance
            else:
                raise ValueError(f"Unknown RAG type requested: {rag_type}")
        return RAGFactory._instances[rag_type]

    @staticmethod
    def get_supported_types():
        return list(RAGFactory._supported_types.keys())
    
if __name__ == '__main__':
    factory = RAGFactory()
    rag_engine = factory.get_instance("ragatouille")
    result = rag_engine.search("present perfect", 5)
    print(result)
