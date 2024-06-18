import time
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
import random
import os


from english_tutor import EnglishTutor

from app.error_identification import prepare_sorted_sentence_collection, explain_sentences, obtain_errors, rag_sentences
from app.file_manager import FileManager
from app.grammar_checker import GrammarChecker
from app.audio_extractor import AudioExtractor
from app.llm.ChatFactory import ChatFactory

from app.rag.RAGFactory import RAGFactory

available_llm = EnglishTutor.get_available_llm()
max_new_tokens = 200
RAG_search_k = 1



@cl.on_settings_update
async def setup_agent(settings):
    print("Settings update start...")
    english_tutor = cl.user_session.get("english_tutor")

    speakerId = settings["SpeakerId"]
    speakers_context = cl.user_session.get("speakers_context")
    explained_sentences = cl.user_session.get("explained_sentences")

    explained_sentences_speaker = get_explained_sentences_speaker(explained_sentences, speakerId)
    cl.user_session.set("explained_sentences_speaker", explained_sentences_speaker)

    await cl.Message(
        content=f"### Selected: {speakerId}",
    ).send()

    current_LLM = settings["CurrentLLM"]
    if english_tutor.get_current_llm_model_id() != current_LLM:
        print(f'LLM updated: {current_LLM}')
        english_tutor.set_chat_llm(current_LLM)

    print("on_settings_update", settings)

    await on_message(None)


# called when a new chat session is created.
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("counter", 0)
    english_tutor = EnglishTutor()

    start = time.time()
    #explained_sentences, speakers_context, sorted_speakers = english_tutor.get_study_plan() # explained sentences, speaker context
    #cl.user_session.set("explained_sentences", explained_sentences)
    #cl.user_session.set("speakers_context", speakers_context)
    #cl.user_session.set("speakers", sorted_speakers)
    #cl.user_session.set("explained_sentences_speaker", explained_sentences)

    start = time.time()
    file_manager = FileManager()
    
    if not os.path.isfile('cache/rag_sentences.json'):
        rag_sentences(file_manager, english_tutor.set_rag_engine(available_RAG[0]))

    explained_sentences = file_manager.read_from_json_file("cache/rag_sentences.json")
    cl.user_session.set("explained_sentences", explained_sentences)
    sentences_collection = file_manager.read_from_json_file("cache/raw_sorted_sentence_collection.json")
    cl.user_session.set("sentences_collection", sentences_collection)
    speakers = await get_speakers(sentences_collection)
    cl.user_session.set("speakers", speakers)

    end = time.time()
    print("on_chat_start time:", end - start)

    available_RAG = english_tutor.get_supported_rag_engines()

    english_tutor.set_chat_llm(available_llm[4])
    english_tutor.set_rag_engine(available_RAG[0])
    cl.user_session.set("english_tutor", english_tutor)

    await cl.ChatSettings(
        [
            Select(
                id="SpeakerId",
                label="Current Speaker",
                values=speakers,
                initial_index=0,
            ),
            Select(
                id="CurrentLLM",
                label="Current model",
                values=available_llm,
                initial_index=0,
            ),
        ]
    ).send()

    hello_msg = f"# Welcome to English Tutor Chat Bot AI! 🚀🤖\n\n"
    hello_msg += f"Please select in configuration (left of the text entry) what speaker you want to check. Otherwise all speakers will be used\n\n"
    initial_message = cl.Message(content=hello_msg)
    await initial_message.send()


    speaker = await ask_for_speaker()
    explained_sentences_speaker = await get_explained_sentences_speaker(explained_sentences, speaker)
    cl.user_session.set("explained_sentences_speaker", explained_sentences_speaker)

    await on_message(None)


# called when a new message is received from the user.
@cl.on_message
async def on_message(message: cl.Message):
    

    english_tutor = cl.user_session.get("english_tutor")
    counter = cl.user_session.get("counter")

    if counter == 0:
        print(f'counter: {counter}')
        explained_sentences_speaker = cl.user_session.get("explained_sentences_speaker")
        # if the dictionary is empty, then the user has completed the exercise
        if not explained_sentences_speaker:
            await cl.Message(
                content="Congratulations! You don't have any mistakes to practice. Let's continue!",
            ).send()
            return
        

        #Step 1: Select a sentence to practice
        errant = None
        for theme_key, theme_value in explained_sentences_speaker.items():
            #print(theme_value)
            errant_errores = theme_value['errant']

            if len(errant_errores) == 0:
                continue

            errant = random.choice(errant_errores)

            # Highlight the error and correction in the sentence
            original_sentence = errant["sentence"]
            corrected_sentence = errant["corrected_sentence"]

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
                original_sentence, errant["o_start"], errant["o_end"],
                errant["original_text"] if errant["original_text"] else "______"
            )

            highlighted_corrected_sentence = highlight_word_in_sentence(
                corrected_sentence, errant["c_start"], errant["c_end"],
                errant["corrected_text"] if errant["corrected_text"] else f'~~{errant["original_text"]}~~'
            )

            text = "**You've made mistake in the following sentence:**\n\n*" + highlighted_original_sentence + "*\n\n"
            text += "**It's corrected sentence:**\n\n*" + highlighted_corrected_sentence + "*\n\n"
            text += errant["llm_explanation"] + "\n\n"
            text += "Do you want to practice the error?"

            await cl.Message(
                content=text,
            ).send()

            res = await ask_action()

        # Step 2: First exercise
        msg = cl.Message(content='')
        await msg.send()

        # selected_speaker_text = cl.user_session.get("selected_speaker_text")
        mistake_description = errant['llm_explanation']
        RAG_context = errant['rag']

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

        response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
        cl.user_session.set("user_excercise", response)

        counter += 1
        cl.user_session.set("counter", counter)

    else:
        counter += 1
        cl.user_session.set("counter", counter)

        msg = cl.Message(content='')
        await msg.send()

        # Step 3: Check user answer, explain result and create new exercise
        context = "The current exersice is: \n"
        context += cl.user_session.get("user_excercise")

        context = "\n\nThe user answer:\n"
        context += "\n\n" + message.content + "\n"

        final_prompt = (f"Check user answer, explain result and create new exercise:\n\n"
                        f"CONTEXT:\n{context}"
                        f"QUESTION:\n Check my answer, explain result and create new exercise without answers.")

        response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)
        cl.user_session.set("user_excercise", response)

        if counter == 4:
            response += "\n\n**You have completed the exercise. Let\'s continue!**"
            cl.user_session.set("counter", 0)

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
        sorted_speakers += sorted( {value['speaker'] for value in sentences_collection} )
    
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