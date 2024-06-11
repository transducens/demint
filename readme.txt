Project Setup Instructions
==========================

Welcome to our project! Follow these setup instructions to ensure everything runs smoothly.

Prerequisites
-------------

Before you start, make sure you have the following prerequisites installed and set up on your system (Ubuntu 20.04 or for Windows, you can use WSL 2 or Docker):
Step 1: Install Miniconda and essential libraries
    sudo apt-get update && \
    sudo apt-get upgrade -y && \
    sudo apt-get install ffmpeg libtiff5 build-essential p7zip-full git wget openjdk-11-jdk -y

    mkdir -p ~/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm -rf ~/miniconda3/miniconda.sh && \
    ~/miniconda3/bin/conda init bash && \
    ~/miniconda3/bin/conda init zsh

RELOAD terminal

Step 2: Clone the Project Repository
    git clone https://github.com/transducens/demint.git
    cd demint

    #to update: git pull https://github.com/transducens/demint.git

Step 3: Create a Conda Environment
    Option 1 (recommended):
        conda env create -f environment.yml
        conda activate DeMINT
        pip install -r requirements.txt
        pip install pymupdf whisper-openai bitsandbytes
        python -m spacy download en_core_web_sm

    Option 2 (for clean system):
        conda create --name DeMINT python=3.11
        conda activate DeMINT
        conda install pytorch torchvision torchaudio pytorch-cuda=11.8 cuda-toolkit faiss-gpu -c defaults -c pytorch -c nvidia -c conda-forge -y
        pip install errant chainlit gradio pyannote.audio language-tool-python pymupdf evaluate bitsandbytes pytube sentence-splitter sentence-transformers ragatouille huggingface_hub whisper-openai accelerate happytransformer pipreqs
        python -m spacy download en_core_web_sm
        conda env export --from-history > environment.yml

            Change environment.yml:
                channels:
                  - defaults
                  - pytorch
                  - nvidia
                  - conda-forge

        pipreqs --force .

Step 4: Hugging Face CLI Login
   To use models from the Hugging Face Hub, you'll need to log in via their CLI tool. This is essential for downloading model files:

   - Login to your Hugging Face account via the CLI:
     huggingface-cli login

   - Enter your Hugging Face API token when prompted. You can find or create an API token on your Hugging Face account's settings page.

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

        or

        python user-app.py

    - Run the application with Chainlit by executing the following command:

        chainlit run chainlit-chat.py -w

    After executing the command, Gradio or Chainlit will start the application and automatically open it in your default web browser.
    If it doesn't open automatically, Gradio will provide a local URL in the terminal output, which you can manually copy and paste into your browser to access the application.

Happy processing!

-------------
Useful Commands
-------------
WSL 2:
wsl --unregister Ubuntu-20.04 #to remove wsl
\\wsl$                        #to access wsl files

DOCKER:
docker login
docker build -t levnikolaevich87/english-tutor:latest .
docker push levnikolaevich87/english-tutor:latest
docker pull levnikolaevich87/english-tutor:latest
docker run -e HF_TOKEN='your token' --gpus all -p 8080:8000 levnikolaevich87/english-tutor:latest

CUDA:
nvcc --version
nvidia-smi
