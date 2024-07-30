import os
import time
import torch

from app.file_manager import FileManager
import app.explain_sentences as explain_sentences
from app.rag.RAGFactory import RAGFactory


input_directory = "./cache/explained_sentences"
output_directory = "./cache/rag_sentences"


def rag_sentences(file_manager, rag_engine, rag_passages=1, input_path="", output_path=""):
    if not os.path.isfile(input_path):
        print(f"{input_path} is not found.")
        print(f"Processing {input_path}")
        explain_sentences.main()
        
    explained_sentences = file_manager.read_from_json_file(input_path)

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


    file_manager.save_to_json_file(output_path, explained_sentences)

    return explained_sentences


def rag_sentences_of_directory(
        file_manager: FileManager,
        rag_engine: RAGFactory,
        rag_passages=5,
        explained_sentences_directory = "cache/explained_sentences", 
        rag_sentences_directory = "cache/rag_sentences", 
    ):
    # Loop through the files in the directory
    for explained_sentences_file in os.listdir(explained_sentences_directory):
        if explained_sentences_file[0] == ".":
            continue

        explained_sentences_path = os.path.join(explained_sentences_directory, explained_sentences_file)
        rag_sentences_path = os.path.join(rag_sentences_directory, explained_sentences_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(explained_sentences_path):
            print(f"Found diarized transcript file: {explained_sentences_path}")

            rag_sentences(
                file_manager,
                rag_engine,
                rag_passages, 
                explained_sentences_path, 
                rag_sentences_path)

def main():
    global input_directory, output_directory
    file_manager = FileManager()
    rag_engine = RAGFactory.get_instance("ragatouille")

    rag_sentences_of_directory(
        file_manager, 
        rag_engine, 
        rag_passages=5, 
        explained_sentences_directory=input_directory, 
        rag_sentences_directory=output_directory)
    
    # Clean GPU VRAM
    if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    