import gradio as gr
import tracemalloc
import time
import os

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

tracemalloc.start()

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor

    if english_tutor is None:
        english_tutor = EnglishTutor()
        print("**************************************")
        print("Loaded English Tutor")
        print("**************************************")

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
    print("**************************************")
    print(f"Loaded data. Time: {end_load - start_load} seconds")
    print("**************************************")

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
def chat_with_ai(user_input, history=None, textbox=""):
    global user_message, chat_answer, history_chat
    user_message = user_input
    history_chat = history
    
    # temp
    print("Preparing answer...")
    bot_response = ""
    for i in ["I", "am", "a", "robot", "but", "I", "am", "trying", "to", "help", "you"]:
        #time.sleep(0.5)
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
def handle_dropdown_selection(selected_speaker):
    global sentences_collection, speakers

    text_to_show = 'No text to show.'
    if sentences_collection is not None:
        # All speakers text
        if selected_speaker == 'All speakers':
            text_to_show = "\n\n"
            for index, value in sentences_collection.items():
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

    
js = """"""
js_autoscroll_function_by_value= """
    function autoscroll_to_string(word_to_search) {
    try {
        console.log("Searching for:", word_to_search);
        const anchors = document.querySelectorAll('#transcript_id a');
        let found = false;
        anchors.forEach(anchor => {
            if (anchor.textContent.includes(word_to_search)) {
                anchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                anchor.animate([
                    { backgroundColor: 'yellow' },
                    { backgroundColor: 'transparent' }
                ], {
                    duration: 2000,
                    iterations: 1
                });
                found = true;
            }
        });
        if (!found) {
            console.log('Element not found for:', word_to_search);
        }
    } catch (error) {
        console.error("Error in autoscroll_to_string:", error);
    }
}
"""
js_autoscroll_function_by_id= """
    function(word_to_search) {
        const id_holder = document.querySelector('meta[name="sentence_id"]');
        console.log("Searching for id:", id_holder);
        const element = document.getElementById(id_holder); 
        if (element) { 
            element.scrollIntoView({behavior: 'smooth', block: 'center'}); 
            element.animate([{ backgroundColor: 'yellow' }, { backgroundColor: 'transparent' }], { duration: 2000, iterations: 1 }); 
        } 
        else { 
            console.log('Element not found for:', word_to_search); 
        }
    }
"""
js_trigger_button = """
    function trigger_button() {
        setTimeout(function() {
            document.querySelector("#mybutton").click();
            console.log("Button clicked");
        }, 5000);
    }
"""
js_print = """
    function js_print() {
        console.log("HTML WORKS");
        sentence = "sentence_5";
    }
"""

css = """
    .fullscreen {
       height: 90vh;
       width: 150vh;
    }
    .dropdown {
        height: 10vh;
    }
    .transcript {
        height: 80vh;
        overflow-y: scroll;
        padding: 10px; 
        border: 1px solid #ddd; 
        border-radius: 5px;
    }
    .chat-container {
        height: 73vh;
    }
    a {
        color: inherit;
        outline: none;
        text-decoration: none;
        -webkit-tap-highlight-color: white;
    }

"""
head_html = '<meta name="sentence_id" content="sentence_1">'


# Temp
def get_id_holder(value=""):
    global id_holder
    id_holder = value
    return id_holder

print("Version of gradio: " + gr.__version__)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=js, head=head_html) as demo:
    initialize_global_variables()
    # All Components container
    with gr.Row():
        # Block for the transcript of the speakers in the audio.
        with gr.Column(scale=0.3):
            default_value = speakers[0] if speakers else None
            with gr.Row(elem_classes="dropdown"):
                dropdown = gr.Dropdown(
                    label="Select a speaker", 
                    choices=speakers, 
                    value=default_value, 
                    interactive=True,
                    scale=1,
                    every=1
                    )
            with gr.Row(elem_classes="transcript"):
                speaker_text = gr.Markdown(
                    value=handle_dropdown_selection(default_value),
                        latex_delimiters=[], # Disable LaTeX rendering
                        every=10
                    )
                dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text])
            


        # Block for chatting with the AI.
        with gr.Column(scale=0.7):
            scroll_button = gr.Button(elem_id="mybutton", visible=True)
            scroll_button.click(fn=None, js=js_autoscroll_function_by_id)

            sb_btn = gr.Button(
                value="Submit",
                render=False,   # rendered in chatBotInterface
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
            )
            gr.HTML().change(fn=None, js=js_print)
            txtbox.submit(fn=None, js=js_autoscroll_function_by_id)

    theme=gr.themes.Base()

    



if __name__ == '__main__':
    is_public_link = False
    demo.launch(
        share=is_public_link,
        server_name="localhost",
        server_port=8001,
        )
