import gradio as gr
import tracemalloc
import time
from english_tutor import EnglishTutor
import re

english_tutor: EnglishTutor | None = None
speakers_context: dict | None = None
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

tracemalloc.start()

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor, speakers_context

    if english_tutor is None:
        print("initialize english_tutor started")
        english_tutor = EnglishTutor()
        english_tutor.set_rag_engine("faiss")
        print("initialize english_tutor finished")

    if speakers_context is None:
        print("initialize speakers_context started")
        # A list of speakers and their transcripts from the audio file.
        speakers_context = english_tutor.get_speakers_context()
        print("initialize speakers_context finished")

# Chat with the AI using the given query.
def chat_with_ai(query):
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


# Given a text and the word to highlight, it returns the text with the word highlighted.
def highlight_error(text, word, font_color="#e43b29", background_color="#4f5b66"):
    style = f'"color: {font_color}; background-color: {background_color}; font-weight: bold"'
    return text.replace(word, f'<span style={style} >{word}</span>')


# Given a text, font color, and background color
# Returns the text with the given font and background color.
# Markdown is used to highlight the text.
def highlight_text(text="", font_color="#FFFFFF", background_color="#000000"):
    return f'<span style="color: {font_color}; background-color: {background_color}">{text}</span>'


# Receives as a parameter the name of the speaker selected in the dropdown.
# Using speaker_context, it joins each sentence in a string.
# Returns a string that is the text spoken by the selected speaker or speakers.
# 0 -> time, 1 -> speaker, 2 -> text
def handle_dropdown_selection(speaker_selection):
    global selected_speaker_text, speakers_context, english_tutor, speaker_colors

    selected_speaker_text = 'No text to show.'
    if speakers_context is not None:
        # All speakers text
        if speaker_selection == 'All speakers':
            selected_speaker_text = "\n\n"
            for speaker_context in speakers_context:
                selected_speaker_text += (
                    '<a id="' + speaker_context[0] + '">'
                    + speaker_context[0] + " " 
                    + speaker_context[1] + " " 
                    + speaker_context[2] + "\n\n"
                    + "</a>"
                )
        else:
            # specific speaker text
            selected_speaker_text = "\n\n"
            for speaker_context in speakers_context:
                if speaker_context[1] == speaker_selection:
                    selected_speaker_text += highlight_text(text=
                            speaker_context[0] + " " 
                            + speaker_context[1] + " " 
                            + speaker_context[2],
                            background_color=speaker_color
                        ) + "\n\n"
                else:
                    selected_speaker_text += (
                        speaker_context[0] + " " 
                        + speaker_context[1] + " " 
                        + speaker_context[2] + "\n\n"
                    )

    # Add scrollable container
    result = f"<div>{selected_speaker_text}</div>"
    return result
        

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


# Splits the text by the separator and includes the separator in the result.
# Returns a list of strings.
def split_inclusive(text, separator):
    return re.split(f'({re.escape(separator)})', text)


# Highlights the input text with the given label in the text.
# Returns a list of tuples with the text and the label.
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
    
js = """"""
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
head_html = ""


print("Version of gradio: " + gr.__version__)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=js, head=head_html) as demo:
    initialize_global_variables()
    # All Components container
    with gr.Row():
        # Block for the transcript of the speakers in the audio.
        with gr.Column(scale=0.3):
            sorted_speakers = update_dropdown()
            default_value = sorted_speakers[0] if sorted_speakers else None
            with gr.Row(elem_classes="dropdown"):
                dropdown = gr.Dropdown(
                    label="Select a speaker", 
                    choices=sorted_speakers, 
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
            response = gr.Textbox(
                label="Chat History:", 
                interactive=False,  
                autoscroll=True, 
                elem_classes="chat-container",
                lines=33,
                max_lines=33,
                scale=3
                )
            query = gr.Textbox(
                label="Enter your query: (ex. How does past perfect work? )",
                lines=2,
                autoscroll=True,
                max_lines=2,
                scale=1
                )
            submit_button = gr.Button(
                value="Submit",
                scale=1,
                )
            # Process the user query when the submit button is clicked.
            submit_button.click(fn=chat_with_ai, inputs=[query], outputs=[response])
            # Or when the user presses the Enter key.
            query.submit(fn=chat_with_ai, inputs=[query], outputs=[response])
    
    theme=gr.themes.Base()

    



if __name__ == '__main__':
    is_public_link = False
    demo.launch(share=is_public_link)