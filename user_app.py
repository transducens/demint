import gradio as gr
import tracemalloc
import time
import os
import argparse

from english_tutor import EnglishTutor
from app.file_manager import FileManager
import app.prepare_sentences as prepare_sentences
import app.rag_sentences as rag_sentences

english_tutor: EnglishTutor | None = None
sentences_collection: dict | None = None
explained_sentences: dict | None = None
speakers: list | None = None
selected_speaker_text = None
default_colors = {
    "red": "#fd0000",
    "blue": "#4a95ce",
    "light blue": "#c0d6e4",
    "gray": "#819090",
    "purple": "#800080",
    "pink": "#ff80ed",
    "brown": "#c1813b",
    "orange": "#edb626",
    "dark blue": "#213a85",
    "olive": "#947825"
}
speaker_color = default_colors['dark blue']
user_message, chat_answer, history_chat = "", "", []
highlighted_sentence_id = ""
selected_speaker = "All speakers"

tracemalloc.start()

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor

    if english_tutor is None:
        english_tutor = EnglishTutor()
        print("*" * 50)
        print("Loaded English Tutor")
        print("*" * 50)

    load_data() # Load the data from the cache files


# Load the data from the cache files. If the cache files are not found, then create them.
def load_data():
    global sentences_collection, explained_sentences, speakers
    start_load = time.time()
    file_manager = FileManager()
    input_files = {
        'sentences_collection': "cache/raw_sorted_sentence_collection.json",
        'explained_sentences': "cache/rag_sentences.json",
    }
    
    if not os.path.isfile(input_files['sentences_collection']):
        print(f"{input_files['sentences_collection']} is not found.")
        print(f"Processing {input_files['sentences_collection']}")
        prepare_sentences.main()
    
    if not os.path.isfile(input_files['explained_sentences']):
        print(f"{input_files['explained_sentences']} is not found.")
        print(f"Processing {input_files['explained_sentences']}")
        rag_sentences.main()

    explained_sentences = file_manager.read_from_json_file(input_files['explained_sentences'])
    sentences_collection = file_manager.read_from_json_file(input_files['sentences_collection'])
    speakers = get_speakers()

    end_load = time.time()
    print("*" * 50)
    print(f"Loaded data. Time: {end_load - start_load} seconds")
    print("*" * 50)

    return explained_sentences, sentences_collection, speakers


# Returns a list of all the speakers that have spoken in the transctipt
def get_speakers():
    sorted_speakers = []
    if sentences_collection is not None:
        sorted_speakers.append("All speakers")
        # Get the speakers names
        sorted_speakers += sorted( {value['speaker'] for value in sentences_collection.values()} )
    
    return sorted_speakers


# Chat with the AI using the given query.
def chat_with_ai(user_input, history=None):
    global user_message, chat_answer, history_chat, highlighted_sentence_id
    user_message = user_input
    history_chat = history
    highlighted_sentence_id = user_input
    
    # temp
    print("Preparing answer...")
    bot_response = ""
    for i in ["I", "am", "a", "robot", "but", "I", "am", "trying", "to", "help", "you"]:
        time.sleep(0.5)
        bot_response += i + " "
        yield bot_response
    
    chat_answer = bot_response
    return ""
    # temp

    print("pressed")
    global selected_speaker_text, english_tutor
    context = ""

    if selected_speaker_text is not None:
        context += "\nYou are given direct speech from a user. When responding, address the user by name: \n"
        context += selected_speaker_text

    D, I, RAG_context = english_tutor.search_in_index(query, k=3)
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


# TODO maybe not necessary. If it is, then move to another file and use here only the function.
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


# Given a text and the word to highlight, it returns the text with the word highlighted.
def highlight_errors_in_text(text, words=[], word_indexes=[], font_color="#FFFFFF", background_color="#FF0000"):
    style = f'"color: {font_color}; background-color: {background_color}; font-weight: bold"'

    # If words list is not empty then using words list
    # Otherwise use word_indexes list
    if words != []:
        for word in words:
            text.replace(word, f'<span style={style} >{word}</span>')
        return text
    else:
        splitted_text = text.split()
        for error_index_word in word_indexes:
            splitted_text[error_index_word] = f'<span style={style} >{splitted_text[error_index_word]}</span>'
        text = " ".join(splitted_text)
        return text


# Given a text, font color, and background color
# Returns the text with the given font and background color.
# Markdown is used to highlight the text.
def highlight_text(text="", font_color="#FFFFFF", background_color="#000000"):
    return f'<span style="color: {font_color}; background-color: {background_color}">{text}</span>'


# Given a sentence, checks in explained_sentences if that sentence has errors and 
# if so highlights them in red
# Returns a string of the sentence with the words highlighted using html and css
def highlight_errors_all(sentence: str):
    global explained_sentences
    
    if sentence in explained_sentences:
        word_indexes = []
        for es in explained_sentences[sentence]:
            for label_error in es['errant']:
                word_indexes.append(label_error['o_start'])

        return highlight_errors_in_text(text=sentence, word_indexes=word_indexes)


# Receives as a parameter the name of the speaker selected in the dropdown.
# Using sentences_collection, it joins each sentence in a string.
# 0 -> time, 1 -> speaker, 2 -> text
def handle_dropdown_selection(speaker_name: str, highlight_sentence_num=0):
    global sentences_collection, speakers, selected_speaker

    selected_speaker = speaker_name
    selected_line = highlight_sentence_num if highlight_sentence_num != 0 else ""

    text_to_show = 'No text to show.'
    if sentences_collection is not None:
        # All speakers text
        if selected_speaker == 'All speakers':
            text_to_show = "\n\n"
            for index, value in sentences_collection.items():
                if highlight_sentence_num and index == highlight_sentence_num:
                    # Label each line and print it
                    text_to_show += (
                        '<a id="sentence_' + index + '">'
                        + value['speaker'] + " " 
                        + value['original_sentence'] + "\n\n"
                        + "</a>"
                    )
        else:
            # specific speaker text
            text_to_show = "\n\n"
            for index, value in sentences_collection.items():
                if value['speaker'] == selected_speaker:
                    # Highlight the lines of the selected speaker
                    text_to_show += highlight_text(text=(
                            '<a id="sentence_' + index + '">'
                            + value['speaker'] + " " 
                            + value['original_sentence'] + "</a>"),
                            background_color=speaker_color
                        ) + "\n\n"
                else:
                    # Label each line and print it
                    text_to_show += (
                    '<a id="sentence_' + index + '">'
                    + value['speaker'] + " " 
                    + value['original_sentence'] + "\n\n"
                    + "</a>"
                )

    # Add scrollable container
    result = f"<div id='transcript_id'>{text_to_show}</div>"
    return result
        

# TODO maybe not necessary. If it is, then move to another file and use here only the function.
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


# Gets the arguments from the environment variables.
def get_arguments_env():
    global selected_speaker
    arg_speaker = os.getenv("GRADIO_SPEAKER", "All speakers")
    selected_speaker = arg_speaker or selected_speaker

    
js = "./app/gradio_functions.js"
css = "./app/gradio_styles.css"
head_html = ""


print("Version of gradio: " + gr.__version__)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=js, head=head_html) as demo:
    get_arguments_env()
    initialize_global_variables()
    print("*" * 50)
    print("Selected speaker: ", selected_speaker)
    print("*" * 50)

    # All Components container
    with gr.Row():
        # Block for the transcript of the speakers in the audio.
        with gr.Column(scale=0.3):
            with gr.Row(elem_classes="dropdown"):
                dropdown = gr.Dropdown(
                    label="Select a speaker", 
                    choices=speakers, 
                    value=selected_speaker, 
                    interactive=True,
                    scale=1,
                    )
            with gr.Row(elem_classes="transcript"):
                speaker_text = gr.Markdown(
                    value=handle_dropdown_selection(selected_speaker),
                        latex_delimiters=[], # Disable LaTeX rendering
                    )
                dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text])
            


        # Block for chatting with the AI.
        with gr.Column(scale=0.7):
            # lg.primary.svelte-cmf5ev
            submit_button = gr.Button(
                value="Submit",
                render=False,   # rendered in chatBotInterface
                elem_id="submit_button",
                elem_classes="svelte-cmf5ev",
            )
            txtbox = gr.Textbox(
                label="Enter your query:",
                render=False,   # rendered in chatBotInterface
                scale=3,
            )
            chatBotInterface = gr.ChatInterface(
                fn=chat_with_ai,
                multimodal=False,
                autofocus=True,
                concurrency_limit=2,
                textbox=txtbox,
                submit_btn=submit_button,
            )


    theme=gr.themes.Base()

    



if __name__ == '__main__':
    is_public_link = False
    demo.launch(
        share=is_public_link,
        server_name="localhost",
        server_port=8001,
        )
