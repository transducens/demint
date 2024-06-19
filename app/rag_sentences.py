import os
import time

from app.file_manager import FileManager
import app.explain_sentences as explain_sentences
from app.rag.RAGFactory import RAGFactory


input_file = "./cache/explained_sentences.json"
output_file = "./cache/rag_sentences.json"


def rag_sentences(file_manager, rag_engine, rag_passages=1):
    if not os.path.isfile(input_file):
        print(f"{input_file} is not found.")
        print(f"Processing {input_file}")
        explain_sentences.main()
        
    explained_sentences = file_manager.read_from_json_file(input_file)

    for id in explained_sentences.keys():
        print("Processing sentence: ", id)
        errant_annotation_list = explained_sentences[id]['errant']

        for index_errant, errant_annotation in enumerate(errant_annotation_list):

            errant_llm_explained = errant_annotation['llm_explanation']
            errant_annotation['rag'] = []
        
            if rag_engine is not None:
                rag = rag_engine.search(errant_llm_explained, rag_passages)
            else:
                print("RAG engine is not available.")
                return None
            
            errant_annotation_list[index_errant]['rag'] = rag
    
        explained_sentences[id]['errant'] = errant_annotation_list


    file_manager.save_to_json_file(output_file, explained_sentences)

    return explained_sentences


def main():
    file_manager = FileManager()
    rag_engine = RAGFactory.get_instance("ragatouille")
    rag_sentences(file_manager, rag_engine, rag_passages=5)

if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")