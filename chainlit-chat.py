import time
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
import random


from english_tutor import EnglishTutor

available_llm = ["google/gemma-1.1-2b-it", "google/gemma-1.1-7b-it"]
max_new_tokens = 200
RAG_search_k = 1


@cl.on_settings_update
async def setup_agent(settings):
    english_tutor = cl.user_session.get("english_tutor")

    speakerId = settings["SpeakerId"]
    speakers_context = cl.user_session.get("speakers_context")

    selected_speaker_text = speakers_context[speakerId]
    cl.user_session.set("selected_speaker_text", selected_speaker_text)

    current_LLM = settings["CurrentLLM"]
    if english_tutor.get_llm_model_id() != current_LLM:
        print(f'LLM updated: {current_LLM}')
        english_tutor = english_tutor.set_llm_model_id(current_LLM)

    current_RAG = settings["CurrentRAG"]
    if english_tutor.get_rag_engine_id() != current_RAG:
        print(f'RAG Engine updated: {current_RAG}')
        english_tutor = english_tutor.set_rag_engine(current_RAG)

    cl.user_session.set("aitana_bot", english_tutor)

    start = time.time()
    study_plan = english_tutor.get_study_plan(speakerId)
    cl.user_session.set("study_plan", study_plan)
    end = time.time()
    print("time:", end - start)

    print("on_settings_update", settings)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("counter", 0)
    english_tutor = EnglishTutor()

    speakers_context = english_tutor.get_speakers_context()
    cl.user_session.set("speakers_context", speakers_context)
    sorted_speakers = sorted(speakers_context.keys())

    speakerId = sorted_speakers[0]

    selected_speaker_text = speakers_context[speakerId]
    cl.user_session.set("selected_speaker_text", selected_speaker_text)

    start = time.time()
    study_plan = english_tutor.get_study_plan(speakerId)
    cl.user_session.set("study_plan", study_plan)
    end = time.time()
    print("time:", end - start)

    hello_msg = f"Hello, {speakerId}! Would you like to learn English?\n"

    await cl.Message(
        content=hello_msg
    ).send()

    available_RAG = english_tutor.get_supported_rag_engines()

    english_tutor.set_llm_model_id(available_llm[0])
    english_tutor.set_rag_engine(available_RAG[0])
    cl.user_session.set("english_tutor", english_tutor)

    await cl.ChatSettings(
        [
            Select(
                id="SpeakerId",
                label="Current Speaker",
                values=sorted_speakers,
                initial_index=0,
            ),
            Select(
                id="CurrentRAG",
                label="Current RAG Engine",
                values=available_RAG,
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


@cl.on_message
async def on_message(message: cl.Message):
    english_tutor = cl.user_session.get("english_tutor")
    counter = cl.user_session.get("counter")

    tema = None
    if counter == 0:
        print(f'counter: {counter}')
        study_plan: list = cl.user_session.get("study_plan")
        res = None
        while res is None or res.get("value") != "continue":
            tema = random.choice(study_plan)
            res = await ask_action(tema['llm_response'])

        msg = cl.Message(content='')
        await msg.send()

        context = ""

        # selected_speaker_text = cl.user_session.get("selected_speaker_text")
        mistake_description = tema['llm_response']

        _, _, RAG_context = await cl.make_async(english_tutor.search_in_index)(mistake_description,
                                                                                     RAG_search_k)

        context_str = "\n".join(RAG_context)

        context += "\n\nThe English rule:\n"
        context += "\n\n" + context_str + "\n"

        context += "\n\nMistake description: \n"
        context += mistake_description

        final_prompt = (f"You are english teacher. \n\nCONTEXT:\n{context} QUESTION:\n Create an exercise to practice "
                        f"my mistake.")

        print(final_prompt)
        response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)

        response = f"{mistake_description} \n\n {response}"

        counter += 1
        cl.user_session.set("counter", counter)

    else:
        counter += 1
        cl.user_session.set("counter", counter)

        msg = cl.Message(content='')
        await msg.send()

        context = "The current exersice is: \n"
        context += ''

        context = "\n\nThe user answer:\n"
        context += "\n\n" + message.content + "\n"

        final_prompt = f"Check user answer, explain result and create new exercise:\n\nCONTEXT:\n{context}"

        print(final_prompt)
        response = await cl.make_async(english_tutor.get_answer)(final_prompt, max_new_tokens)

        if counter == 4:
            cl.user_session.set("counter", 0)


    msg.content = f"{response}"

    await msg.update()


async def ask_action(content):
    return await cl.AskActionMessage(
        content=content,
        actions=[
            cl.Action(name="cancel", value="cancel", label="❌ No, thank you..."),
            cl.Action(name="continue", value="continue", label="✅ Yes, please!"),
        ],
    ).send()


