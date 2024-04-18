from sentence_transformers import SentenceTransformer
import faiss
import os

from app.rag.rag_engine_interface import IRagEngine


class RagFAISS(IRagEngine):
    def __init__(self, model_name='avsolatorio/GIST-small-Embedding-v0'):
        # Initialize the SentenceTransformer model on creation of a RagFAISS instance
        self.__index_file = 'cache/faiss_index.bin'
        self.__modelST = SentenceTransformer(model_name)
        self.__indexFlatIP = None  # Placeholder for the FAISS index
        self.__text = []  # Placeholder for the paragraphs extracted from the PDF
        self.__normalize = False  # Flag to indicate whether to normalize embeddings

    def __create_faiss_index(self, paragraphs, normalize=False):
        """
        Create a FAISS index using embeddings from the provided paragraphs.

        Args:
            paragraphs (list): A list of paragraphs to index.
            normalize (bool): Whether to normalize the embeddings.
        """
        self.__normalize = normalize
        self.__text = paragraphs
        embeddings = self.__modelST.encode(self.__text, show_progress_bar=True)

        # Normalize embeddings if required
        if self.__normalize:
            faiss.normalize_L2(embeddings)

        # Initialize and populate the FAISS index
        d = embeddings.shape[1]  # Dimensionality of embeddings
        self.__indexFlatIP = faiss.IndexFlatIP(d)
        self.__indexFlatIP.add(embeddings)

    def prepare_index(self, paragraphs):
        """
        Load a FAISS index from a file if it exists, or create one using embeddings
        from the provided paragraphs.

        Args:
            paragraphs (list): A list of paragraphs to index.
            normalize (bool): Whether to normalize the embeddings.
        """
        if os.path.exists(self.__index_file):
            # Load the FAISS index from the file
            self.__indexFlatIP = faiss.read_index(self.__index_file)
            self.__text = paragraphs
            print("FAISS index loaded from file." +
                  f"If you want to create a new index, please delete {self.__index_file}.")
        else:
            # Create the FAISS index and save it to the file
            self.__create_faiss_index(paragraphs, False)
            faiss.write_index(self.__indexFlatIP, self.__index_file)
            print(f"FAISS index created and saved to {self.__index_file}.")

    def search(self, query, k=5):
        """
        Search the FAISS index for the k most similar paragraphs to the query.

        Args:
            query (str): The query string.
            k (int): The number of results to return.

        Returns:
            tuple: Cosine similarities, indices of nearest neighbors, and the paragraphs corresponding to those indices.
        """
        # Encode the query and prepare it for FAISS search
        query_embedding = self.__modelST.encode(query)
        xq = query_embedding.reshape(1, -1)
        if self.__normalize:
            faiss.normalize_L2(xq)

        # Perform the search on the index
        D, I = self.__indexFlatIP.search(xq, k)  # D - cosine similarities, I - indices of nearest neighbors
        RAG_context = [self.__text[idx] for idx in I[0]]

        output = [
            {
                "content": item,
            }
            for item in RAG_context
        ]
        
        return output
