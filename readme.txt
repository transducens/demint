Project Setup Instructions
==========================

Welcome to our project! Follow these setup instructions to ensure everything runs smoothly.

Prerequisites
-------------

Before you start, make sure you have the following prerequisites installed and set up on your system:

1. Install FFmpeg
   FFmpeg is required for processing audio files, especially for the functionality provided by Whisper. To install FFmpeg:

   - Windows:
     - Download the latest version from FFmpeg.org or from https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
     - Extract the files and add the path to the bin folder to your system's PATH environment variable.
     - Verify the installation by opening a command prompt and typing ffmpeg -version.

   - macOS:
     - Use Homebrew by running brew install ffmpeg in the terminal.
     - Verify the installation with ffmpeg -version.

   - Linux:
     - Install FFmpeg using your distribution's package manager, for example, sudo apt-get install ffmpeg for Ubuntu.
     - Confirm by running ffmpeg -version in the terminal.

   Ensure that FFmpeg is correctly installed and accessible from your PATH to avoid issues during audio processing.

2. Install 7-Zip
   7-Zip is required for extracting files from compressed archives, which may be necessary when installing FFmpeg on Windows or handling other compressed files. To install 7-Zip:

   - Windows:
     - Download the latest version from the 7-Zip official website at https://www.7-zip.org/
     - Install 7-Zip by running the downloaded executable file and following the installation prompts.
     - Optionally, add the path to the 7-Zip executable (usually C:\Program Files\7-Zip) to your system's PATH environment variable to use it from the command prompt.
     - Verify the installation by opening a command prompt and typing 7z -version.

   - macOS and Linux:
     - While 7-Zip primarily targets Windows, macOS and Linux users can use command-line tools like unzip, tar, and gzip that come pre-installed with most distributions. Alternatively, for a GUI application, macOS users can use The Unarchiver, and Linux users can use p7zip (the POSIX command-line port of 7-Zip).
     - For installing p7zip on Linux, use your distribution's package manager, for example, sudo apt-get install p7zip-full for Ubuntu.
     - Confirm the installation by running 7z -version in the terminal (for p7zip users).

    Ensure that 7-Zip or equivalent tools are correctly installed and accessible from your PATH to avoid issues when extracting compressed files.

3. Hugging Face CLI Login
   To use models from the Hugging Face Hub, you'll need to log in via their CLI tool. This is essential for downloading model files:

   - Login to your Hugging Face account via the CLI:
     huggingface-cli login

   - Enter your Hugging Face API token when prompted. You can find or create an API token on your Hugging Face account's settings page.

4. Organizing PDF
   For the project to process your documents and audio files correctly, please organize them into specific folders within the project directory:

   - PDF Documents for RAG: Place your PDF documents into a folder named pdf_rag. These documents will be used for text-based queries and information retrieval.

5. Setting Up the Conda Environment
    For package and environment management, this project utilizes Conda. If Conda is not yet installed on your system, it is recommended to install Miniconda. It's a minimal installer for Conda and provides all necessary tools.

    - **Installing Miniconda:**

      1. Download Miniconda for Windows, macOS, or Linux from the official website: https://docs.conda.io/en/latest/miniconda.html.
      2. Follow the provided instructions to install Miniconda. Optionally, add Miniconda to your PATH during installation or use the Miniconda prompt/terminal for Conda commands.
      3. For Windows execute: setx PATH "%PATH%;C:\ProgramData\miniconda3;C:\ProgramData\miniconda3\Scripts;C:\ProgramData\miniconda3\Library\bin" /M

    - **Setting Up Your Project Environment with Conda:**

      1. Open your system's command prompt or terminal.
      2. Change directory to your project's root folder where the `environment.yml` file is located.
         ```
         cd /path/to/your/project
         ```
      3. Create the Conda environment using the `environment.yml` file by running:
         ```
         conda env create -f environment.yml
         ```
         This command sets up a new Conda environment with all the dependencies specified in the `environment.yml` file.
      4. Once the environment creation process is complete, activate the new environment with:
         ```
         conda activate DeMINT
         ```
      5. To verify the setup, check the installed packages in the environment:
         ```
         conda list
         ```

    This process will ensure that you have a Conda environment ready with all the necessary dependencies for the project. Make sure to activate the project-specific Conda environment whenever you work on the project to maintain consistency across development and production setups.

By following these setup instructions, you'll ensure that all components of the project function correctly.

-------------
Launching the Application
-------------

    To start the application, you need to execute it using Gradio from the terminal.
    Make sure you are in the project directory where your main.py file is located.

    Then, follow these steps to launch the application:
    - Open a terminal or Anaconda Prompt and navigate to your project directory.
    - Activate your environment with:
         ```
         conda activate DeMINT
         ```
    - Set up the Hugging Face credentials by running and following the instructions in the terminal:
         ```
         huggingface-cli login
         ```
    - Run the application with Gradio by executing the following command:

        python gradio-chat.py

    - Run the application with Chainlit by executing the following command:

        chainlit run chainlit-chat.py -w

    After executing the command, Gradio or Chainlit will start the application and automatically open it in your default web browser.
    If it doesn't open automatically, Gradio will provide a local URL in the terminal output, which you can manually copy and paste into your browser to access the application.

Happy processing!

-------------
Flight Log
-------------
https://docs.google.com/document/d/14XDQEhmLaw1h2JEPxD4VU8NhrZbyfar2BQ1_C0neF7E/edit?usp=sharing

Usefully commands:
conda activate DeMINT
conda deactivate
conda remove --name DeMINT --all

conda env export > environment.yml
conda env create -f environment.yml
conda env update --name DeMINT --file environment.yml --prune


pip install faiss-cpu
pip install PyMuPDF
pip install whisper-openai
pip install sentence-transformers
pip install pyannote.audio

Example:
https://chat.openai.com/share/7eef562a-30cb-44dc-924d-992c97b7a5a1

=================
Ubuntu 20.04
    sudo apt-get update && \
    sudo apt-get upgrade -y && \
    sudo apt-get install ffmpeg libtiff5 build-essential git wget

    mkdir -p ~/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm -rf ~/miniconda3/miniconda.sh && \
    ~/miniconda3/bin/conda init bash && \
    ~/miniconda3/bin/conda init zsh

RELOAD terminal

    git clone https://github.com/transducens/demint.git
    cd demint
    git pull https://github.com/transducens/demint.git

Variant 1:
    conda env create -f environment-ubuntu.yml
    conda activate DeMINT

Variant 2:
    conda create --name DeMINT
    conda activate DeMINT
    conda env update --name DeMINT --file environment-ubuntu.yml --prune

For clean system:
    conda create --name DeMINT
    conda activate DeMINT
    conda install faiss-gpu pytorch torchvision torchaudio pytorch-cuda=12.1 cuda-toolkit -c pytorch -c nvidia -c conda-forge
    pip install pymupdf evaluate bitsandbytes pytube sentence-splitter language-tool-python gradio chainlit sentence-transformers ragatouille dspy-ai huggingface_hub pyannote.audio whisper-openai accelerate
    pip install errant
    python -m spacy download en_core_web_sm
    conda env export > environment-ubuntu.yml


===========
WSL 2

wsl --unregister Ubuntu-20.04
\\wsl$

===========
DOCKER
docker login

docker build -t levnikolaevich87/english-tutor:latest .
docker push levnikolaevich87/english-tutor:latest
docker pull levnikolaevich87/english-tutor:latest

docker run -e HF_TOKEN='your token' --gpus all -p 8080:8000 levnikolaevich87/english-tutor:latest

nvcc --version
nvidia-smi

git clone -b features/DEMINT-001-llm-factory https://github.com/transducens/demint.git

docker run --gpus all --shm-size 2g -p 8083:80 -v D:/Development/UNIVERSIDAD/BECA/tgi:/data -e DISABLE_EXLLAMA=True -e HUGGING_FACE_HUB_TOKEN=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 ghcr.io/huggingface/text-generation-inference:2.0 --model-id google/gemma-1.1-2b-it --num-shard 1 --max-input-tokens 1000 --max-batch-prefill-tokens 1000
