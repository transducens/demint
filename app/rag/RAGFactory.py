from app.rag.content_extractor import ContentExtractor
from app.rag.rag_faiss import RagFAISS
from app.rag.rag_ragatouille import RAGatouilleTutor

part_count = 3
overlap = 0.1


class RAGFactory:
    _instances = {}
    _supported_types = {
        'faiss': RagFAISS,
        'ragatouille': RAGatouilleTutor,
    }

    @staticmethod
    def get_instance(rag_type):
        if rag_type not in RAGFactory._instances:
            if rag_type in RAGFactory._supported_types:
                instance = RAGFactory._supported_types[rag_type]()

                collection = []
                if rag_type == 'ragatouille':
                    collection = ContentExtractor.get_content()
                elif rag_type == 'faiss':
                    collection = ContentExtractor.get_content(part_count=part_count, overlap=overlap)

                instance.prepare_index(collection)

                RAGFactory._instances[rag_type] = instance
            else:
                raise ValueError(f"Unknown RAG type requested: {rag_type}")
        return RAGFactory._instances[rag_type]

    @staticmethod
    def get_supported_types():
        return list(RAGFactory._supported_types.keys())