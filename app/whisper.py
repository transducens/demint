import torch
import evaluate

from typing import Any
from transformers import AutoModelForSpeechSeq2Seq, Seq2SeqTrainer, WhisperTokenizer, WhisperProcessor, WhisperFeatureExtractor, Seq2SeqTrainingArguments
from datasets import load_dataset

from dataclasses import dataclass
from typing import Any, Dict, List, Union

from datasets import load_dataset, DatasetDict

import os

from transformers import WhisperForConditionalGeneration
from datasets import Audio

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

from huggingface_hub import notebook_login

notebook_login()

class DataCollatorSpeechSeq2SeqWithPadding:
    processor: any
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors = "pt")

        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors = "pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        return batch

class Whisper:
    def __init__(self, model_id = "openai/whisper-large-v3"):
        """
        self.__model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            # QLoRA
            #load_in_4bit = True,
            #device_map = "auto",
            torch_dtype = torch.torch_dtype,
            low_cpu_mem_usage = True,
            use_safetensors = True
        )
        """

        self.__model = WhisperForConditionalGeneration.from_pretrained(model_id)

        self.__model.generation_config.language = "english"
        self.__model.generation_config.task = "transcribe"

        self.__model.generation_config.forced_decoder_ids = None

        self.__model.to(device)

        self.__feature_extractor = WhisperFeatureExtractor.from_pretrained(model_id)
        self.__processor = WhisperProcessor.from_pretrained(model_id, language="english", task="transcribe")
        self.__tokenizer = WhisperTokenizer.from_pretrained(model_id, language="english", task="transcribe")
        self.__metric = evaluate.load("wer")

    """
    def load_dataset(self):
        common_voice = DatasetDict()

        common_voice["train"] = load_dataset("mozilla-foundation/common_voice_11_0", "es", split="train+validation", use_auth_token=True)
        common_voice["test"] = load_dataset("mozilla-foundation/common_voice_11_0", "es", split="test", use_auth_token=True)
        print(common_voice)
        print(common_voice["train"][15])
        common_voice = common_voice.remove_columns(["accent", "age", "client_id", "down_votes", "gender", "locale", "path", "segment", "up_votes"])
        print(common_voice)
        print(common_voice["train"][15])

        return common_voice
    """

    def load_dataset(self):
        common_voice = load_dataset("audiofolder", data_dir=os.path.join("TSCC_database"))
        print(common_voice)
        print(common_voice["train"][15])

        return common_voice

    def prepare_dataset(self, batch):
        audio = batch["audio"]
        batch["input_features"] = self.__feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
        batch["labels"] = self.__tokenizer(batch["sentence"]).input_ids

        return batch

    def prepare_batch(self, batch):
        audio = batch["audio"]

        batch["input_features"] = self.__feature_extractor(audio["array"], sampling_rate = audio["sampling_rate"]).input_features[0]

        batch["labels"] = self.__tokenizer(batch["sentence"]).input_ids
        return batch
    
    def compute_metrics(self, pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        label_ids[label_ids == -100] = self.__tokenizer.pad_token_id

        pred_str = self.__tokenizer.batch_decode(pred_ids, skip_special_tokens = True)
        label_str = self.__tokenizer.batch_decode(label_ids, skip_special_tokens = True)

        wer = 100 * self.__metric.compute(predictions = pred_str, references = label_str)

        return {"wer": wer}
    
    def training(self, common_voice):
        common_voice = common_voice.map(self.prepare_dataset, remove_columns=common_voice.column_names["train"], num_proc=1)
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.__processor,
            decoder_start_token_id=self.__model.config.decoder_start_token_id,
        )

        training_args = Seq2SeqTrainingArguments(
            output_dir="./whisper-en_students",  # change to a repo name of your choice
            per_device_train_batch_size=16,
            gradient_accumulation_steps=1,  # increase by 2x for every 2x decrease in batch size
            learning_rate=1e-5,
            warmup_steps=500,
            max_steps=4000,
            gradient_checkpointing=True,
            fp16=True,
            evaluation_strategy="steps",
            per_device_eval_batch_size=8,
            predict_with_generate=True,
            generation_max_length=225,
            save_steps=1000,
            eval_steps=1000,
            logging_steps=25,
            report_to=["tensorboard"],
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
        )

        trainer = Seq2SeqTrainer(
            args=training_args,
            model=self.__model,
            train_dataset=common_voice["train"],
            eval_dataset=common_voice["test"],
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            tokenizer=self.__processor.feature_extractor,
        )

        trainer.train()

if __name__ == '__main__':
    whisper_model = Whisper("openai/whisper-small")

    common_voice = whisper_model.load_dataset()
    common_voice = common_voice.cast_column("audio", Audio(sampling_rate=16000))
    whisper_model.training(common_voice)
