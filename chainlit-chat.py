import time
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
import random


from english_tutor import EnglishTutor

available_llm = EnglishTutor.get_available_llm()
max_new_tokens = 200
RAG_search_k = 1


@cl.on_settings_update
async def setup_agent(settings):
    print("Settings update start...")
    english_tutor = cl.user_session.get("english_tutor")

    #speakerId = settings["SpeakerId"]
    #speakers_context = cl.user_session.get("speakers_context")

    #selected_speaker_text = speakers_context[speakerId]
    #cl.user_session.set("selected_speaker_text", selected_speaker_text)

    current_LLM = settings["CurrentLLM"]
    if english_tutor.get_current_llm_model_id() != current_LLM:
        print(f'LLM updated: {current_LLM}')
        english_tutor.set_chat_llm(current_LLM)

    current_RAG = settings["CurrentRAG"]
    if english_tutor.get_rag_engine_id() != current_RAG:
        print(f'RAG Engine updated: {current_RAG}')
        english_tutor.set_rag_engine(current_RAG)

    cl.user_session.set("aitana_bot", english_tutor)

    start = time.time()
    #study_plan = english_tutor.get_study_plan(speakerId)
    #cl.user_session.set("study_plan", study_plan)
    end = time.time()
    print("time:", end - start)

    #print("on_settings_update", settings)


# called when a new chat session is created.
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("counter", 0)
    english_tutor = EnglishTutor()

    # TODO repetitivo?? ya que 'get_study_plan() ya lo hace
    speakers_context = english_tutor.get_speakers_context(group_by_speaker=False)    
    cl.user_session.set("speakers_context", speakers_context)

    #selected_speaker_text = speakers_context[speakerId]
    #cl.user_session.set("selected_speaker_text", selected_speaker_text)

    start = time.time()
    study_plan = english_tutor.get_study_plan()
    cl.user_session.set("study_plan", study_plan)
    end = time.time()
    print("on_chat_start time:", end - start)

    available_RAG = english_tutor.get_supported_rag_engines()

    english_tutor.set_chat_llm(available_llm[0])
    english_tutor.set_rag_engine(available_RAG[0])
    cl.user_session.set("english_tutor", english_tutor)

    await cl.ChatSettings(
        [
            #Select(
            #    id="SpeakerId",
            #    label="Current Speaker",
            #    values=sorted_speakers,
            #    initial_index=0,
            #),
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

    hello_msg = f"# Welcome to English Tutor Chat Bot AI! 🚀🤖\n\n"
    hello_msg += "Hi there! Could you please share your name with me? I'd love to get started analyzing your phrases.\n\n"
    #hello_msg += f"{speakerId}, let's start by learning English!"
    initial_message = cl.Message(content=hello_msg)
    await initial_message.send()
    await on_message(None)


# called when a new message is received from the user.
@cl.on_message
async def on_message(message: cl.Message):
    english_tutor = cl.user_session.get("english_tutor")
    counter = cl.user_session.get("counter")

    if counter == 0:
        print(f'counter: {counter}')
        study_plan: dict = cl.user_session.get("study_plan")

        #Step 1: Select a sentence to practice
        res = None
        errant = None
        while res is None or res.get("value") != "continue":
            theme_key = random.choice(list(study_plan.keys()))
            theme_value = study_plan[theme_key]
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
