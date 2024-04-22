import gradio as gr
import tracemalloc
import time
from english_tutor import EnglishTutor
import re

global speakers_context, selected_speaker_text, english_tutor
english_tutor = None
speakers_context = None
selected_speaker_text = None
speaker_colors = {"speaker1": "#40E0D0", 
                  "speaker2": "#FFA07A", 
                  "speaker3": "#FFD700", 
                  "speaker4": "#FF6347", 
                  "speaker5": "#FF69B4", 
                  "speaker6": "#7B68EE", 
                  "speaker7": "#00FF7F", 
                  "speaker8": "#FF4500", 
                  "speaker9": "#FF1493", 
                  "speaker10": "#FF33FF",}

tracemalloc.start()

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor, speakers_context

    if english_tutor is None:
        print("initialize english_tutor started")
        english_tutor = EnglishTutor()
        print("initialize english_tutor finished")

    if speakers_context is None:
        print("initialize speakers_context started")
        # A list of speakers and their transcripts from the audio file.
        speakers_context = english_tutor.get_speakers_context()
        print("initialize speakers_context finished")

# Chat with the AI using the given query.
def chat_with_ai(query):
    global selected_speaker_text, english_tutor
    context = ""

    if selected_speaker_text is not None:
        context += "\nYou are given direct speech from a user. When responding, address the user by name: \n"
        context += selected_speaker_text

    D, I, RAG_context = english_tutor.search_in_faiss_index(query, k=3)
    context_str = "\n".join(RAG_context)

    context += "\n\nThe English rule:\n"
    context += "\n\n" + context_str + "\n"

    final_prompt = (f"Based on your extensive knowledge and the following detailed context, please provide a "
                    f"comprehensive answer to explain the English rule:\n\nCONTEXT:\n{context}\n\nQUESTION:\n{query}")
    print("final_prompt:")
    print(final_prompt)
    start_time = time.time()
    response = english_tutor.get_answer(final_prompt, 200)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to get the response: {elapsed_time} seconds")

    new_chat_history_item = ("\n Q: " + query +
                             "\n A: " + response +
                             "\n ------------------------")

    english_tutor.update_chat_history(new_chat_history_item)

    output = ''
    for sentence in english_tutor.get_chat_history():
        output += sentence
    return output


def get_video(video_url):
    global english_tutor, speakers_context
    clean_cache()

    info_dict = english_tutor.get_video_info(video_url)
    video_title = info_dict.get('title', None)
    print("Title: " + video_title)

    english_tutor.download_audio(video_url)

    # Get the speakers' context from the video.
    # A list of speakers and their transcripts from the audio file.
    # At the moment the value is a default text.
    speakers_context = english_tutor.get_speakers_context()

    return f"Video info: {video_title}"


# Update the dropdown with the speakers' names.
# Gets the speakers' names from the speakers_context dictionary.
def update_dropdown(_=None):
    global speakers_context
    sorted_speakers = []
    if speakers_context is not None:
        sorted_speakers.append("All speakers")
        # Get the speakers names
        sorted_speakers += sorted( {speaker_context[1] for speaker_context in speakers_context} )
    return sorted_speakers

# TODO: finish this function
# Labels the speaker text to highlight the errors and speaker's name.
def label_speaker_text(speaker_selection):
    global selected_speaker_text, speakers_context, english_tutor

    colors = speaker_colors.copy()
    labeled_speaker_text = []
    speakers = {}
    if speakers_context is not None:
        if speaker_selection == "All speakers":
            for speaker_context in speakers_context:
                labeled_speaker_text.append( ("\n\n" + speaker_context[0] + "] ", "time") )
                #labeled_speaker_text.append( (speaker_context[1], "speaker") )
                if speaker_context[1] not in speakers:
                    # speaker_name = speaker_color_key
                    speakers[speaker_context[1]] = colors.popitem()[0]
                labeled_speaker_text.append( (speaker_context[1], speakers[speaker_context[1]]) )
                labeled_speaker_text.append( (speaker_context[2], "text") )
        #else:
            # specific speaker text
        #    selected_speaker_text = "\n\n".join(
        #        speaker_context[0] + "] " 
        #        + "**" + speaker_context[1] + "** "
        #        + speaker_context[2] + "\n" 
        #        for speaker_context in speakers_context if speaker_context[1] == speaker_selection)

    return labeled_speaker_text

# Receives as a parameter the name of the speaker selected in the dropdown.
# Returns a string that is the text spoken by the selected speaker or speakers.
# 0 -> time, 1 -> speaker, 2 -> text
def handle_dropdown_selection(speaker_selection):
    global selected_speaker_text, speakers_context, english_tutor
    tuple_labels = label_speaker_text(speaker_selection)
    
    return tuple_labels
        


def get_audio_path():
    audio_path = "audio/extracted_audio.wav"
    return audio_path


def refresh_audio(_=None):
    return get_audio_path()


def clean_cache():
    global speakers_context, selected_speaker_text, english_tutor
    #english_tutor.clean_cache()
    speakers_context = None
    selected_speaker_text = None


def split_inclusive(text, separator):
    return re.split(f'({re.escape(separator)})', text)


def label_text(text, input, label=None):
    separated_text = split_inclusive(text, input)
    
    if len(separated_text) == 1:
        return [(separated_text[0], None)]
    else:
        result = []
        for subtext in separated_text:
            if subtext == input:
                result.append((subtext, label))
            else:
                result.append((subtext, None))
        return result
    

def main():
    print(gr.__version__)
    # Create the Gradio interface.
    with gr.Blocks() as demo:
        gr.Markdown("Chat with English Tutor AI")
        with gr.Row():
            # Block for downloading the audio from the YouTube video.
            with gr.Column():
                link = gr.Textbox(
                        lines=2,
                        label="Enter link to YouTube's video: (ex. https://www.youtube.com/watch?v=wv_nEUnhFFE )"
                    )
                with gr.Column():
                    # Process the YouTube link when the submit button is clicked.
                    info_markdown = gr.Markdown("Video info:")

                    submit_button_yt = gr.Button("Download audio")
                    submit_button_yt.click(fn=get_video, inputs=[link], outputs=[info_markdown])

            # Block for playing the audio.
            with gr.Column():
                audio_player = gr.Audio(value=get_audio_path, label="Listen to the audio", type="filepath")
                refresh_button = gr.Button("Refresh video")
                refresh_button.click(fn=get_audio_path, inputs=[], outputs=audio_player)

        with gr.Row(equal_height=True):
            # Block for the transcript of the speakers in the audio.
            with gr.Column():
                sorted_speakers = update_dropdown()
                default_value = sorted_speakers[0] if sorted_speakers else None
                dropdown = gr.Dropdown(label="Select a speaker", choices=sorted_speakers, value=default_value)
                #speaker_text = gr.Textbox(label="Speaker's text", value=handle_dropdown_selection(default_value),
                #                          interactive=False, lines=10, elem_id="speaker_text")

                speaker_text = gr.HighlightedText(
                    label="Transcript",
                    value=handle_dropdown_selection(default_value),
                    interactive=False,
                    combine_adjacent=True,
                    show_legend=True,
                    color_map=speaker_colors
                )
                dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text])

            # Block for chatting with the AI.
            with gr.Column():
                #gr.Markdown("Chat with English Tutor AI")
                response = gr.Textbox(label="Chat History:", interactive=False, lines=10, autoscroll=True, elem_id="chatbot_response")
                query = gr.Textbox(label="Enter your query: (ex. How does past perfect work? )")
                submit_button = gr.Button("Submit")
                # Process the user query when the submit button is clicked.
                submit_button.click(fn=chat_with_ai, inputs=[query], outputs=[response])
                gr.HighlightedText(
                    value=[
                        ("In your phrase", None),
                        ("'I likes tomato'", "neutro"),
                        ("you should use", None), 
                        ("like", "bien"),
                        ("instead of", None),
                        ("likes", "mal")
                    ],
                    combine_adjacent=True,
                    show_legend=True,
                    color_map={"bien": "#36f802", "mal": "#FF0000", "neutro": "white"},),
                theme=gr.themes.Base()

    demo.launch()



if __name__ == '__main__':
    initialize_global_variables()
    main()
