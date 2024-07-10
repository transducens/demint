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

# Testing
visible_options = False

tracemalloc.start()

prompt_question = [
    f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.",
    f"TASK:\n You have asked the student if he wants to attempt to write the sentence correctly. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n",
    f"TASK:\n You have asked the student if he wants an exercise in order to practice. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n",
    f"TASK:\n You have asked the student if he wants an extensive explanation of english grammar. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n",
    f"TASK:\n You have asked the student if he wants an example of the sentence. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n",
    f"TASK:\n Based on the student answer, check if his sentence is correct comparing it to corrected sentece provided in the context. If it is corrrect, tell the student he did well. In case it is not correct, tell the student which mistakes he has made including new errors not previously made.",
    f"QUESTION:\n Create an exercise of English base on the english rules and mistake description provided in the context in order to me to practice.",
    f"QUESTION:\n Base on the exercise propose to the student, correct his answer using if needed the english rules provided in the context",
    f"TASK:\n Give an extended explanation of the english grammar rules present in the context.",
    f"TASK:\n Create an example for the correct use of the english grammar rul provided in the context. Try to be original"
]

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor, state, max_new_tokens, response, explained_sentences_speaker, id_sentence, id_error, error, chat_response

    state = 0
    max_new_tokens = 200
    response = chat_response = ""

    if english_tutor is None:
        english_tutor = EnglishTutor()
        print("*" * 50)
        print("Loaded English Tutor")
        print("*" * 50)

    load_data() # Load the data from the cache files

    explained_sentences_speaker = get_explained_sentences_speaker(explained_sentences, "All speakers")
    id_sentence = id_error = 0
    error = None

def get_explained_sentences_speaker(explained_sentences, speaker:str):
    if speaker == "All speakers":
        return explained_sentences
    else:
        result = {}
        for key, value in explained_sentences.items():
            if value['speaker'] == speaker:
                result[key] = value
        return result

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
def chat_with_ai(user_input, history):
    global user_message, chat_answer, history_chat, highlighted_sentence_id, state
    
    # Testing vvvvvvvvv
    global visible_options
    visible_options = not visible_options
    # Testing ^^^^^^^^^

    user_message = user_input
    history_chat = history
    #highlighted_sentence_id = user_input
    error_sentence_id = "sentence_" + "53"  # The sentence id of the errors we are going to work with now.

    # temp
    """
    print("Preparing answer...")
    bot_response = ""
    for i in ["I", "am", "a", "robot", "but", "I", "am", "trying", "to", "help", "you"]:
        time.sleep(0.5)
        bot_response += i + " "
        yield bot_response
    
    chat_answer = bot_response
    """
    print("called bot response")
    output = ""
    history.append((user_input, "bot response"))   # must be Tuples
    
    # temp
    """
    if state == 0:
        output = select_error()
        state = 1
    
    elif state == 1:
        # Step 2: Exercises
        #msg = cl.Message(content='')
        #await msg.send()

        response = error_explanation()
        chat_response = "Do you want an extensive explanation of the English grammar of this case?"
        response += f"\n\n **{chat_response}**"
        output = response

        #counter += 1
        #cl.user_session.set("counter", counter)
        state = 2

    elif state == 2:
        response = ask_grammar(user_input)

        response = response.lower()
        output = ""
        if response == 'yes':
            output = explain_grammar()
        
        #response = "\n\n **Do you want an example of the correct use of the grammar rules?**"
        chat_response = "Do you want an example of the correct use of the grammar rules?"
        output += f"\n\n **{chat_response}**"
        
        state = 3

    elif state == 3:
        #response = await correct_exercise(message.content)
        response = ask_example(user_input)

        response = response.lower()
        output = ""
        if response == 'yes':
            output = create_example()
        
        chat_response = "Do you want an exercise to practice these grammar rules?"
        response += f"\n\n **{chat_response}**"
        state = 4

    elif state == 4:
        #response = await correct_exercise(message.content)
        response = ask_exercise(user_input)

        response = response.lower()
        outpu = ""
        if response == 'yes':
            output = create_exercise()
            output += "\n\n **Complete the exercise**"

            output = f"Here is an exercise in order to you to practise:\n{output}"
            state = 5
        else:
            output += "\n\n **Do you want to attempt to write the sentence correctly?**"
            state = 6
    elif state == 5:
        #response = await correct_exercise(message.content)
        output = correct_exercise(user_input)
        output += "\n\n **Do you want another exercise to practice these grammar rules?**"
        state = 4

    elif state == 6:
        response = ask_sentence(user_input)

        response = response.lower()
        if response == 'yes':
            state = 7
        else:
            state = 0
    elif state == 7:
        output = check_corrected(user_input)
        state = 0
    """
    
    return output, history, error_sentence_id



    #Delete
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
def build_transcript(speaker_name: str):
    global sentences_collection, speakers, selected_speaker

    selected_speaker = speaker_name

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

def handle_dropdown_selection(speaker_name: str):
    print("Called handle_dropdown_selection")
    return build_transcript(speaker_name)

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

def create_context():
    global error
    #errant = cl.user_session.get("error")
    errant = error

    mistake_description = errant['llm_explanation']
    RAG_context = errant['rag']

    content_list = [f'{item["content"]}' for item in RAG_context]
    context_str = "\n----------\n".join(content_list)

    context = "\n\nIncorrect Sentence:\n"
    context += "\n\n" + errant["sentence"] + "\n"

    context += "\n\Correct Sentence:\n"
    context += "\n\n" + errant["corrected_sentence"] + "\n"

    context += "\n\nThe English rule:\n"
    context += "\n\n" + context_str + "\n"

    context += "\n\nMistake description: \n"
    context += mistake_description

    return context

def error_explanation():
    context = create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    return response

def ask_grammar(student_response):
    #english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += chat_response

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an extensive explanation of english grammar. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    print("Respuesta: ", response)

    
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    response = response.split('>')[1].split('<')[0]

    return response

def ask_example(student_response):
    #english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += chat_response

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an example of the sentence. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response =  english_tutor.get_answer(final_prompt, max_new_tokens)
    print("Respuesta: ", response)

    
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    response = response.split('>')[1].split('<')[0]

    #cl.user_session.set("user_excercise", response)

    return response

def ask_exercise(student_response):
    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += chat_response

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an exercise in order to practice. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    print("Respuesta: ", response)
    
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    response = response.split('>')[1].split('<')[0]

    return response

def ask_sentence(student_response):
    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += chat_response

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants to attempt to write the sentence correctly. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    print("Respuesta: ", response)
    
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    

    response = response.split('>')[1].split('<')[0]

    return response

def explain_grammar():
    #english_tutor = cl.user_session.get("english_tutor")

    context = create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Give an extended explanation of the english grammar rules present in the context.")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    #cl.user_session.set("user_excercise", response)
    
    return response

def create_exercise():
    context = create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create an exercise of English base on the english rules and mistake description provided in the context in order to me to practice.")

    response =  english_tutor.get_answer(final_prompt, max_new_tokens)
    chat_answer = response
    #cl.user_session.set("user_excercise", response)
    
    return response

def correct_exercise(student_response):
    context = "The exercise propose to the student: \n"
    context += chat_answer

    context += "\n\nThe student answer:\n"
    context += "\n\n" + student_response + "\n"
    
    context += create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Base on the exercise propose to the student, correct his answer using if needed the english rules provided in the context"
        f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def create_example():
    context = create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Create an example for the correct use of the english grammar rul provided in the context. Try to be original")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def check_corrected(student_response):
    context = create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Based on the student answer, check if his sentence is correct comparing it to corrected sentece provided in the context. If it is corrrect, tell the student he did well. In case it is not correct, tell the student which mistakes he has made including new errors not previously made."
        f"ANSWER:\n{student_response}\n")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def select_error():
    global error
    print("selecting error")
    #explained_sentences_speaker = cl.user_session.get("explained_sentences_speaker")
    
    #id_sentence = cl.user_session.get("id_sentence")
    #id_error = cl.user_session.get("id_error")
    
    #errors_speaker = explained_sentences_speaker.items()
    errors_speaker = list(explained_sentences_speaker.values())
    error = errors_speaker[3]['errant'][0]

    original_sentence = error["sentence"]
    corrected_sentence = error["corrected_sentence"]

    def highlight_word_in_sentence(sentence, start_idx, end_idx, highlight_text):
            words = sentence.split()
            highlighted_sentence = " ".join(
                words[:start_idx] +
                [f'**[{highlight_text}]**'] +
                words[end_idx:]
            )
            return highlighted_sentence

    # Highlight the error and correction in the sentence
    highlighted_original_sentence = highlight_word_in_sentence(
        original_sentence, error["o_start"], error["o_end"],
        error["original_text"] if error["original_text"] else "______"
    )

    add = len(error["corrected_text"].split())

    highlighted_corrected_sentence = highlight_word_in_sentence(
        corrected_sentence, error["c_start"], error["c_end"] + add,
        error["corrected_text"] if error["corrected_text"] else f'~~{error["original_text"]}~~'
    )

    text = "**You've made a mistake in the following sentence:**\n\n*" + highlighted_original_sentence + "*\n\n"
    text += "**It's corrected sentence:**\n\n*" + highlighted_corrected_sentence + "*\n\n"
    text += error["llm_explanation"] + "\n\n"

    return text

    selected = False

    while id_sentence < len(errors_speaker) and not selected:
        #sentence_id, explained_sentence = errors_speaker[id_sentence]
        
        #errant_errors = explained_sentence['errant']
        errant_errors = errors_speaker[id_sentence]['errant']
        while id_error < len(errant_errors):
            print("id_sentence: ", id_sentence)
            print("id_error: ", id_error)

            error = errant_errors[id_error]

            original_sentence = error["sentence"]
            corrected_sentence = error["corrected_sentence"]

            def highlight_word_in_sentence(sentence, start_idx, end_idx, highlight_text):
                words = sentence.split()
                highlighted_sentence = " ".join(
                    words[:start_idx] +
                    [f'**[{highlight_text}]**'] +
                    words[end_idx:]
                )
                return highlighted_sentence

            # Highlight the error and correction in the sentence
            highlighted_original_sentence = highlight_word_in_sentence(
                original_sentence, error["o_start"], error["o_end"],
                error["original_text"] if error["original_text"] else "______"
            )

            add = len(error["corrected_text"].split())

            highlighted_corrected_sentence = highlight_word_in_sentence(
                corrected_sentence, error["c_start"], error["c_end"] + add,
                error["corrected_text"] if error["corrected_text"] else f'~~{error["original_text"]}~~'
            )

            text = "**You've made a mistake in the following sentence:**\n\n*" + highlighted_original_sentence + "*\n\n"
            text += "**It's corrected sentence:**\n\n*" + highlighted_corrected_sentence + "*\n\n"
            text += error["llm_explanation"] + "\n\n"
            text += "Do you want to practice the error?"

            # Ask if wanna study that error with exercises
            #await cl.Message(
            #    content=text,
            #).send()
            #go_check_error = await ask_action()
                
            if go_check_error["value"] == "cancel":
                id_error += 1
            else:
                # Step 2: Exercises
                cl.user_session.set("error", error)

                cl.user_session.set("id_sentence", id_sentence)
                cl.user_session.set("id_error", id_error)
                selected = True

                #await on_message(None)
                break

        id_sentence += 1
        id_error = 0

    return


js = "./app/gradio_javascript.js"
css = "./app/gradio_css.css"
head_html = ""
with open("./app/gradio_head_html.html", 'r') as file:
    head_html = file.read()

js_autoscroll_by_id = "(sentence_id) => {js_autoscroll_by_id(sentence_id);}"
js_toggle_visibility = "(msg, hist, htxt) => {js_toggle_visibility(); return [msg, hist];}"


print("Version of gradio: " + gr.__version__)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=None, head=head_html) as demo:
    get_arguments_env()
    initialize_global_variables()
    print("*" * 50)
    print("Selected speaker: ", selected_speaker)
    print("*" * 50)

    # All Components container
    with gr.Row():
        # Block for the transcript of the speakers in the audio.
        with gr.Column(scale=0.3):
            with gr.Group():
                with gr.Row(elem_classes="dropdown"):
                    dropdown = gr.Dropdown(
                        label="Select a speaker", 
                        choices=speakers, 
                        value=selected_speaker, 
                        interactive=True,
                        )
                with gr.Row(elem_classes="transcript"):
                    speaker_text = gr.Markdown(
                        value=handle_dropdown_selection(selected_speaker),
                            latex_delimiters=[], # Disable LaTeX rendering
                        )
                    dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text])
            


        # Block for chatting with the AI.
        with gr.Column(scale=0.7, variant="default"):
            with gr.Group():
            # lg.primary.svelte-cmf5ev
                chatbot = gr.Chatbot(
                    layout="bubble",
                    bubble_full_width=False,
                    elem_id = "chatbot",
                    height="80vh"
                )
                with gr.Row(elem_id="option_buttons"):
                    #visible_options = True
                    option1 = gr.Button(
                        value="Option 1",
                        elem_id="option1",
                        scale=1,
                    )
                    option2 = gr.Button(
                        value="Option 2",
                        elem_id="option2",
                        scale=1,
                    )
                    option3 = gr.Button(
                        value="Option 3",
                        elem_id="option3",
                        scale=1,
                    )
                    option4 = gr.Button(
                        value="Option 4",
                        elem_id="option4",
                        scale=1,
                    )
                with gr.Row(elem_id="chat_input"):
                    txtbox = gr.Textbox(
                        label="",
                        elem_id="textbox_chatbot",
                        scale=4,
                        placeholder="Type a message...",
                        container=False,
                    )
                    submit_button = gr.Button(
                        value="Submit",
                        elem_id="submit_button",
                        elem_classes="svelte-cmf5ev",
                        scale=1,
                    )
            hidden_textbox = gr.Textbox(value="", visible=False, render=True)

            submit_button.click(chat_with_ai, [txtbox, chatbot], [txtbox, chatbot, hidden_textbox], js=js_toggle_visibility)
            txtbox.submit(chat_with_ai, [txtbox, chatbot], [txtbox, chatbot, hidden_textbox], js=js_toggle_visibility)
            chatbot.change(fn=None, inputs=[hidden_textbox], js=js_autoscroll_by_id) 

    theme=gr.themes.Base()


if __name__ == '__main__':
    is_public_link = False
    demo.launch(
        share=is_public_link,
        server_name="localhost",
        server_port=8001,
        )
