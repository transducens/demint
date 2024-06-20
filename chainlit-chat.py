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
    english_tutor = EnglishTutor()
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
            
        

        #Step 1: Select a sentence to practice
        for sentence_id, explained_sentence in explained_sentences_speaker.items():
            errant_errors = explained_sentence['errant']
            for error in errant_errors:
                # Highlight the error and correction in the sentence
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

                highlighted_corrected_sentence = highlight_word_in_sentence(
                    corrected_sentence, error["c_start"], error["c_end"],
                    error["corrected_text"] if error["corrected_text"] else f'~~{error["original_text"]}~~'
                )

                text = "**You've made mistake in the following sentence:**\n\n*" + highlighted_original_sentence + "*\n\n"
                text += "**It's corrected sentence:**\n\n*" + highlighted_corrected_sentence + "*\n\n"
                text += error["llm_explanation"] + "\n\n"
                text += "Do you want to practice the error?"

                # Ask if wanna study that error with exercises
                await cl.Message(
                    content=text,
                ).send()
                go_check_error = await ask_action()
                
                if go_check_error["value"] == "cancel":
                    continue
                else:
                    # Step 2: Exercises
                    cl.user_session.set("error", error)
                    await on_message(None)

        # Ended checking errors for that speaker
        msg = cl.Message(content="You have completed the exercises. Let's continue!")
        await msg.send()



# called when a new message is received from the user.
@cl.on_message
async def on_message(message: cl.Message):
    english_tutor = cl.user_session.get("english_tutor")
    counter = cl.user_session.get("counter")
    error = cl.user_session.get("error")
    print(f'counter: {counter}')

    # Step 2: Exercises
    msg = cl.Message(content='')
    await msg.send()

    # selected_speaker_text = cl.user_session.get("selected_speaker_text")
    mistake_description = error['llm_explanation']
    RAG_context = error['rag']

    content_list = [f'{item["content"]}' for item in RAG_context]
    context_str = "\n----------\n".join(content_list)

    context = "\n\nThe English rule:\n"
    context += "\n\n" + context_str + "\n"

    context += "\n\nMistake description: \n"
    context += mistake_description

    final_prompt = (
        f"You are an English teacher talking to a student. \n\n"
        f"CONTEXT:\n{context}\n"
        f"QUESTION:\n Create an short exercise to help a student practice their mistake. Without answers.")

    # Generate exercise number 1
    response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    cl.user_session.set("user_excercise", response)

    counter += 1
    cl.user_session.set("counter", counter)

    # TODO continue asking for exercises until the user has completed 3 exercises
    msg = cl.Message(content='')
    await msg.send()

    # Step 3: Check user answer, explain result and create new exercise
    context = "The current exersice is: \n"
    context += cl.user_session.get("user_excercise")

    # Ask user for anser to exercise
    user_response = await cl.AskUserMessage(
        content=("Write your answer to the exercise below\n\n"),
        timeout=180,
    ).send()
    if user_response:
        await cl.Message(
            content=f"Your answer: {user_response['output']}",
        ).send()

    # TODO Create correction for the answer of the user to exercise 1

    # Follow with more exercises
    #context += "\n\n" + message.content + "\n"
#
    #final_prompt = (f"Check user answer, explain result and create new exercise:\n\n"
    #                f"CONTEXT:\n{context}"
    #                f"QUESTION:\n Check my answer, explain result and create new exercise without answers.")
#
    #response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
    #cl.user_session.set("user_excercise", response)

    
    #response += "\n\n**You have completed the exercise. Let\'s continue!**"
    #cl.user_session.set("counter", 0)

    msg.content = f"{response}"

    await msg.update()

    

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