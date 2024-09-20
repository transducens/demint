import gradio as gr
import tracemalloc
import time
import os
import argparse

from english_tutor import EnglishTutor
from app.file_manager import FileManager
import app.prepare_sentences as prepare_sentences
import app.rag_sentences as rag_sentences
from app.teacher_model import TeacherModel

english_tutor: EnglishTutor | None = None
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
        english_tutor = EnglishTutor()
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

    load_data() # Load the data from the cache files

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

def chat_with_ai(user_input, history):
    global user_message, chat_answer, history_chat, highlighted_sentence_id, state
    global category_list, category_errors, index_category, index_error, count, log_conversation, chat_response, state_change
  
    user_message = user_input
    history_chat = history
    final_prompt = None

    output = ""

    match state:
        case -1:
            categories = list(category_list.keys())

            if index_category >= len(categories):
                state = 100
                output = "No more errors left to check. You have complete the class."
            else:
                category = categories[index_category]
                list_tuples = category_errors[category]
                if index_error >= len(list_tuples):
                    index_category += 1
                    index_error = 0

                    if index_category >= len(categories):
                        state = 100
                        output = "No more error categories left to check. You have complete the class."
                        return "", history, ""
                
                tuple_error = list_tuples[index_error]
                #highlighted_sentence_id = tuple_error[0]
                        
                incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])

                prompt = (f"Base on the following context:\n\n"
                          f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                          f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                          f"EXPLANATION:\n{explanation}\n\n"
                          f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
            
                response = create_prompt([prompt])
                output = "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                output += response + "\n\n"

                chat_response = "Do you want to practice this error?"
                output += f"\n\n **{chat_response}**"
                state = 0

        case 0:
            context = "You ask the student: \n"
            context += chat_response

            context += "\n\nThe student responce is the following:\n"
            context += "\n\n" + user_input + "\n"

            prompt = (f"Base on the following context:\n\n"
                        f"CONTEXT:\n{context}"
                        f"TASK:\n You have asked the student if he wants to check his english errors of an expecific category. Determine if the students wants it based of the following answer. Your answer must be 'yes' or 'no'.\n\n"
                        f"ANSWER:\n{user_input}")
                        
            output = create_prompt([prompt])

            if english_tutor.get_chat_llm()[:3] != 'gpt':
                output = sentiment_analisys(output)

            output = output.lower()
            if output == 'yes':
                #response = error_explanation()
                context = create_context(history, "I want a short explanation of the gramatical error")
            
                final_prompt = (
                    f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
                    f"CONTEXT:\n{context}\n"
                    f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.")

                response = create_prompt([final_prompt])
                chat_response = "What do you want to do next?"
                response += f"\n\n **{chat_response}**"
                output = response
                state = 1
            else:
                index_error += 1

                categories = list(category_list.keys())
                category = list(category_list.keys())[index_category]
                list_tuples = category_errors[category]

                if index_error >= len(list_tuples):
                    index_category += 1
                    index_error = 0

                    if index_category >= len(categories):
                        state = 100
                        output = "No more error categories left to check. You have complete the class."
                        return "", history, ""
                
                tuple_error = list_tuples[index_error]

                incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])

                prompt = (f"Base on the following context:\n\n"
                          f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                          f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                          f"EXPLANATION:\n{explanation}\n\n"
                          f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
            
                response = create_prompt([prompt])
                output = "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                output += response + "\n\n"

                chat_response = "Do you want to practice this other error?"
                output += f"\n\n **{chat_response}**"
                state = 0
        case 1:
            output = new_new_change_state(user_input, history)
            print(output)
            print(type(output))
            print(output.split('"'))
            next_id = output.split('"')[3]
            output = output.split('"')[7]

            if next_id == 'i2' or next_id == 'i3' or next_id == 'i4' or count == 6:
                if count == 6:
                    output += "\nI think we can move to the next exercise.\n"

                count = 0
                history = list()
                categories = list(category_list.keys())

                if index_category >= len(categories):
                    state = 100
                    output += "No more errors left to check. You have complete the class."
                else:
                    category = categories[index_category]
                    list_tuples = category_errors[category]
                    if index_error >= len(list_tuples):
                        index_category += 1
                        index_error = 0

                        if index_category >= len(categories):
                            state = 100
                            output += "No more error categories left to check. You have complete the class."
                            return "", history, ""
                
                    tuple_error = list_tuples[index_error]
                    #highlighted_sentence_id = tuple_error[0]
                        
                    incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])

                    prompt = (f"Base on the following context:\n\n"
                              f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                              f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                              f"EXPLANATION:\n{explanation}\n\n"
                              f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
            
                    response = create_prompt([prompt])
                    output += "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                    output += response + "\n\n"

                    chat_response = "Do you want to practice this error?"
                    output += f"\n\n **{chat_response}**"
                    state = 0
            else:
                count += 1
        case _:
            output = "No more error categories left to check. You have complete the class."

    if highlighted_sentence_id == 1:
        error_sentence_id = ""
    else:
        error_sentence_id = "sentence_" + str(highlighted_sentence_id)

    history.append((user_input, output))   # must be Tuples
    
    if log_conversation:
        log_conversation_item(user_input, output)

        if final_prompt != None:
            log_prompts(final_prompt, output)

    return "", history, error_sentence_id   

# Chat with the AI using the given query.
def chat_with_ai_obsoleto(user_input, history):
    global user_message, chat_answer, history_chat, highlighted_sentence_id, state
    global category_list, category_errors, index_category, index_error, count, log_conversation, chat_response, state_change
  
    user_message = user_input
    history_chat = history
    final_prompt = None

    output = ""
    
    match state:
        case -1:
            category = list(category_list.keys())[index_category]
            output = "Most frecuent error type: " + category + ". Want to practice it?"
            state = 0
        case 0:
            #output = ask_error(user_input)
            context = "You ask the student: \n"
            context += chat_response

            context += "\n\nThe student responce is the following:\n"
            context += "\n\n" + user_input + "\n"

            prompt = (f"Base on the following context:\n\n"
                        f"CONTEXT:\n{context}"
                        f"TASK:\n You have asked the student if he wants to check his english errors of an expecific category. Determine if the students wants it based of the following answer. Your answer must be 'yes' or 'no'.\n\n"
                        f"ANSWER:\n{user_input}")

            output = create_prompt([prompt])

            if english_tutor.get_chat_llm()[:3] != 'gpt':
                output = sentiment_analisys(output)

            output = output.lower()
            if output == 'yes':
                categories = list(category_list.keys())

                if index_category >= len(categories):
                    state = 100
                    output = "No more error categories left to check. You have complete the class."
                else:
                    category = categories[index_category]
                    list_tuples = category_errors[category]
                    if index_error >= len(list_tuples):
                        index_category += 1
                        index_error = 0

                        if index_category >= len(categories):
                            state = 100
                            output = "No more error categories left to check. You have complete the class."
                        else:
                            category = categories[index_category]
                            output = "Most frecuent error type: " + category + ". Want to practice it?"
                            state = 0
                    else:
                        tuple_error = list_tuples[index_error]
                        #highlighted_sentence_id = tuple_error[0]
                        
                        incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])

                        prompt = (f"Base on the following context:\n\n"
                                    f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                                    f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                                    f"EXPLANATION:\n{explanation}\n\n"
                                    f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
            
                        response = create_prompt([prompt])
                        output = "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                        output += response + "\n\n"

                        chat_response = "Do you want to practice this error?"
                        output += f"\n\n **{chat_response}**"
                        state = 1
            else:
                index_category += 1
                categories = list(category_list.keys())

                if index_category >= len(categories):
                    state = 100
                    output = "No more error categories left to check. You have complete the class."
                else:
                    category = categories[index_category]
                    output = "Most frecuent error type: " + category + ". Want to practice it?"
        case 1:
            #output = ask_error(user_input)
            context = "You ask the student: \n"
            context += chat_response

            context += "\n\nThe student responce is the following:\n"
            context += "\n\n" + user_input + "\n"

            prompt = (f"Base on the following context:\n\n"
                        f"CONTEXT:\n{context}"
                        f"TASK:\n You have asked the student if he wants to check his english errors of an expecific category. Determine if the students wants it based of the following answer. Your answer must be 'yes' or 'no'.\n\n"
                        f"ANSWER:\n{user_input}")
                        
            output = create_prompt([prompt])

            if english_tutor.get_chat_llm()[:3] != 'gpt':
                output = sentiment_analisys(output)

            output = output.lower()
            if output == 'yes':
                #response = error_explanation()
                context = create_context(history, "I want a short explanation of the gramatical error")
            
                final_prompt = (
                    f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
                    f"CONTEXT:\n{context}\n"
                    f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.")

                response = create_prompt([final_prompt])
                chat_response = "What do you want to do next?"
                response += f"\n\n **{chat_response}**"
                output = response
                state = 3
            else:
                index_error += 1

                categories = list(category_list.keys())
                category = list(category_list.keys())[index_category]
                list_tuples = category_errors[category]

                if index_error >= len(list_tuples):
                    index_category += 1
                    index_error = 0

                    if index_category >= len(categories):
                        state = 100
                        output = "No more error categories left to check. You have complete the class."
                    else:
                        category = categories[index_category]
                        output = "Most frecuent error type: " + category + ". Want to practice it?"
                        state = 0
                else:
                    tuple_error = list_tuples[index_error]

                    incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])

                    prompt = (f"Base on the following context:\n\n"
                              f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                              f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                              f"EXPLANATION:\n{explanation}\n\n"
                              f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
            
                    response = create_prompt([prompt])
                    output = "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                    output += response + "\n\n"

                    chat_response = "Do you want to practice this other error?"
                    output += f"\n\n **{chat_response}**"
        case 3:
            output = new_change_state(user_input, history)

            if output == '2':
                output = '1'

            match int(output):
                case 1:
                    categories = list(category_list.keys())
                    category = categories[index_category]
                    list_tuples = category_errors[category]
                    index_error += 1

                    if index_error >= len(list_tuples):
                        index_category += 1
                        index_error = 0

                        if index_category >= len(categories):
                            state = 100
                            output += "No more error categories left to check. You have complete the class."
                        else:
                            category = categories[index_category]
                            output += "Most frecuent error type: " + category + ". Want to practice it?"
                            state = 0
                    else:
                        tuple_error = list_tuples[index_error]

                        incorrect_sentence, correct_sentence, explanation = select_error(tuple_error[0], tuple_error[1])
                        
                        prompt = (f"Base on the following context:\n\n"
                                  f"INCORRECT SENTENCE:\n{incorrect_sentence}\n\n"
                                  f"CORRECT SENTENCE:\n{correct_sentence}\n\n"
                                  f"EXPLANATION:\n{explanation}\n\n"
                                  f"TASK:\n Base on the incorrect and correct sentences, explain briefly the error using the explanation provided. The word or words that form part of the error are located between brackets Bear in mind that the explanation might be inaccurate. In those cases do nnot use it. Do not make any reference to the correct sentence\n\n")
                        response = create_prompt([prompt])
                        output = "**You've made a mistake in the following sentence:**\n\n*" + incorrect_sentence + "*\n\n"
                        output += response + "\n\n"

                        chat_response = "Do you want to practice this other error?"
                        output += f"\n\n **{chat_response}**"
                        state = 1
                case 3:
                    context = create_context(history, user_input)
            
                    final_prompt = (
                        f"You are an English teacher. I want you to help me learn English: \n\n"
                        f"CONTEXT:\n{context}\n"
                        f"TASK:\n Give an extended explanation of the english grammar rules present in the context. Do not make any reference to the corrected sentence.")
                    
                    output = create_prompt([final_prompt])
                case 4:
                    context = create_context(history, user_input)
            
                    final_prompt = (
                        f"You are an English teacher. I want you to help me learn English: \n\n"
                        f"CONTEXT:\n{context}\n"
                        f"TASK:\n Create an example for the correct use of the english grammar rules provided in the context. Try to be original and do not make any reference to the corrected sentence.")
                    
                    output = create_prompt([final_prompt])
                case 5:
                    context = create_context(history, user_input)
            
                    final_prompt = (
                        f"You are an English teacher. I want you to help me learn English: \n\n"
                        f"CONTEXT:\n{context}\n"
                        f"QUESTION:\n Create an simple exercise of English base on the english rules and mistake description provided in the context in order to me to practice. The exercise must be just a simple sentence for the student to complete. Do not show the answer.")

                    output = create_prompt([final_prompt])

                    output += "\n\n **Complete the exercise**"
                    output = f"Here is an exercise in order to you to practice:\n{output}"
                    state = 4
                case 6:
                    output += "\n\n **Write down the correct sentence**"
                    state = 5
                case 7:
                    context = create_context(history, user_input)

                    final_prompt = (
                        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
                        f"CONTEXT:\n{context}\n"
                        f"TASK:\n Based on the question I gave you, answer it in a simple way and always in the context of english teaching. If the question is not english related, you cannot help the student and you must remind the student that you are an English professor that only answers english related questions."
                        f"QUESTION:\n{user_input}. Remember that you are an English teacher.\n")
                    
                    output = create_prompt([final_prompt])
        case 4:
            context = "The exercise propose to the student: \n"
            context += chat_answer

            context += "\n\nThe student answer:\n"
            context += "\n\n" + user_input + "\n"
            
            context += create_context(history, user_input)
                
            final_prompt = (
                f"You are an English teacher. I want you to help me learn English: \n\n"
                f"CONTEXT:\n{context}\n"
                f"QUESTION:\n Base on the exercise propose to the student, correct his answer using if needed the english rules provided in the context"
                f"ANSWER:\n{user_input}")
            
            output = create_prompt([final_prompt])
            state = 3
        case 5:
            context = create_context(history, user_input)
            
            final_prompt = (
                f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
                f"CONTEXT:\n{context}\n"
                f"TASK:\n Based on the student answer, check if his sentence is correct comparing it to corrected sentece provided in the context. If it is corrrect, tell the student he did well. In case it is not correct, tell the student which mistakes he has made including new errors not previously made."
                f"ANSWER:\n{user_input}\n")
            
            output = create_prompt([final_prompt])
            state = 3
        case _:
            output = "No more error categories left to check. You have complete the class."

    if highlighted_sentence_id == 1:
        error_sentence_id = ""
    else:
        error_sentence_id = "sentence_" + str(highlighted_sentence_id)

    history.append((user_input, output))   # must be Tuples
    
    if log_conversation:
        log_conversation_item(user_input, output)

        if final_prompt != None:
            log_prompts(final_prompt, output)

    return "", history, error_sentence_id

def log_conversation_item(user_input, bot_response):
    global new_conversation
    file_manager = FileManager()
    filename = f"log/conversation_{conversation_name}_{selected_speaker}.json"
    item = {"user": user_input, "assistant": bot_response}

    if not os.path.exists(filename):
        new_conversation = False
        file_manager.save_to_json_file(filename, [ {"conversation": [item]} ])
        
    else:
        if new_conversation:
            # Create a new conversation
            new_conversation = False
            saved_data = file_manager.read_from_json_file(filename)
            saved_data.append( {"conversation": [item]} )
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
    item = {"prompt": prompt, "response": response}

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
    print("Called handle_dropdown_selection")
    return build_transcript(speaker_name)

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
    parser = argparse.ArgumentParser(description="English Tutor")

    parser.add_argument("--conver", required=True, type=str, help="The transcripted conversation to show. Default is diarization_result")
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

    # arguments = {
    #     "speaker": args.speaker,
    #     "conver": args.conver,
    #     "port": args.port,
    #     "log": args.log
    # }

    # return arguments

def create_context(history, user_input):
    global error
    #errant = cl.user_session.get("error")
    errant = error

    mistake_description = errant['llm_explanation']
    RAG_context = errant['rag']

    content_list = [f'{item["content"]}' for item in RAG_context]
    context_str = "\n----------\n".join(content_list)

    #context = "\n\nConversation History:\n"
    #context += "\n\n" + str(history) + "\n"

    context = "\n\nIncorrect Sentence:\n"
    context += "\n\n" + errant["original_sentence"] + "\n"

    context += "\n\Correct Sentence:\n"
    context += "\n\n" + errant["corrected_sentence"] + "\n"

    context += "\n\nThe English rule:\n"
    context += "\n\n" + context_str + "\n"

    context += "\n\nMistake description: \n"
    context += mistake_description

    if teacher_model != None:
        list_history = history.copy()
        list_history.append((user_input))
        kind_teacher_prompt = teacher_model.format_messages(list_history)
        kind_teacher_response = teacher_model.get_response(kind_teacher_prompt)
        kind_teacher_response = teacher_model.format_response(kind_teacher_response)
        
        context += "\n\nA teacher would respond in the following way. Only use this if the teacher response is related to the current topic:\n"
        context += "\n\n" + kind_teacher_response + "\n" 

    return context

def create_prompt(prompts):
    prompt = ""
    for x in prompts:
        prompt += x

    response = english_tutor.get_answer(prompt, max_new_tokens)

    return response

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

    prompt = "You are an English tutoring chatbot that helps non-native speakers analyze grammatical errors in sentences and correct them. Your goal is to help the user understand their mistakes, practice correcting the sentence with the error or other sentences with similar errors posed as exercises, and provide guidance based on various sources. The text that will be analyzed results from the transcription of a speech conversation between the user and other humans; therefore it may contain informal language. Your focus should be on the grammatical errors and not on the informal aspects of the conversation or the potential presence of incomplete sentences.\n\n"
    prompt += "There are specific intentions that the user might express during the interaction as indicated below. Each intention is represented by an id such as I1 that you will use later to identify the user's intention.\n"
    prompt += "I1. The user wants to do an exercise where they correct a sentence with a similar error.\n"
    prompt += "I2. The user wants to move on to the next error.\n"
    prompt += "I3. The user does not understand the error and needs an additional explanation.\n"
    prompt += "I4. The user has understood everything.\n"
    prompt += "I5. The user wants to try writing the correct form of their erroneous sentence so that you can evaluate it.\n"
    prompt += "I6. The user has an intention related to the conversation, requiring a response in context.\n"
    prompt += "I7. The user has an unrelated intention, and you should gently remind them to stay on topic.\n"
    prompt += "I8. The user is giving the answer to an exercise you proposed.\n\n"
    prompt += "Your task is to identify the user's intention based on their input and respond appropriately. You are provided next with some information on the error that may help you generate responses. Although this information may be relevant in some cases, it may be inaccurate in others. Therefore, it is not mandatory that you use all the information provided.\n"
    prompt += "The information on the error obtained from different sources is:\n"
    prompt += f"- Error type as identified by the tool ERRANT: {error_type}\n"
    prompt += f"- Explanation of the error given by an AI model: {mistake_description}\n"
    #prompt += f"- Explanation of the error given by a grammar checker model: {grammar_checker_explanation}\n"
    prompt += f"- Potential relevant passages from English textbooks (retrieved via RAG): {context_str}\n"
    prompt += f"- The last few turns of the conversation excluding the last user turn: {history}\n"
    prompt += f"- The last turn of the conversation: {user_response}\n"

    if teacher_model != None:
        prompt += f"- A suggestion for the teacher's response given by a AI teacher model with no specific knowledge of English learning: {teacher_suggestion}\n"
    
    prompt += "### Instructions for response generation:\n"
    prompt += "1. Identify the user's intention.\n"
    prompt += "If the intention is:\n"
    prompt += f"- **I1**: Create a short simple English sentence with an error similar to the one the user made. Guide the user to attempt correcting {exercise_sentence} in your response.\n"
    prompt += "- **I2**: Confirm their understanding and offer to analyze the next error.\n"
    prompt += "- **I3**: Provide a detailed explanation using the provided information and your own knowledge of English grammar. Make sure you do not provide the correct sentence as part of the explanation as the user should try to correct it themselves. Ask then the user if they want to practice or move on to another error.\n"
    prompt += "- **I4**: Acknowledge their understanding and tell them that you are ready to move on to the next error.\n"
    prompt += "- **I5**: Ask the user to provide the correct form of their erroneous sentence.\n"
    prompt += "- **I6**: Respond contextually using the provided information.\n"
    prompt += "- **I7**: Politely remind the user to focus on the session and offer options related to language learning: practice, explanation, or moving on to the next error.\n"
    prompt += "- **I8**: Evaluate the user's response according to your proposed exercise and provide feedback.\n"
    prompt += "3. Always try to consider the user's intention and the provided context when generating responses. However, you can also exceptionally generate responses that do not directly use the provided information if you think they are more appropriate for the situation.\n"
    prompt += "4. Make your responses sound natural and engaging to the user, but at the same time, be clear and concise in your explanations. Generate responses between 1 and 5 sentences long.\n"
    prompt += "5. There is a sequence of interactions with the user that you should try to follow: explain the error, practice with other sentences, and get a correct sentence from the user. However, you can skip some steps if you think they are not necessary for the user's learning process.\n\n"
    prompt += "Generate both the identified intention and the next response to the user in a structured JSON format like this:"
    prompt += "{\n"
    prompt += "intention: INTENTION_ID,\n"
    prompt += "response: GENERATED_RESPONSE\n"
    prompt += "}"

    response = english_tutor.get_answer(prompt, max_new_tokens).lower() 
    return response

def new_change_state(user_response, history):
    prompt = "The context of the conversation is the following\n" + str(history) + "\n"
    prompt += "The student lattest response is:\n" + user_response + "\n"
    prompt += "Base on the context provided and the student response, determine the intencion of the student from this list:\n"
    prompt += "1- Understands the error: This is when the student does not have more doubts and whants to continue with the next error\n"
    prompt += "2- Request the next error: This is when the student wants to pass directly to the next error\n"
    prompt += "3- Does not understant the error: This is when the student still has some doubts about the current error\n"
    prompt += "4- Request an example: This is when the student wants an example of the current error\n"
    prompt += "5- Request an exercise: This is when the student wants an exercise of the current error\n"
    prompt += "6- Attemps to correct sentence: This is when the student wants to make an attempt at writting the sentence without the error"
    prompt += "7- None of the above: This is when the student response does not correspond with any of the intencions that where mention before\n"
    prompt += "If there are multiple options in the list that fit the description, only pick the first one\n"
    prompt += "Your answer must be only the number of the list"

    response = english_tutor.get_answer(prompt, max_new_tokens).lower()
    return response

def sentiment_analisys(response):
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
        
    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    response = response.split('>')[1].split('<')[0]

    return response

def error_explanation(history):
    context = create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    return response

def ask_error(student_response):
    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += chat_response

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants to check his english errors of an expecific category. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    if english_tutor.get_chat_llm()[:3] != 'gpt':
        final_prompt = (f"Base on the following sentence:\n\n"
                        f"SENTENCE:\n{response}"
                        f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
        
        response = english_tutor.get_answer(final_prompt, max_new_tokens)
        response = response.split('>')[1].split('<')[0]

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

    if english_tutor.get_chat_llm()[:3] != 'gpt':
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

    if english_tutor.get_chat_llm()[:3] != 'gpt':    
        final_prompt = (f"Base on the following sentence:\n\n"
                        f"SENTENCE:\n{response}"
                        f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
        
        response = english_tutor.get_answer(final_prompt, max_new_tokens)
        response = response.split('>')[1].split('<')[0]

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
    
    if english_tutor.get_chat_llm()[:3] != 'gpt':
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
    
    if english_tutor.get_chat_llm()[:3] != 'gpt':
        final_prompt = (f"Base on the following sentence:\n\n"
                        f"SENTENCE:\n{response}"
                        f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
        
        response = english_tutor.get_answer(final_prompt, max_new_tokens)
        response = response.split('>')[1].split('<')[0]

    return response

def explain_grammar(history):
    #english_tutor = cl.user_session.get("english_tutor")

    context = create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Give an extended explanation of the english grammar rules present in the context.")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    #cl.user_session.set("user_excercise", response)
    
    return response

def create_exercise(history):
    context = create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create an exercise of English base on the english rules and mistake description provided in the context in order to me to practice.")

    response =  english_tutor.get_answer(final_prompt, max_new_tokens)
    chat_answer = response
    #cl.user_session.set("user_excercise", response)
    
    return response

def correct_exercise(student_response, history):
    context = "The exercise propose to the student: \n"
    context += chat_answer

    context += "\n\nThe student answer:\n"
    context += "\n\n" + student_response + "\n"
    
    context += create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Base on the exercise propose to the student, correct his answer using if needed the english rules provided in the context"
        f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def create_example(history):
    context = create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Create an example for the correct use of the english grammar rul provided in the context. Try to be original")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def check_corrected(student_response, history):
    context = create_context(history)
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Based on the student answer, check if his sentence is correct comparing it to corrected sentece provided in the context. If it is corrrect, tell the student he did well. In case it is not correct, tell the student which mistakes he has made including new errors not previously made."
        f"ANSWER:\n{student_response}\n")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    return response

def answer_question(student_response, history):
    context = create_context(history)

    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Based on the question I gave you, answer it in a simple way and always in the context of english teaching. If the question is not english related, you cannot help the student and you must remind the student that you are an English professor that only answers english related questions."
        f"QUESTION:\n{student_response}. Remember you are an English teacher.\n")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)

    return response

def safe_guard(student_response):

    final_prompt = (f"You are an English teacher. You are helping me learn english"
                    f"TASK:\n I, the student, have made you a question. Determine if the question is related to the english as a learning subject. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)
    
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")

    response = english_tutor.get_answer(final_prompt, max_new_tokens)

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

    state = -1
    index_category = 0
    index_error = 0

js = "./app/gradio_javascript.js"
css = "./app/gradio_css.css"
head_html = ""
with open("./app/gradio_head_html.html", 'r') as file:
    head_html = file.read()

js_autoscroll_by_id = "(sentence_id) => {js_autoscroll_by_id(sentence_id);}"
js_toggle_visibility = "(msg, hist, htxt) => {js_toggle_visibility(); return [msg, hist];}"


print("Version of gradio: " + gr.__version__)
# Create the Gradio interface.
with gr.Blocks(fill_height=True, theme=gr.themes.Base(), css=css, js=js, head=head_html) as demo:
    print("Creating the interface")
    get_arguments()
    initialize_global_variables()
    print("*" * 50)
    print("Selected speaker: ", selected_speaker)
    print("*" * 50)

    page_state = gr.State("loaded", render=False)

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
                user_initial_message = "Hello, I am " + selected_speaker
                welcome_message = "Hello! I am your English tutor. I will help you to learn English. Are you ready?"
                chatbot = gr.Chatbot(
                    layout="bubble",
                    bubble_full_width=False,
                    elem_id = "chatbot",
                    height="80vh",
                    value = [(user_initial_message, welcome_message)],
                    label = "Chatbot DeMINT",
                    avatar_images = ("./public/user.png", "./public/logo_dark.png"),
                )
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
            hidden_textbox = gr.Textbox(value="", visible=False, render=True)

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
    