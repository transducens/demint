import time
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
import random
import os

from english_tutor import EnglishTutor
import app.prepare_sentences as prepare_sentences
import app.rag_sentences as rag_sentences
from app.file_manager import FileManager


available_llm = EnglishTutor.get_available_llm()
max_new_tokens = 200
rag_file = "cache/rag_sentences.json"


@cl.on_settings_update
async def setup_agent(settings):
    print("Settings update start...")
    english_tutor = cl.user_session.get("english_tutor")

    speakerId = settings["SpeakerId"]
    explained_sentences = cl.user_session.get("explained_sentences")

    explained_sentences_speaker = await get_explained_sentences_speaker(explained_sentences, speakerId)
    cl.user_session.set("explained_sentences_speaker", explained_sentences_speaker)

    await cl.Message(
        content=f"### Selected: {speakerId}",
    ).send()

    #current_LLM = settings["CurrentLLM"]
    #if english_tutor.get_current_llm_model_id() != current_LLM:
    #    print(f'LLM updated: {current_LLM}')
    #    english_tutor.set_chat_llm(current_LLM)

    print("on_settings_update", settings)

    await on_message(None)


# called when a new chat session is created.
@cl.on_chat_start
async def on_chat_start():
    hello_msg = f"# Welcome to English Tutor Chat Bot AI! 🚀🤖\n\n"
    hello_msg += f"Please select in configuration (left of the text entry) what speaker you want to check. Otherwise all speakers will be used\n\n"
    initial_message = cl.Message(content=hello_msg)
    await initial_message.send()

    start_chat = time.time()
    cl.user_session.set("counter", 0)
    english_tutor = EnglishTutor(llm_model_name = "gpt-4-turbo")
    explained_sentences, sentences_collection, speakers = await load_data()
    end_chat = time.time()
    print("on_chat_start time:", end_chat - start_chat)

    #english_tutor.set_chat_llm(available_llm[4])
    cl.user_session.set("english_tutor", english_tutor)

    await cl.ChatSettings(
        [
            Select(
                id="SpeakerId",
                label="Current Speaker",
                values=speakers,
                initial_index=0,
            ),
            #Select(
            #    id="CurrentLLM",
            #    label="Current model",
            #    values=available_llm,
            #    initial_index=0,
            #),
        ]
    ).send()

    # Loop how many times you can check some speaker
    for i in range(0,10):
    # Ask the user to select a speaker
        speaker = await ask_for_speaker()
        explained_sentences_speaker = await get_explained_sentences_speaker(explained_sentences, speaker)
        cl.user_session.set("explained_sentences_speaker", explained_sentences_speaker)


        # Start the conversation
        explained_sentences_speaker = cl.user_session.get("explained_sentences_speaker")
        # if the dictionary is empty, then the user has completed the exercise
        while not explained_sentences_speaker:
            await cl.Message(
                content="Congratulations! You don't have any mistakes to practice. Let's continue!",
            ).send()

            # Ask for another speaker
            speaker = await ask_for_speaker()
            explained_sentences_speaker = await get_explained_sentences_speaker(cl.user_session.get("explained_sentences"), speaker)
            cl.user_session.set("explained_sentences_speaker", explained_sentences_speaker)
        
        id_sentence = id_error = 0
        #errors_speaker = explained_sentences_speaker.items()

        cl.user_session.set("id_sentence", id_sentence)
        cl.user_session.set("id_error", id_error)
        cl.user_session.set("state", 0)

        await select_error()
        return



# called when a new message is received from the user.
@cl.on_message
async def on_message(message: cl.Message):
    english_tutor = cl.user_session.get("english_tutor")
    counter = cl.user_session.get("counter")
    error = cl.user_session.get("error")
    print(f'counter: {counter}')

    state = cl.user_session.get("state")

    if state == 0:
        # Step 2: Exercises
        msg = cl.Message(content='')
        await msg.send()

        response = await error_explanation()

        response += "\n\n **Do you want an extensive explanation of the English grammar of this case?**"

        msg.content = f"{response}"
        await msg.update()

        counter += 1
        cl.user_session.set("counter", counter)
        cl.user_session.set("state", 1)

    elif state == 1:
        print("Mensaje: ", message.content)
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()

        response = await ask_grammar(message.content)
        print(response)
        print("*****************")

        msg.content = f"{response}"
        await msg.update()

        counter += 1
        cl.user_session.set("counter", counter)

        response = response.lower()
        print("Previo: ", response)
        output = ""
        if response == 'yes':
            output = await explain_grammar()

            print("Gramatica: ", output)

            #msg.content = f"{response}"
            #await msg.update()
        
        #response = "\n\n **Do you want an example of the correct use of the grammar rules?**"
        output += "\n\n **Do you want an example of the correct use of the grammar rules?**"
        msg.content = f"{output}"
        await msg.update()

        cl.user_session.set("state", 2)

    elif state == 2:
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()

        #response = await correct_exercise(message.content)
        response = await ask_example(message.content)
        print(response)
        print("*****************")

        msg.content = f"{response}"
        await msg.update()

        msg.content = response
        await msg.update()

        response = response.lower()
        if response == 'yes':
            response = await create_example()

            msg.content = response
            await msg.update()
        
        response += "\n\n **Do you want an exercise to practice these grammar rules?**"
        msg.content = f"{response}"
        await msg.update()
        cl.user_session.set("state", 3)

    elif state == 3:
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()

        #response = await correct_exercise(message.content)
        response = await ask_exercise(message.content)
        print(response)
        print("*****************")

        msg.content = f"{response}"
        await msg.update()

        response = response.lower()
        if response == 'yes':
            response = await create_exercise()
            response += "\n\n **Complete the exercise**"

            msg.content = f"Here is an exercise in order to you to practise:\n{response}"
            await msg.update()
            cl.user_session.set("state", 4)
        else:
            response += "\n\n **Do you want to attempt to write the sentence correctly?**"
            msg.content = f"{response}"
            await msg.update()
            cl.user_session.set("state", 5)
    elif state == 4:
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()

        #response = await correct_exercise(message.content)
        response = await correct_exercise(message.content)

        response += "\n\n **Do you want another exercise to practice these grammar rules?**"

        msg.content = f"{response}"
        await msg.update()

        cl.user_session.set("state", 3)
    elif state == 5:
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()

        response = await ask_sentence(message.content)

        msg.content = f"{response}"
        await msg.update()

        counter += 1
        cl.user_session.set("counter", counter)

        response = response.lower()
        if response == 'yes':
            cl.user_session.set("state", 6)
        else:
            cl.user_session.set("state", 0)
            await select_error()
    elif state == 6:
        # TODO continue asking for exercises until the user has completed 3 exercises
        msg = cl.Message(content='')
        await msg.send()
        
        response = await check_corrected(message.content)
        print(response)
        print("*****************")

        msg.content = f"{response}"
        await msg.update()

        cl.user_session.set("state", 0)
        await select_error()

async def ask_action():
    return await cl.AskActionMessage(
        content="Make a decision",
        actions=[
            cl.Action(name="cancel", value="cancel", label="❌ No, thank you..."),
            cl.Action(name="continue", value="continue", label="✅ Yes, please!"),
        ],
    ).send()

async def ask_for_speaker():
    speakers = cl.user_session.get("speakers")
    res = await cl.AskActionMessage(
        content="Choose the speaker you want to analyse",
        actions=[
            *[cl.Action(name=speaker, value=speaker, label=speaker) for speaker in speakers],
        ],
    ).send()

    if res:
        return res.get("value")
    else:
        return "All speakers"


# Returns a list of all the speakers that have spoken in the transctipt
async def get_speakers(sentences_collection):
    sorted_speakers = []
    if sentences_collection is not None:
        sorted_speakers.append("All speakers")
        # Get the speakers names
        sorted_speakers += sorted( {value['speaker'] for value in sentences_collection.values()} )
    
    return sorted_speakers


async def get_explained_sentences_speaker(explained_sentences, speaker:str):
    if speaker == "All speakers":
        return explained_sentences
    else:
        result = {}
        for key, value in explained_sentences.items():
            if value['speaker'] == speaker:
                result[key] = value
        return result
    

async def load_data():
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
    cl.user_session.set("explained_sentences", explained_sentences)
    sentences_collection = file_manager.read_from_json_file(input_files['sentences_collection'])
    cl.user_session.set("sentences_collection", sentences_collection)
    speakers = await get_speakers(sentences_collection)
    cl.user_session.set("speakers", speakers)
    cl.user_session.set("explained_sentences_speaker", explained_sentences)

    end_load = time.time()
    print("**************************************")
    print("Load data time:", end_load - start_load)
    print("**************************************")

    return explained_sentences, sentences_collection, speakers

async def create_context():
    errant = cl.user_session.get("error")

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

async def error_explanation():
    english_tutor = cl.user_session.get("english_tutor")

    context = await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create a short explanation of the gramatical error using the mistake description provided in the context and alaways on the student phrase without saying the correct one.")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def ask_sentence(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += cl.user_session.get("user_excercise")

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants to attempt to write the sentence correctly. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    print("Respuesta: ", response)
    """
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    """
    print("JEJEJ: ", response)
    response = response.split('>')[1].split('<')[0]

    cl.user_session.set("user_excercise", response)

    return response

async def ask_exercise(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += cl.user_session.get("user_excercise")

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an exercise in order to practice. Determine if the students wants to try based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    print("Respuesta: ", response)
    """
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    """
    response = response.split('>')[1].split('<')[0]

    cl.user_session.set("user_excercise", response)

    return response

async def ask_grammar(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += cl.user_session.get("user_excercise")

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an extensive explanation of english grammar. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    print("Respuesta: ", response)

    """
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    """
    response = response.split('>')[1].split('<')[0]

    cl.user_session.set("user_excercise", response)

    return response

async def ask_example(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    # Step 3: Check user answer, explain result and create new exercise
    context = "You ask the student: \n"
    context += cl.user_session.get("user_excercise")

    context += "\n\nThe student responce is the following:\n"
    context += "\n\n" + student_response + "\n"

    final_prompt = (f"Base on the following context:\n\n"
                    f"CONTEXT:\n{context}"
                    f"TASK:\n You have asked the student if he wants an example of the sentence. Determine if the students wants it based of the following answer. Please enclose 'yes' or 'no' in your answer in <asnwer></answer> tags.\n\n"
                    f"ANSWER:\n{student_response}")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    print("Respuesta: ", response)

    """
    final_prompt = (f"Base on the following sentence:\n\n"
                    f"SENTENCE:\n{response}"
                    f"TASK:\n Your output must be the sentence enclosing 'yes' or 'no' words in the sentence in <asnwer></answer> tags.\n\n")
    
    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    """
    response = response.split('>')[1].split('<')[0]

    cl.user_session.set("user_excercise", response)

    return response

async def check_corrected(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    context = await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to correct the mistakes I have made based on the following context: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Based on the student answer, check if his sentence is correct comparing it to corrected sentece provided in the context. If it is corrrect, tell the student he did well. In case it is not correct, tell the student which mistakes he has made including new errors not previously made."
        f"ANSWER:\n{student_response}\n")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def create_exercise():
    english_tutor = cl.user_session.get("english_tutor")

    context = await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create an exercise of English base on the english rules and mistake description provided in the context in order to me to practice.")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def correct_exercise(student_response):
    english_tutor = cl.user_session.get("english_tutor")

    context = "The exercise propose to the student: \n"
    context += cl.user_session.get("user_excercise")

    context += "\n\nThe student answer:\n"
    context += "\n\n" + student_response + "\n"
    
    context += await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Base on the exercise propose to the student, correct his answer using if needed the english rules provided in the context"
        f"ANSWER:\n{student_response}")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def explain_grammar():
    english_tutor = cl.user_session.get("english_tutor")

    context = await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Give an extended explanation of the english grammar rules present in the context.")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def create_example():
    english_tutor = cl.user_session.get("english_tutor")

    context = await create_context()
        
    final_prompt = (
        f"You are an English teacher. I want you to help me learn English: \n\n"
        f"CONTEXT:\n{context}\n"
        f"TASK:\n Create an example for the correct use of the english grammar rul provided in the context. Try to be original")

    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)
    
    return response

async def select_error():
    print("selecting error")
    explained_sentences_speaker = cl.user_session.get("explained_sentences_speaker")
    
    id_sentence = cl.user_session.get("id_sentence")
    id_error = cl.user_session.get("id_error")
    
    #errors_speaker = explained_sentences_speaker.items()
    errors_speaker = list(explained_sentences_speaker.values())

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
            await cl.Message(
                content=text,
            ).send()
            go_check_error = await ask_action()
                
            if go_check_error["value"] == "cancel":
                id_error += 1
            else:
                # Step 2: Exercises
                cl.user_session.set("error", error)

                cl.user_session.set("id_sentence", id_sentence)
                cl.user_session.set("id_error", id_error)
                selected = True

                await on_message(None)
                break

        id_sentence += 1
        id_error = 0

    return