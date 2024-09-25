
# DeMINT: Automated Language Debriefing for English Learners via AI Chatbot Analysis of Meeting Transcripts

## Table of Contents
- [DeMINT](#demint-automated-language-debriefing-for-english-learners-via-ai-chatbot-analysis-of-meeting-transcripts)
  - [Project Overview](#project-overview)
  - [Project Goals](#project-goals)
  - [Installation and Setup](#installation-and-setup)
  - [Preparing Data](#preparing-data)
    - [Download Audio from Youtube (optional)](#download-audio-from-youtube-optional)
    - [Create Cache Files](#create-cache-files)
  - [Run application](#run-application)
    - [Run Kind Teacher Server](#run-kind-teacher-server)
    - [Run the Chatbot Application](#run-the-chatbot-application)
  - [Clean the Cache Files](#clean-the-cache-files)
  - [How to Cite this Work](#how-to-cite-this-work)
  - [Documents](#documents)


## Project overview

This is the repository for DeMINT's chatbot code and auxiliary scripts.

DeMINT ("Automated Language Debriefing for English Learners via AI Chatbot Analysis of Meeting Transcripts") is a project funded by the EU's [UTTER](https://he-utter.eu/) project (grant agreement number 101070631) via a cascaded funding [call](https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/competitive-calls-cs/3722). DeMINT was one of 8 projects selected out of 54 submissions. The project runs from January 15, 2024, to October 15, 2024.

DeMINT's architecture was presented at UTTER 2nd User Day, an online event held on July 5, 2024. The [video](https://www.youtube.com/watch?v=TzEK9JlxVH4) of the presentation is now available online. The project is being executed by the Transducens research group at Universitat d'Alacant, Spain. 

## Project goals

DeMINT aims to develop a conversational system that helps non-native English speakers improve their language skills by analyzing transcripts of video conferences in which they have participated. The system integrates cutting-edge techniques in conversational AI, including:

- Pre-trained large language models (LLMs)
- In-context learning
- External non-parametric memory retrieval
- Efficient parameter fine-tuning
- Grammatical error correction
- Error-preserving speech synthesis

The project will culminate in a pilot study to assess the system’s effectiveness among L2-English learners.

<img src="demint-diagram.png" width="700">

# Installation and setup

Clone the project repository:

```bash
git clone https://github.com/transducens/demint.git
cd demint
```

Install Conda following [the official tutorial](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
Then create the Conda environment and install dependencies:

```bash
conda env create -f environment.yml
conda activate DeMINT
pip install -r requirements.txt
```

Finally, set up HuggingFace. To use models from the HuggingFace hub, log in using the CLI:

```bash
huggingface-cli login
```

When prompted, enter your HuggingFace API token. You can find or [generate this token](https://huggingface.co/docs/hub/security-tokens#how-to-manage-user-access-tokens) in the settings section of your HuggingFace account.

Additionally, you must accept the user conditions to use the following models:

- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
- [openai/whisper-large-v3](https://huggingface.co/openai/whisper-large-v3)
- [meta-llama/Meta-Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)

If you wish to use any other models from HuggingFace, you may also need to accept their respective user conditions.


# Preparing data
Go to the root directory `demint`.

## Download audio from YouTube (optional)

<details>
<summary>
More details.
</summary>

### Option 1
Download directly the audio from YouTube (internally gets converted using ffmpeg) and it gets stored in 'assets/audios/', if possible with 'wav' extension.

**Download audio file**

```bash
usage: python -m app.audio_downloader [-h] -u URL [-n NAME]

Description of your script

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL of the video to download
  -n NAME, --name NAME  Name set to the downloaded video file

```

### Option 2
Download the video from YouTube and store it in 'assets/videos/'. Then extract the audio of all the videos from the directory 'assets/videos/' and store them in 'assets/audios/' with 'wav' extension.

**Download video file**
```bash
usage: python -m app.video_downloader [-h] -u URL [-n NAME]

Description of your script

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL of the video to download
  -n NAME, --name NAME  Name set to the downloaded video file
```

**Extract audio**
```bash
# Extract audio from a video file.
# From assets/videos/ to assets/audios/
usage: python -m app.extract_audio [-h] [-vf VIDEO_FILE] [-af AUDIO_FILE] [-vd VIDEO_DIRECTORY]
                        [-ad AUDIO_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -vf VIDEO_FILE, --video_file VIDEO_FILE
                        Path to where the input video file is located.
  -af AUDIO_FILE, --audio_file AUDIO_FILE
                        Path to where the output audio file will be saved.
  -vd VIDEO_DIRECTORY, --video_directory VIDEO_DIRECTORY
                        Path to the directory containing the input video files.
  -ad AUDIO_DIRECTORY, --audio_directory AUDIO_DIRECTORY
                        Path to the directory where the output audio files will be saved.
```
</details>

## Create cache files

Fot the correct execution of the application, the files from `cache/rag_sentences/` and `cache/raw_sorted_sentence_collection/` are required.
And it is also necessary that the conversation used in the application has the same name in both directories.

### Option 1 (recommended)
**Run all the videos through the pipeline**

The videos are read from the directory: `assets/videos/` by default. 
```bash
bash run_pipeline.sh
```

### Option 2
**Download audio from YouTube (optional)**

The videos are saved in `assets/videos/`
```bash
usage: python -m app.video_downloader [-h] -u URL [-n NAME]

Description of your script

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL of the video to download
  -n NAME, --name NAME  Name set to the downloaded video file
```

**Extract audio**

Extracts the audio from a video file (by default from `assets/videos/`) and stores the audio (by default in `assets/audios/`) with the same name, 16hz of sample rate and mono audio.
```bash
# Extract audio from a video file.
# From assets/videos/ to assets/audios/
usage: python -m app.extract_audio [-h] [-vf VIDEO_FILE] [-af AUDIO_FILE] [-vd VIDEO_DIRECTORY]
                        [-ad AUDIO_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -vf VIDEO_FILE, --video_file VIDEO_FILE
                        Path to where the input video file is located.
  -af AUDIO_FILE, --audio_file AUDIO_FILE
                        Path to where the output audio file will be saved.
  -vd VIDEO_DIRECTORY, --video_directory VIDEO_DIRECTORY
                        Path to the directory containing the input video files.
  -ad AUDIO_DIRECTORY, --audio_directory AUDIO_DIRECTORY
                        Path to the directory where the output audio files will be saved.
```

**Diarize audio**

Diarizes the audio (by default from `assets/audios/`) and stores the resulting segments in a directory (by default in `cache/diarized_audios/`) with the same name, 16hz of sample rate and mono audio.
The first number of each segment is the index and the second number is the speaker ID.
```bash
# Diarize an audio file or a directory of audio files.
# From assets/audios/ to cache/diarized_audios/
usage: python -m app.diarize_audio [-h] [-af AUDIO_FILE] [-ad AUDIO_DIRECTORY]
                        [-sd SEGMENTS_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -af AUDIO_FILE, --audio_file AUDIO_FILE
                        Path to where the input audio file is located.
  -ad AUDIO_DIRECTORY, --audio_directory AUDIO_DIRECTORY
                        Path to the input directory containing the audio files.
  -sd SEGMENTS_DIRECTORY, --segments_directory SEGMENTS_DIRECTORY
                        Path to the output directory where all the diarized audios will
                        be saved.
```

**Transcribe audio**

Transcribes the diarized audio (by default from `cache/diarized_audios/`) and stores the resulting transcription (by default in `cache/diarized_transcripts`) with the same name in JSON format.
```bash
# Transcribe the audio files of a directory.
# From cache/diarized_audios/ to cache/diarized_transcripts/
usage: python -m app.whisper_speech [-h] [-ad AUDIO_DIRECTORY] [-tf TRANSCRIPT_FILE]
                         [-aad ALL_AUDIOS_DIRECTORY] [-td TRANSCRIPT_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -ad AUDIO_DIRECTORY, --audio_directory AUDIO_DIRECTORY
                        Path to where the audio input directory of is located.
  -tf TRANSCRIPT_FILE, --transcript_file TRANSCRIPT_FILE
                        Path to where the output transcript file will be saved.
  -aad ALL_AUDIOS_DIRECTORY, --all_audios_directory ALL_AUDIOS_DIRECTORY
                        Path to the directory containing the input audio directories.
  -td TRANSCRIPT_DIRECTORY, --transcript_directory TRANSCRIPT_DIRECTORY
                        Path to the directory where the output transcript files will be
                        saved.
```

**Prepare sentences collection**

Extracts the sententences and sorts them (by default from `cache/diarized_transcripts/`) and stores the result (by default in `cache/raw_sorted_sentence_collecion/`) with the same name in JSON format.
```bash
# Prepare a sorted sentence collection from a transcript file or a directory of transcript files.
# From cache/diarized_transcripts/ to cache/raw_sorted_sentence_collection/
usage: python -m app.prepare_sentences [-h] [-tf TRANSCRIPT_FILE] [-sf SENTENCES_FILE]
                            [-td TRANSCRIPT_DIRECTORY] [-sd SENTENCES_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -tf TRANSCRIPT_FILE, --transcript_file TRANSCRIPT_FILE
                        Path to where the input transcript file is located.
  -sf SENTENCES_FILE, --sentences_file SENTENCES_FILE
                        Path to where the output sentences collection file will be saved.
  -td TRANSCRIPT_DIRECTORY, --transcript_directory TRANSCRIPT_DIRECTORY
                        Path to the directory containing the input transcript files.
  -sd SENTENCES_DIRECTORY, --sentences_directory SENTENCES_DIRECTORY
                        Path to the directory where the output sentences collection files
                        will be saved.
```

**Obtain errant errors**

Extracts grammatical errors (by default from `cache/raw_sorted_sentence_collection/`) and stores the sentences with errors (by default in `cache/errant_all_evaluation/`) with the same name in JSON format.
```bash
# Obtain errors from a sentences collection file.
# From cache/raw_sorted_sentence_collection/ to cache/errant_all_evaluation/
usage: python -m app.obtain_errors [-h] [-sf SENTENCES_FILE] [-ef ERRANT_FILE]
                        [-sd SENTENCES_DIRECTORY] [-ed ERRANT_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -sf SENTENCES_FILE, --sentences_file SENTENCES_FILE
                        Path to where the input sentences collection file is located.
  -ef ERRANT_FILE, --errant_file ERRANT_FILE
                        Path to where the output errant evaluation file will be saved.
  -sd SENTENCES_DIRECTORY, --sentences_directory SENTENCES_DIRECTORY
                        Path to the directory containing the input sentences collection
                        files.
  -ed ERRANT_DIRECTORY, --errant_directory ERRANT_DIRECTORY
                        Path to the directory where the output errant evaluation files
                        will be saved.
```

**Explain obtained errors**

Using an LLM (by default Llama 3.1 8B Instruct), explains all errors with more detail (by default from `cache/errant_all_evaluation/` ) and stores them (by default in `cache/explained_sentences/`) with the same name in JSON format.
```bash
# Explain the obtained errors from the errant evaluation files.
# From cache/errant_all_evaluation/ to cache/explained_sentences/
usage: python -m app.explain_sentences [-h] [-ef ERRANT_FILE] [-xf EXPLAINED_FILE]
                            [-ed ERRANT_DIRECTORY] [-xd EXPLAINED_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -ef ERRANT_FILE, --errant_file ERRANT_FILE
                        Path to where the input errant evaluation file is located.
  -xf EXPLAINED_FILE, --explained_file EXPLAINED_FILE
                        Path to where the output explained sentences file will be saved.
  -ed ERRANT_DIRECTORY, --errant_directory ERRANT_DIRECTORY
                        Path to the directory containing the input errant evaluation
                        files.
  -xd EXPLAINED_DIRECTORY, --explained_directory EXPLAINED_DIRECTORY
                        Path to the directory where the output explained sentences files
                        will be saved.
```

**Get RAG data about the sentences**

Indexes RAG data related to the extracted errors (by default from `cache/explained_sentences/`) and stores all the information (by default in `cache/rag_sentences/`) with the same name in JSON format.
```bash
# Get RAG (Retrieval-Augmented Generation) data for each sentence
# From cache/explained_sentences/ to cache/rag_sentences/
usage: python -m app.rag_sentences [-h] [-xf EXPLAINED_FILE] [-rf RAG_FILE]
                        [-xd EXPLAINED_DIRECTORY] [-rd RAG_DIRECTORY]

options:
  -h, --help            show this help message and exit
  -xf EXPLAINED_FILE, --explained_file EXPLAINED_FILE
                        Path to where the input explained sentences file is located.
  -rf RAG_FILE, --rag_file RAG_FILE
                        Path to where the output rag sentences file will be saved.
  -xd EXPLAINED_DIRECTORY, --explained_directory EXPLAINED_DIRECTORY
                        Path to the directory containing the input explained sentences
                        files.
  -rd RAG_DIRECTORY, --rag_directory RAG_DIRECTORY
                        Path to the directory where the output rag sentences files will
                        be saved.
```

# Run application

## Run kind teacher server
**Create kind teacher environment**
```bash
cd kind_teacher_server

conda env create -f environment.yml

conda activate llamafactory_env

bash init.sh
```


**Set parameters of kind teacher API server (optional)**
```bash
# Default 8000
export KIND_TEACHER_PORT=8000

# Default localhost
export KIND_TEACHER_HOST="localhost"
```
(Port and address of the server can be modified manually in "kind_teacher_server/src/llamafactory/api/app.py")


**Run kind teacher API server**
```bash
# If you are not inside of the directory
cd kind_teacher_server

[CUDA_VISIBLE_DEVICES=0] llamafactory-cli api run_api_inference_1.yaml
```


## Run the chatbot application


**Set the OPENAI key for GPT**
```bash
export OPENAI_API_KEY="my_chatgpt_key_goes_here"
```


**Run chatbot**
```bash
usage: python user_app.py [-h] \
                          [-l] \
                          [--conver CONVER] \
                          [--speaker SPEAKER] \ 
                          [--port PORT] \ 
                          [--no_log] \ 
                          [--port_kind_teacher PORT_KIND_TEACHER] \ 
                          [--address_kind_teacher ADDRESS_KIND_TEACHER]

options:
  -h, --help         Show this help message and exit
  -l, --list         List all the conversations available.
  --conver CONVER    The transcripted conversation to show. Default is diarization_result
  --speaker SPEAKER  The speaker to show in the transcript. Default is All speakers.
  --port PORT        The port in which the server will run. Default is 8000
  --no_log           If the flag is called, the chatbot conversation will not save logs of the execution. Default is False.
  --port_kind_teacher PORT_KIND_TEACHER
                        The port in which the kind teacher will run. Default is 8000
  --address_kind_teacher ADDRESS_KIND_TEACHER
                        The address in which the kind teacher will run. Default is
                        localhost

```

# Clean the cache files

```bash 
bash clean_cache.sh
```

Gradio will automatically open the application in your default web browser. If it doesn't, a local URL will be provided in the terminal output.

## How to cite this work

If you use DeMINT in your research, please cite it as follows:

```bibtex
@misc{DeMINT2024,
  author = {Juan Antonio Pérez-Ortiz and Miquel Esplà-Gomis and Víctor M. Sánchez-Cartagena and Felipe Sánchez-Martínez and Roman Chernysh and Gabriel Mora-Rodríguez and Lev Berezhnoy},
  title = {{DeMINT}: Automated Language Debriefing for English Learners via AI Chatbot Analysis of Meeting Transcripts},
  year = {2024},
  howpublished = {\url{https://github.com/transducens/demint}},
}
```

## Documents

- The data management plan addresses issues such as data collection, data generation, data sharing, property rights and privacy, and long-term preservation and re-use, in compliance with national and EU legislation.
- The consent form in Catalan will be signed by the participants in the human evaluation and has been already approved by the university's ethics committee.

Links to these documents will be made available here.

<img src="public/logo_dark.png" width="200" height="200">
