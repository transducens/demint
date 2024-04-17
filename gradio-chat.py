import gradio as gr
import tracemalloc
import time
from english_tutor import EnglishTutor

global speakers_context, selected_speaker_text, english_tutor
english_tutor = None
speakers_context = None
selected_speaker_text = None

tracemalloc.start()


def initialize_global_variables():
    global english_tutor, speakers_context

    if english_tutor is None:
        print("initialize english_tutor started")
        english_tutor = EnglishTutor()
        print("initialize english_tutor finished")

    if speakers_context is None:
        print("initialize speakers_context started")
        speakers_context = english_tutor.get_speakers_context()
        print("initialize speakers_context finished")


def chat_with_ai(query):
    global selected_speaker_text, english_tutor
    context = ""

    if selected_speaker_text is not None:
        context += "\nYou are given direct speech from a user. When responding, address the user by name: \n"
        context += selected_speaker_text

    D, I, RAG_context = english_tutor.search_in_faiss_index(query, k=3)
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
    speakers_context = english_tutor.get_speakers_context()

    return f"Video info: {video_title}"


def update_dropdown(_=None):
    global speakers_context
    sorted_speakers = []
    if speakers_context is not None:
        sorted_speakers = sorted(speakers_context.keys())
    return sorted_speakers


def handle_dropdown_selection(speaker_selection):
    global selected_speaker_text, speakers_context, english_tutor

    selected_speaker_text = ""
    if speakers_context is not None:
        selected_speaker_text = speakers_context.get(speaker_selection, "No text available.")

        #sentences = english_tutor.split_test_into_sentences(
            #selected_speaker_text
        #)
        #matches = english_tutor.check_sentences(sentences)

        #for i, match in enumerate(matches):
            #if len(match) > 0:
                #print(f"====================================")
                #sentence = sentences[i]
                #print(f"Sentence: {sentence}")
                #for error in match:
                    #print(
                        #f"Error: {error.message}, RuleId: {error.ruleId}, Offset: {error.offset}, Length: {error.errorLength}")

    return selected_speaker_text


def get_audio_path():
    audio_path = "audio/extracted_audio.wav"
    return audio_path


def refresh_audio(_=None):
    return get_audio_path()


def clean_cache():
    global speakers_context, selected_speaker_text, english_tutor
    english_tutor.clean_cache()
    speakers_context = None
    selected_speaker_text = None


def main():
    with gr.Blocks() as english_tutor_chat_ai:
        gr.Markdown("Chat with English Tutor AI")
        with gr.Row():
            with gr.Column():
                link = gr.Textbox(
                    label="Enter link to YouTube's video: (ex. https://www.youtube.com/watch?v=wv_nEUnhFFE )")
                with gr.Column():
                    # Process the YouTube link when the submit button is clicked.
                    info_markdown = gr.Markdown("Video info:")

                    submit_button_yt = gr.Button("Download audio")
                    submit_button_yt.click(fn=get_video, inputs=[link], outputs=[info_markdown])

            with gr.Column():
                audio_player = gr.Audio(value=get_audio_path, label="Listen to the audio", type="filepath")
                refresh_button = gr.Button("Refresh video")
                refresh_button.click(fn=get_audio_path, inputs=[], outputs=audio_player)

        with gr.Row():
            with gr.Column():
                sorted_speakers = update_dropdown()
                default_value = sorted_speakers[0] if sorted_speakers else None
                dropdown = gr.Dropdown(label="Select a speaker", choices=sorted_speakers, value=default_value)
                speaker_text = gr.Textbox(label="Speaker's text", value=handle_dropdown_selection(default_value),
                                          interactive=False, lines=10)
                dropdown.change(fn=handle_dropdown_selection, inputs=[dropdown], outputs=[speaker_text])

        gr.Markdown("Chat with English Tutor AI")
        with gr.Row():
            with gr.Column():
                query = gr.Textbox(label="Enter your query: (ex. How does past perfect work? )")
                submit_button = gr.Button("Submit")
                response = gr.Textbox(label="Chat History:", interactive=False, lines=10)
                # Process the user query when the submit button is clicked.
                submit_button.click(fn=chat_with_ai, inputs=[query], outputs=[response])

    english_tutor_chat_ai.launch()


if __name__ == '__main__':
   initialize_global_variables()
   main()
