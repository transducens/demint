# Thirdy party imports
import errant
from sentence_splitter import SentenceSplitter

from app.file_manager import FileManager


input_file = "./cache/diarization_result.json"
output_file = "./cache/raw_sorted_sentence_collection.json"


def prepare_sorted_sentence_collection(file_manager, speaker_context: list):
    raw_sentence_collection = {}
    index = 1
    print("Creating sorted sentence collection ...")
    for line in speaker_context:    # 0 time, 1 speaker, 2 sentence
        raw_sentence_collection[index] = {
            'time': line[0],
            'speaker': line[1],
            'original_sentence': line[2]
        }
        index += 1

    file_manager.save_to_json_file(output_file, raw_sentence_collection)

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


def main():
    file_manager = FileManager()

    diarization = file_manager.read_from_json_file(input_file)
    if diarization is None:
        print(f"{input_file} is not found.")
        print(f"Processing {input_file}")
        return
    speakers_context = process_diarizated_text(diarization)
    prepare_sorted_sentence_collection(file_manager, speakers_context)
    print("Raw Sorted Sentence Collection is created...")


if __name__ == '__main__':
    main()    