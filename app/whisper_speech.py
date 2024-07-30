from transformers import WhisperForConditionalGeneration, pipeline
import csv

from jiwer import wer
from transformers import WhisperTokenizer, WhisperFeatureExtractor

import os

from transformers import WhisperForConditionalGeneration

from peft import PeftModel, PeftConfig

model_id = "./whisper-v3-LoRA-en_students_test_2"

peft_model_id = "LoRA_Test/checkpoint-7500/adapter_model" # Use the same model ID as before.
language = "en"
task = "transcribe"
peft_config = PeftConfig.from_pretrained(peft_model_id)
model = WhisperForConditionalGeneration.from_pretrained(
  peft_config.base_model_name_or_path, load_in_8bit=False)

model = PeftModel.from_pretrained(model, peft_model_id)

tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-large-v3", language="english", task="transcribe")
aaa = WhisperFeatureExtractor.from_pretrained("openai/whisper-large-v3")
pipe = pipeline(model=model, tokenizer=tokenizer, feature_extractor=aaa, task="automatic-speech-recognition", device=device)

def transcribe(audio):
    p = pipe(audio, return_timestamps=False)
    text = p["text"]
    return text