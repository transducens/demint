# Thirdy party imports
import errant
from sentence_splitter import SentenceSplitter
import os
import argparse

from app.file_manager import FileManager


input_directory = "./cache/diarized_transcripts"
output_directory = "./cache/raw_sorted_sentence_collection"


def prepare_sorted_sentence_collection(file_manager, input_path, output_path):
    raw_sentence_collection = {}
    index = 1
    print("Creating sorted sentence collection ...")
    
    diarization = file_manager.read_from_json_file(input_path)
    if diarization is None:
        print(f"{input_path} is not found.")
        print(f"Processing {input_path}")
        return
    speakers_context = process_diarizated_text(diarization)
    
    for line in speakers_context:    # 0 time, 1 speaker, 2 sentence
        raw_sentence_collection[index] = {
            'time': line[0],
            'speaker': line[1],
            'original_sentence': line[2]
        }
        index += 1

    file_manager.save_to_json_file(output_path, raw_sentence_collection)

    return raw_sentence_collection


# Given a list of diarization results
# Return a list of transcripts separating for time, speaker, and text
def process_diarizated_text(diarization_result):
    # Loads diarization results from a file, if it exists
    speakers_context = [] # List of the transcripts for each speaker
    sentence_splitter = SentenceSplitter(language='en')
    for transcript in diarization_result:
        parts = transcript.split("||")
        if len(parts) > 1:
            text_time, speaker_label, text = parts[0].split("]")[0].strip()[1:], parts[0].split("]")[1].strip(), parts[1].strip()
            # Appens the time, speaker, and text to the 3D list
            if text:
                for ds in sentence_splitter.split(text):
                    ds = ds.strip()
                    if ds:
                        ds = ds[0].upper() + ds[1:]
                        if ds[-1] not in ['.', '?', '!', '-', '"', "'", "(", ")"]:
                            ds += "."
                        speakers_context.append([text_time, speaker_label, ds])

    return speakers_context


def get_diarization_grouped_by_speaker(diarization_result):
        # Loads diarization results from a file, if it exists
        speakers_context = {} # List of the transcripts for each speaker
        for transcript in diarization_result:
            parts = transcript.split("||")
            if len(parts) > 1:
                speaker_label, text = parts[0].split("]")[1].strip(), parts[1].strip()

                if speaker_label in speakers_context:
                    speakers_context[speaker_label] += " " + text
                else:
                    speakers_context[speaker_label] = text

        return speakers_context


def prepare_sentences_collection_of_directory(
        file_manager: FileManager,
        diarized_directory="cache/diarized_transcripts", 
        sentence_collection_directory="cache/raw_sorted_sentence_collection", 
    ):
    # Loop through the files in the directory
    for diarized_transcript_file in os.listdir(diarized_directory):
        if diarized_transcript_file[0] == ".":
            continue

        diarized_transcript_path = os.path.join(diarized_directory, diarized_transcript_file)
        sentence_collection_path = os.path.join(sentence_collection_directory, diarized_transcript_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(diarized_transcript_path):
            print(f"Found diarized transcript file: {diarized_transcript_path}")

            prepare_sorted_sentence_collection(file_manager, diarized_transcript_path, sentence_collection_path)


def get_args():
    parser = argparse.ArgumentParser(description="Prepare a sorted sentence collection from a transcript file or a directory of transcript files.")
    parser.add_argument("-tf", "--transcript_file", type=str, help="Path to where the input transcript file is located.")
    parser.add_argument("-sf", "--sentences_file", type=str, help="Path to where the output sentences collection file will be saved.")
    parser.add_argument("-td", "--transcript_directory", type=str, help="Path to the directory containing the input transcript files.")
    parser.add_argument("-sd", "--sentences_directory", type=str, help="Path to the directory where the output sentences collection files will be saved.")

    return parser.parse_args()


def main():
    global input_directory, output_directory
    file_manager = FileManager()
    transcript_directory = input_directory
    sentences_directory = output_directory
    args = get_args()

    if args.transcript_file:
        if args.transcript_directory:
            raise ValueError("Error: Please provide either a transcript file or a transcript directory.")
        elif args.sentences_file:
            prepare_sorted_sentence_collection(file_manager, args.transcript_file, args.sentences_file)
        elif args.sentences_directory:
            transcript_file = os.path.basename(args.transcript_file)
            transcript_name, transcript_extension = os.path.splitext(transcript_file)
            prepare_sorted_sentence_collection(file_manager, args.transcript_file, os.path.join(args.sentences_directory, transcript_name + ".json"))
        else:
            transcript_file = os.path.basename(args.transcript_file)
            transcript_name, transcript_extension = os.path.splitext(transcript_file)
            prepare_sorted_sentence_collection(file_manager, args.transcript_file, os.path.join(sentences_directory, transcript_name + ".json"))

    elif args.transcript_directory:
        if args.sentences_directory:
            prepare_sentences_collection_of_directory(file_manager, args.transcript_directory, args.sentences_directory)
        elif args.sentences_file:
            raise ValueError("Error: Please provide a directory to save the sentences collection files.")
        else:
            prepare_sentences_collection_of_directory(file_manager, args.transcript_directory, sentences_directory)
        
    elif args.sentences_file or args.sentences_directory:
        raise ValueError("Error: Please provide a transcript file or a transcript directory.")

    else:
        prepare_sentences_collection_of_directory(file_manager, transcript_directory, sentences_directory)


if "__main__" == __name__:
    main()