from datetime import datetime
import time
import gradio as gr
import os
import argparse
import warnings

welcome_message = "Hello! I am your English tutor. I will help you to learn English. Are you ready?"

# Suppress the warnings
# warnings.filterwarnings("ignore")

# takes too long to load:
# from english_tutor import EnglishTutor
from app.file_manager import FileManager
from app.teacher_model import TeacherModel

print("Starting the application", flush=True)


# english_tutor: EnglishTutor | None = None
english_tutor = None
teacher_model: TeacherModel | None = None
sentences_collection: dict | None = None
explained_sentences: dict | None = None
speakers: list | None = None
selected_speaker_text = None
kind_teacher_port = 8000
kind_teacher_address = "localhost"
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
highlighted_sentence_id = 1
new_conversation = True

# Arguments
log_conversation = True
new_conversation = True
conversation_name = ""
port = 7860
selected_speaker = "All speakers"



from openai import OpenAI

from pydantic import BaseModel
class ResponseStruct(BaseModel):
    intention: str
    response: str

# Initialize the global variables.
def initialize_global_variables():
    global english_tutor, state, max_new_tokens, response, explained_sentences_speaker 
    global id_sentence, id_error, error, chat_response, category_list, category_errors
    global index_category, index_error, count, selected_speaker
    global state_change 
    global teacher_model, kind_teacher_address, kind_teacher_port

    state = -1
    max_new_tokens = 200
    count = 0
    response = chat_response = ""

    if english_tutor is None:
        # english_tutor = EnglishTutor()
        english_tutor = OpenAI()
        print("*" * 50)
        print("Loaded English Tutor")
        print("*" * 50)

    try:
        if teacher_model is None:
            teacher_model = TeacherModel(address=kind_teacher_address, port=kind_teacher_port)

            if teacher_model.test_connection():
                print("*" * 50)
                print("Confirmed connection with Teacher Model")
                print("*" * 50)
            else:
                raise ValueError("Error connecting to Teacher Model")
    except:
        teacher_model = None
        print("~" * 50)
        print("ERROR: Could not connect to Teacher Model")
        print("~" * 50)

    print("Before load data", flush=True)
    load_data() # Load the data from the cache files
    print("After load data", flush=True)

    if selected_speaker != "All speakers" and selected_speaker not in speakers:
        raise ValueError(f"The speaker '{selected_speaker}' is not in the list of speakers.")

    explained_sentences_speaker = get_explained_sentences_speaker(explained_sentences, "All speakers")
    id_sentence = id_error = 0
    error = None
    category_list = {}
    category_errors = {}
    state_change = False

    index_category = index_error = 0

    list_errors()

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
    global sentences_collection, explained_sentences, speakers, conversation_name
    start_load = time.time()
    file_manager = FileManager()
    input_files = {
        'sentences_collection': f"cache/raw_sorted_sentence_collection/{conversation_name}.json",
        'explained_sentences': f"cache/rag_sentences/{conversation_name}.json",
    }

    print(f"Reading cache files from: {input_files['sentences_collection']} and {input_files['explained_sentences']}")
    
    if (not os.path.isfile(input_files['sentences_collection']) 
        or not os.path.isfile(input_files['explained_sentences'])):
        raise FileNotFoundError("The cache files of the conversation are not found. Please run the 'run_pipeline.sh' script to create the cache files.")
        
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

# -------------------------------------------------------------
def new_new_change_state(user_response, history):
    global error
    #errant = cl.user_session.get("error")
    errant = error

    mistake_description = errant['llm_explanation']
    RAG_context = errant['rag']
    error_type = errant['error_type']
    exercise_sentence = errant['original_sentence']

    content_list = [f'{item["content"]}' for item in RAG_context]
    context_str = "\n----------\n".join(content_list)

    teacher_suggestion = None
    if teacher_model != None:
        list_history = history.copy()
        list_history.append((user_response))
        kind_teacher_prompt = teacher_model.format_messages(list_history)
        kind_teacher_response = teacher_model.get_response(kind_teacher_prompt)
        teacher_suggestion = teacher_model.format_response(kind_teacher_response)
    else:
        teacher_suggestion = "No suggestion available."

    # T5 explanation not used

    prompt = f"""
    
You are an English tutoring chatbot that helps non-native speakers analyze grammatical errors in sentences and correct them. Your goal is to help the user understand their mistakes, practice correcting the sentence with the error or other sentences with similar errors posed as exercises, and provide guidance based on various sources. The text that will be analyzed results from the transcription of a speech conversation between the user and other humans; therefore it may contain informal language. Your focus should be on the grammatical errors and not on the informal aspects of the conversation or the potential presence of incomplete sentences.

There are specific intentions that the user might express during the interaction as indicated below. Each intention is represented by an id such as I1 that you will use later to identify the user's intention.

I0. The last turn of the conversation is the string <start>, indicating the beginning of the discussion of a new error.
I1. The user wants to do an exercise where they correct a sentence with a similar error.
I2. The user wants to move on to the next error.
I3. The user does not understand the error and needs an additional explanation.
I4. The user has understood everything.
I5. The user wants to try writing the correct form of their erroneous sentence so that you can evaluate it.
I6. The user has an intention related to the conversation, requiring a response in context.
I7. The user has an unrelated intention, and you should gently remind them to stay on topic.
I8. The user is giving the answer to an exercise you proposed.

Your task is to identify the user's intention based on their input and respond appropriately. You are provided next with some information on the error that may help you generate responses. Although this information may be relevant in some cases, it may be inaccurate in others. Therefore, it is not mandatory that you use all the information provided.

Original sentence with the error: {exercise_sentence}

The information on the error obtained from different sources is:
- Error type as identified by the tool ERRANT: {error_type}
- Explanation of the error given by an AI model: {mistake_description}
- Potential relevant passages from English textbooks (retrieved via RAG): {context_str}
- Previous conversation context (excluding the most recent user input): {history}
- Current user input: {user_response}
- A suggestion for the teacher's response given by a AI teacher model with no specific knowledge of English learning: {teacher_suggestion}

### Instructions for response generation:
1. Identify the user's intention.
2. If the intention is:
- **I0**: Provide a very short explanation of the error using the provided information and your own knowledge of English grammar. Make sure you do not provide the correct sentence as part of the explanation as the user should try to correct it themselves. Ask then the user if they want to practice or move on to another error. 
- **I1**: Create a short simple English sentence with an error similar to the one the user made. Guide the user to attempt correcting {exercise_sentence} in your response.
- **I2**: Confirm their understanding and offer to analyze the next error.
- **I3**: Provide a detailed explanation using the provided information and your own knowledge of English grammar. Make sure you do not provide the correct sentence as part of the explanation as the user should try to correct it themselves. Ask then the user if they want to practice or move on to another error.
- **I4**: Acknowledge their understanding and tell them that you are ready to move on to the next error.
- **I5**: Ask the user to provide the correct form of their erroneous sentence.
- **I6**: Respond contextually using the provided information.
- **I7**: Politely remind the user to focus on the session and offer options related to language learning: practice, explanation, or moving on to the next error.
- **I8**: Evaluate the user's response according to your proposed exercise and provide feedback.
3. Always try to consider the user's intention and the provided context when generating responses. However, you can also exceptionally generate responses that do not directly use the provided information if you think they are more appropriate for the situation.
4. Make your responses sound natural and engaging to the user, but at the same time, be clear and concise in your explanations. Generate responses between 1 and 5 sentences long.
5. There is a sequence of interactions with the user that you should try to follow: explain the error, practice with other sentences, and get a correct sentence from the user. However, you can skip some steps if you think they are not necessary for the user's learning process.\n
6. Punctuation and capitalization errors are not considered in the evaluation of the user's response. Never inform the user of these types of errors. 

Always generate both the identified intention and the next response to the user in a structured JSON format like this (make sure you don't use quotes around keys but only around values):
{{intention: "INTENTION_ID", response: "GENERATED_RESPONSE"}}
"""
    
    prompt = f"""

You are an English tutoring chatbot that helps non-native speakers correct grammatical errors in transcriptions of their speech conversations. Your task is to guide users to understand and fix their mistakes through explanations, examples, and exercises that pose sentences with similar mistakes so that the user suggests the correct sentence. Focus on grammar and ignore informal language or incomplete sentences from transcriptions.

Identify the user's intention based on their input. The user's intention in a format like I0 can be one of the following:

- I0: The current user input is the string <start>, indicating the beginning of the discussion of a new error. Give a very brief explanation without providing the correct sentence. Ask the user if they want to practice with other sentences with similar errors, get a detailled explanation of the error, or move to the next error. Include the original sentence in your text. 
- I1: The user wants to correct a sentence with a similar error. Provide an example with a similar error.
- I2: The user is ready to move to the next error or explicitly indicates that they want to move on or discuss the next error.
- I3: The user needs more explanation. Give a detailed explanation without correcting the sentence.
- I4: The user understands everything. Acknowledge and move to the next error.
- I5: The user wants to correct their wrong sentence themselves. Ask them to submit their correction of the original sentence ({exercise_sentence}) for your evaluation.
- I6: The user requests a response in context. Respond based on the provided information.
- I7: The user is off-topic. Politely guide them back to the topic.
- I8: The user is answering an exercise. Evaluate their response and provide feedback. Do not be overly strict in your responses. Once the main error is corrected, avoid pointing out additional mistakes unless they are crucial.

Original sentence: {exercise_sentence}

You may use the following information to help generate responses, but it is not mandatory as it may be inaccurate:

- Error type (ERRANT tool): {error_type}
- Explanation of the error from an AI model: {mistake_description}
- Potentially relevant context from textbooks (RAG): {context_str}
- Previous conversation (excluding current user input): {history}
- Current user input: {user_response}
- A suggestion for the teacher's response given by a AI teacher model with no specific knowledge of English learning: {teacher_suggestion}

**Instructions**:

1. Identify the user's intention.
2. Generate a response in line with the identified intention:
   - Short, clear explanations (1-4 sentences).
   - Provide exercises, explanations, and feedback as appropriate.
3. Responses should be engaging, clear, and tailored to the user's input. However, you can also exceptionally generate responses that do not directly use the provided information if you think they are more appropriate for the situation.
4. Skip steps or condense explanations if unnecessary for the user's learning process.
5. Ignore punctuation and capitalization errors. Never inform the user of these types of errors. If this is the only error in the sentence, tell the user about it and propose to move to the next error.

Generate responses in the following JSON format:
{{intention: "INTENTION_ID", response: "GENERATED_RESPONSE"}}
"""

    completion = english_tutor.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an English tutoring chatbot that helps non-native speakers analyze grammatical errors in sentences and correct them."},
            {"role": "user", "content": prompt},
        ],
        response_format=ResponseStruct,
    )
    return completion.choices[0].message, prompt

    # response = english_tutor.get_answer(prompt, max_new_tokens).lower() 
    # return response


def get_next_error(index_category, index_error, categories, category_errors):
    if index_category >= len(categories):
        return False
    
    category = categories[index_category]
    list_tuples = category_errors[category]
    if index_error >= len(list_tuples):
        index_category += 1
        index_error = 0

    if index_category >= len(categories):
        return False
    
    list_tuples = category_errors[category]
    tuple_error = list_tuples[index_error]
    
    return True, tuple_error[0], tuple_error[1]

def parse_gpt4_output(output):
    if output.parsed:
        intention= output.parsed.intention
        output = output.parsed.response
        print(intention)
        print(output)
        return True, intention, output
    else:
        print(output.refusal)
        return False

# ---------------------------------------------
def chat_with_ai(user_input, history):
    global user_message, chat_answer, history_chat, highlighted_sentence_id, state
    global category_list, category_errors, index_category, index_error, count, log_conversation, chat_response, state_change
    
    categories = list(category_list.keys())
    next_error_exists, sentence_id, error_id = get_next_error(index_category, index_error, categories, category_errors)

    if not next_error_exists:
        output = "No errors left to check. The class is finished."
        return "", history, ""
    
    select_error(sentence_id, error_id)

    user_message = user_input if count != 0 else "<start>"
    output, prompt = new_new_change_state(user_message, history)

    parse_worked, intention, output = parse_gpt4_output(output)
    if not parse_worked:
        # set intention!!!!!!!!!!!!
        pass

    #if next_id == 'I2' or next_id == 'I3' or next_id == 'I4':
    count += 1

    if intention == 'I2' or intention == 'I4' or count==6:
        count = 0
        index_error += 1

        next_error_exists, sentence_id, error_id = get_next_error(index_category, index_error, categories, category_errors)

        if not next_error_exists:
            output = "No errors left to check. The class is finished."
            return "", history, ""
    
        select_error(sentence_id, error_id)

        user_message = "<start>"
        output, prompt = new_new_change_state(user_message, history)
        parse_worked, intention, output = parse_gpt4_output(output)
        if not parse_worked:
            # set intention!!!!!!!!!!!!
            pass
        output= "Next error. " + output

    # 1 is intialized to 1 menaing no actual sentence; this is a flag only activated at 
    # the beginning of the conversation when no sentence is highlighted
    if highlighted_sentence_id == 1:
        error_sentence_id = ""
    else:
        error_sentence_id = "sentence_" + str(highlighted_sentence_id)

    history.append((user_input, output))   # must be tuples
    
    if log_conversation:
        log_conversation_item(user_input, output)
        log_prompts(prompt, output)

    return "", history, error_sentence_id


def log_conversation_item(user_input, bot_response):
    global new_conversation
    file_manager = FileManager()
    filename = f"log/conversation_{conversation_name}_{selected_speaker}.json"
    item = {"user": user_input, "assistant": bot_response, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if not os.path.exists(filename):
        new_conversation = False
        file_manager.save_to_json_file(filename, [ {"conversation": [{"assistant": welcome_message}, item]} ])
        
    else:
        if new_conversation:
            # Create a new conversation
            new_conversation = False
            saved_data = file_manager.read_from_json_file(filename)
            saved_data.append( {"conversation": [{"assistant": welcome_message}, item]})
            file_manager.save_to_json_file(filename, saved_data)
            
        else:
            # Append to the existing conversation
            saved_data = file_manager.read_from_json_file(filename)
            saved_data[-1]["conversation"].append(item)
            file_manager.save_to_json_file(filename, saved_data)

def log_prompts(prompt, response):
    global new_conversation
    file_manager = FileManager()
    filename = f"log/prompts_{conversation_name}_{selected_speaker}.json"
    item = {"prompt": prompt, "response": response, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if not os.path.exists(filename):
        new_conversation = False
        file_manager.save_to_json_file(filename, [ {"prompt": [item]} ])
        
    else:
        if new_conversation:
            # Create a new conversation
            new_conversation = False
            saved_data = file_manager.read_from_json_file(filename)
            saved_data.append( {"prompt": [item]} )
            file_manager.save_to_json_file(filename, saved_data)
            
        else:
            # Append to the existing conversation
            saved_data = file_manager.read_from_json_file(filename)
            saved_data[-1]["prompt"].append(item)
            file_manager.save_to_json_file(filename, saved_data)


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
                    + '<span class="speaker_name"> ' + value['speaker'] + " </span> " 
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
                            + '<span class="selected_speaker_name"> ' + value['speaker'] + " </span> " 
                            + value['original_sentence'] + "</a>"),
                            background_color=speaker_color
                        ) + "\n\n"
                else:
                    # Label each line and print it
                    text_to_show += (
                    '<a id="sentence_' + index + '">'
                    + '<span class="speaker_name"> ' + value['speaker'] + " </span> " 
                    + value['original_sentence'] + "\n\n"
                    + "</a>"
                )
            
    # Add scrollable container
    result = f"<div id='transcript_id'>{text_to_show}</div>"
    return result

def handle_dropdown_selection(speaker_name: str):
    global selected_speaker
    selected_speaker = speaker_name

    reset_states()

    print("Called handle_dropdown_selection with speaker: ", speaker_name)
    return build_transcript(speaker_name), [("Hello, I am " + selected_speaker, welcome_message)], ""

def clean_cache():
    global speakers_context, selected_speaker_text, english_tutor
    #english_tutor.clean_cache()
    speakers_context = None
    selected_speaker_text = None

# Gets the arguments from the environment variables.
def get_arguments_env():
    global selected_speaker
    arg_speaker = os.getenv("GRADIO_SPEAKER", "All speakers")
    arg_speaker = os.getenv("GRADIO_PORT", "8000")
    arg_speaker = os.getenv("GRADIO_CONVER", "diarization_result")
    selected_speaker = arg_speaker or selected_speaker

# Gets the arguments from the command line.
def get_arguments():
    global log_conversation, selected_speaker, conversation_name, port
    global kind_teacher_port, kind_teacher_address
    parser = argparse.ArgumentParser(description="English Tutor Chatbot")

    parser.add_argument("-l", "--list", action="store_true", help="List all the conversations available.")
    parser.add_argument("--conver", required=False, type=str, help="The transcripted conversation to show. Default is diarization_result")
    parser.add_argument("--speaker", type=str, default="All speakers", help="The speaker to show in the transcript. Default is All speakers.")
    parser.add_argument("--port", type=int, default=7860, help="The port in which the server will run. Default is 7860")
    parser.add_argument("--no_log", action="store_true", help="If the flag is called, the chatbot conversation will not save logs of the execution. Default is False.")
    parser.add_argument("--port_kind_teacher", type=int, default=8000, help="The port in which the kind teacher will run. Default is 8000")
    parser.add_argument("--address_kind_teacher", type=str, default="localhost", help="The address in which the kind teacher will run. Default is localhost")

    args = parser.parse_args()

    port = args.port
    conversation_name = args.conver
    log_conversation = not args.no_log
    selected_speaker = args.speaker
    kind_teacher_port = args.port_kind_teacher
    kind_teacher_address = args.address_kind_teacher
    
    # If the list flag is called, then list all the conversations available and exit.
    if args.list:
        list_available_conversations()
        print()
        exit(0)

    if conversation_name is None:
        raise ValueError("The conversation name is not provided. Please provide a conversation name using the --conver flag.\nFor more information use the --help flag.")

def create_prompt(prompts):
    prompt = ""
    for x in prompts:
        prompt += x

    response = english_tutor.get_answer(prompt, max_new_tokens)

    return response


def list_errors():
    global error, category_list, category_errors, selected_speaker

    errors_speaker = list(explained_sentences_speaker.items())
    index_list = list(explained_sentences_speaker.keys())

    index_sentence = 0

    #selected_speaker = "SPEAKER_01"

    for _, xx in errors_speaker:
        index = index_sentence
        y = xx['errant']
        id_error = 0

        if xx['speaker'] != selected_speaker and selected_speaker != "All speakers":
            index_sentence += 1
            continue
        
        while id_error < len(y):
            value = category_list.get(y[id_error]['error_type'], 0)
            dupla = (index, id_error)
            if value == 0:
                category_list[y[id_error]['error_type']] = 1
                category_errors[y[id_error]['error_type']] = [dupla]
            else:
                list_index = category_errors[y[id_error]['error_type']]
                
                category_list[y[id_error]['error_type']] =  value + 1
                list_index.append(dupla)
                category_errors[y[id_error]['error_type']] = list_index

            id_error += 1
        
        index_sentence += 1
        
    category_list = {k: v for k, v in sorted(category_list.items(), key=lambda item: item[1], reverse=True)}
    print((category_list))
    print(category_errors)

    return

def select_error(index_sentence = 0, index_error = 0):
    global error, highlighted_sentence_id
    errors_speaker = list(explained_sentences_speaker.values())
    error = errors_speaker[index_sentence]['errant'][index_error]

    highlighted_sentence_id = list(explained_sentences_speaker.items())[index_sentence][0]
    
    original_sentence = error["original_sentence"]
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

    #text = "**You've made a mistake in the following sentence:**\n\n*" + highlighted_original_sentence + "*\n\n"
    #text += "**It's corrected sentence:**\n\n*" + highlighted_corrected_sentence + "*\n\n"
    #text += error["llm_explanation"] + "\n\n"
    incorrect_sentence = highlighted_original_sentence
    correct_sentence = highlighted_corrected_sentence
    explanation = error["llm_explanation"]

    return incorrect_sentence, correct_sentence, explanation

def reset_states():
    global state, index_category, index_error
    global selected_speaker, highlighted_sentence_id

    print("Resetting states with speaker: ", selected_speaker)

    initialize_global_variables()

    state = -1
    index_category = 0
    index_error = 0

def list_available_conversations():
    conversations_sentence_collection = []
    conversations_rag_sentences = []
    available_conversations = []
    file_manager = FileManager()
    input_directories = {
        'sentences_collection': f"cache/raw_sorted_sentence_collection/",
        'explained_sentences': f"cache/rag_sentences/",
    }

    # Loop through the files in the directory
    for file in os.listdir(input_directories['sentences_collection']):
        if file.endswith(".json"):
            conversations_sentence_collection.append(file)

    for file in os.listdir(input_directories['explained_sentences']):
        if file.endswith(".json"):
            conversations_rag_sentences.append(file)

    available_conversations = [item for item in conversations_sentence_collection if item in conversations_rag_sentences]

    print()
    print("Available conversations and speakers:")
    for conv in available_conversations:
        sorted_speakers = ["All speakers"]
        conver_path = input_directories['sentences_collection'] + conv

        sorted_sentences_collection = file_manager.read_from_json_file(conver_path)
        sorted_speakers += sorted( {value['speaker'] for value in sorted_sentences_collection.values()} )

        print("-", conv[:-5])
        for sp in sorted_speakers:
            print("  -", sp)
        print()


js = "./app/gradio_javascript.js"
css = "./app/gradio_css.css"
head_html = ""

with open("./app/gradio_head_html.html", 'r') as file:
    head_html = file.read()

js_autoscroll_by_id = "(sentence_id) => {js_autoscroll_by_id(sentence_id);}"
js_toggle_visibility = "(msg, hist, htxt) => {js_toggle_visibility(); return [msg, hist];}"
js_refresh_page = "(param) => {js_refresh_page(param); return param;}"


print("Version of gradio: " + gr.__version__, flush=True)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=js, head=head_html) as demo:
    print("Creating the interface", flush=True)
    get_arguments()
    initialize_global_variables()
    print("*" * 50)
    print("Selected speaker: ", selected_speaker)
    print("*" * 50)

    page_state = gr.State("loaded", render=False)
    user_initial_message = "Hello, I am " + selected_speaker
    chatbot = gr.Chatbot(
        layout="bubble",
        bubble_full_width=False,
        elem_id = "chatbot",
        height="80vh",
        value = [(user_initial_message, welcome_message)],
        label = "Chatbot DeMINT",
        avatar_images = ("./public/user.png", "./public/logo_dark.png"),
        render=False,
    )
    hidden_textbox = gr.Textbox(value="", visible=False, render=True)

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
                        value=handle_dropdown_selection(selected_speaker)[0],
                        latex_delimiters=[], # Disable LaTeX rendering
                    )
                    dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text, chatbot, hidden_textbox])


        # Block for chatting with the AI.
        with gr.Column(scale=0.7, variant="default"):
            with gr.Group():
            # lg.primary.svelte-cmf5ev
                chatbot.render()
                with gr.Row(elem_id="option_buttons"):
                    option1 = gr.Button(
                        value="Option 1",
                        elem_id="option1",
                        scale=1,
                        elem_classes="option_button",
                    )
                    option2 = gr.Button(
                        value="Option 2",
                        elem_id="option2",
                        scale=1,
                        elem_classes="option_button",
                    )
                    option3 = gr.Button(
                        value="Option 3",
                        elem_id="option3",
                        scale=1,
                        elem_classes="option_button",
                    )
                    option4 = gr.Button(
                        value="Option 4",
                        elem_id="option4",
                        scale=1,
                        elem_classes="option_button",
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

            submit_button.click(chat_with_ai, [txtbox, chatbot], [txtbox, chatbot, hidden_textbox], show_progress="hidden") # js=js_toggle_visibility
            txtbox.submit(chat_with_ai, [txtbox, chatbot], [txtbox, chatbot, hidden_textbox], show_progress="hidden") # js=js_toggle_visibility
            chatbot.change(fn=None, inputs=[hidden_textbox], js=js_autoscroll_by_id) 

    # TODO
    demo.unload(reset_states)

if __name__ == '__main__':
    print("Launching the interface")
    is_public_link = True
    demo.launch(
        share=is_public_link,
        server_name="localhost",
        server_port=port,
        )
    