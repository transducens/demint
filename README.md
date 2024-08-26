
# DeMINT: Automated Language Debriefing for English Learners via AI Chatbot Analysis of Meeting Transcripts

## Project Overview

This is the repository for DeMINT's chatbot code and auxiliary scripts.

DeMINT ("Automated Language Debriefing for English Learners via AI Chatbot Analysis of Meeting Transcripts") is a project funded by the EU's [UTTER](https://he-utter.eu/) project (grant agreement number 101070631) via a cascaded funding [call](https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/competitive-calls-cs/3722). DeMINT runs from January 15, 2024, to October 15, 2024.

### Project Goals

DeMINT aims to develop a conversational system that helps non-native English speakers improve their language skills by analyzing transcripts of video conferences in which they have participated. The system integrates cutting-edge techniques in conversational AI, including:

- Pre-trained large language models (LLMs)
- In-context learning
- External non-parametric memory retrieval
- Efficient parameter fine-tuning
- Grammatical error correction
- Error-preserving speech synthesis

The project will culminate in a pilot study to assess the system’s effectiveness among L2-English learners.

<img src="demint-diagram.png" width="700">

## Installation and Setup

Clone the project repository:

```bash
git clone https://github.com/transducens/demint.git
cd demint
```

Create a Conda environment and install dependencies:

```bash
conda env create -f environment.yml
conda activate DeMINT
pip install -r requirements.txt
pip install pymupdf whisper-openai bitsandbytes
python -m spacy download en_core_web_sm
```

Finally, set up HuggingFace and OpenAI API access. To use models from the HuggingFace hub, log in using the CLI:

```bash
huggingface-cli login
```

Enter your HuggingFace API token when prompted. You can find or create an API token in your HuggingFace account's settings.

For OpenAI API access, set your API key as an environment variable:

```bash
export OPENAI_API_KEY=[your OpenAI API key]
```

## Running the preprocessing pipeline

Place videos of the online meetings in the `assets/videos` directory. Run the preprocessing pipeline:

```bash
conda activate DeMINT
bash run_pipeline.sh
```

All necessary files will be generated in the `cache` directory.

## Running the chatbot

Simply run:

```bash
conda activate DeMINT
bash run_app.sh
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

<img src="public/logo_dark.png" width="200" height="200">
