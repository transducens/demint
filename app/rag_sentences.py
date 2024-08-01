import os
import time
import argparse

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


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-xf", "--explained_file", type=str, help="Path to where the input explained sentences file is located.")
    parser.add_argument("-rf", "--rag_file", type=str, help="Path to where the output rag sentences file will be saved.")
    parser.add_argument("-xd", "--explained_directory", type=str, help="Path to the directory containing the input explained sentences files.")
    parser.add_argument("-rd", "--rag_directory", type=str, help="Path to the directory where the output rag sentences files will be saved.")

    return parser.parse_args()


def main():
    global input_directory, output_directory
    explained_directory = input_directory
    rag_directory = output_directory
    file_manager = FileManager()
    rag_engine = RAGFactory.get_instance("ragatouille")
    rag_passages = 5
    args = get_args()

    if args.explained_file:
        if args.explained_directory:
            raise ValueError("Error: Please provide either an explained sentences file or an explained sentences directory.")
        elif args.rag_file:
            rag_sentences(file_manager, rag_engine, rag_passages, args.explained_file, args.rag_file)
        elif args.rag_directory:
            explained_file = os.path.basename(args.explained_file)
            transcript_name, transcript_extension = os.path.splitext(explained_file)
            rag_sentences(file_manager, rag_engine, rag_passages, args.explained_file, os.path.join(args.rag_directory, transcript_name + ".json"))
        else:
            explained_file = os.path.basename(args.explained_file)
            transcript_name, transcript_extension = os.path.splitext(explained_file)
            rag_sentences(file_manager, rag_engine, rag_passages, args.explained_file, os.path.join(rag_directory, transcript_name + ".json"))

    elif args.explained_directory:
        if args.rag_directory:
            rag_sentences_of_directory(file_manager, rag_engine, rag_passages, args.explained_directory, args.rag_directory)
        elif args.rag_file:
            raise ValueError("Error: Please provide a directory to save the explained sentences files.")
        else:
            rag_sentences_of_directory(file_manager, rag_engine, rag_passages, args.explained_directory, rag_directory)
        
    elif args.rag_file or args.rag_directory:
        raise ValueError("Error: Please provide a transcript file or a transcript directory.")

    else:
        rag_sentences_of_directory(file_manager, rag_engine, rag_passages, explained_directory, rag_directory)



if "__main__" == __name__:
    main()