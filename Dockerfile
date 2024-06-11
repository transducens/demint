# Use Ubuntu 20.04 as the base image
FROM ubuntu:20.04

# Set non-interactive mode for apt-get and configure timezone settings
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install necessary libraries and tools
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    gnupg \
    ffmpeg \
    libtiff5 \
    build-essential \
    p7zip-full \
    git \
    wget \
    openjdk-11-jdk \
    curl

# Install Miniconda
RUN mkdir -p /miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda3/miniconda.sh && \
    bash /miniconda3/miniconda.sh -b -u -p /miniconda3 && \
    rm -rf /miniconda3/miniconda.sh

# Set the PATH environment variable
ENV PATH="/miniconda3/bin:${PATH}"

# Initialize conda
RUN conda init bash && conda init zsh

# Set the working directory
WORKDIR /demint

# Copy the project into the container
COPY . /demint

# Create and activate a clean conda environment
RUN conda create --name DeMINT python=3.11 && \
    echo "conda activate DeMINT" >> ~/.bashrc

# Install necessary packages using conda and pip
RUN /miniconda3/bin/conda run -n DeMINT conda install pytorch torchvision torchaudio pytorch-cuda=11.8 cuda-toolkit faiss-gpu -c defaults -c pytorch -c nvidia -c conda-forge -y && \
    /miniconda3/bin/conda run -n DeMINT pip install errant chainlit gradio pyannote.audio language-tool-python pymupdf evaluate bitsandbytes pytube sentence-splitter sentence-transformers ragatouille huggingface_hub whisper-openai accelerate happytransformer pipreqs && \
    /miniconda3/bin/conda run -n DeMINT python -m spacy download en_core_web_sm

# Set environment variable for Hugging Face token
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# Expose ports 8000
EXPOSE 8000

# Set entry point and default command
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["conda run --no-capture-output -n DeMINT chainlit run chainlit-chat.py -w"]
