import torch
import evaluate

from typing import Any
from transformers import Seq2SeqTrainer, WhisperTokenizer, WhisperProcessor, WhisperFeatureExtractor, Seq2SeqTrainingArguments, TrainerCallback, TrainingArguments, TrainerControl, TrainerState
from transformers.trainer_utils import PREFIX_CHECKPOINT_DIR
from datasets import load_dataset
import datasets

from dataclasses import dataclass
from typing import Any, Dict, List, Union

from datasets import load_dataset, load_from_disk

import os

from transformers import WhisperForConditionalGeneration, EarlyStoppingCallback

from peft import LoraConfig, LoraConfig, get_peft_model

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

@dataclass
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
        self.__model = WhisperForConditionalGeneration.from_pretrained(model_id)

        self.__model.generation_config.language = "english"
        self.__model.generation_config.task = "transcribe"

        self.__model.generation_config.forced_decoder_ids = None

        self.__model.to(device)

        self.__feature_extractor = WhisperFeatureExtractor.from_pretrained(model_id)
        self.__processor = WhisperProcessor.from_pretrained(model_id, language="english", task="transcribe")
        self.__tokenizer = WhisperTokenizer.from_pretrained(model_id, language="english", task="transcribe")
        self.__metric = evaluate.load("wer")

        lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"], lora_dropout=0.00, bias="none")

        self.__model.enable_input_require_grads()
        self.__model = get_peft_model(self.__model, lora_config)
        self.__model.print_trainable_parameters()

        print(self.__model.config.max_length, flush=True)
        self.__model.config.max_length = 800
        print(self.__model.config.max_length, flush=True)

    def load_dataset(self):
        common_voice = load_dataset("audiofolder", data_dir=os.path.join("C"))
        return common_voice

    def prepare_dataset(self, batch):
        #print(batch, flush=True)
        audio = batch["audio"]
        batch["input_features"] = self.__feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
        batch["labels"] = self.__tokenizer(batch["sentence"]).input_ids

        batch["input_length"] = len(batch["audio"]['array'])
        batch["labels_length"] = len(self.__tokenizer(batch["sentence"], add_special_tokens=False).input_ids)

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
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.__processor,
            decoder_start_token_id=self.__model.config.decoder_start_token_id,
        )

        class SavePeftModelCallback(TrainerCallback):
            def on_save(
                self,
                args: TrainingArguments,
                state: TrainerState,
                control: TrainerControl,
                **kwargs,
            ):
                checkpoint_folder = os.path.join("LoRA_Test", f"{PREFIX_CHECKPOINT_DIR}-{state.global_step}")
        
                peft_model_path = os.path.join(checkpoint_folder, "adapter_model")
                kwargs["model"].save_pretrained(peft_model_path)
        
                pytorch_model_path = os.path.join(checkpoint_folder, "pytorch_model.bin")
                if os.path.exists(pytorch_model_path):
                    os.remove(pytorch_model_path)
                return control

        callbacks = [EarlyStoppingCallback(early_stopping_patience=5), SavePeftModelCallback]

        training_args = Seq2SeqTrainingArguments(
            output_dir="./whisper-v3-LoRA-en_students_test_2",  # change to a repo name of your choice
            per_device_train_batch_size=8,
            gradient_accumulation_steps=1,  # increase by 2x for every 2x decrease in batch size
            learning_rate=1e-5,
            warmup_steps=50,
            max_steps=100000,
            gradient_checkpointing=True,
            fp16=True,
            evaluation_strategy="steps",
            per_device_eval_batch_size=8,
            predict_with_generate=True,
            #generation_max_length=225,
            save_steps=500,
            eval_steps=500,
            logging_steps=25,
            report_to=["tensorboard"],
            remove_unused_columns=False,
            label_names=["labels"],
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
            push_to_hub=True,
            #callbacks=callbacks
        )

        trainer = Seq2SeqTrainer(
            args=training_args,
            model=self.__model,
            train_dataset=common_voice["train"],
            eval_dataset=common_voice["validation"],
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            tokenizer=self.__processor.feature_extractor,
            callbacks=callbacks,
        )

        self.__processor.save_pretrained(training_args.output_dir)

        trainer.train()

        kwargs = {
            "dataset_tags": "Gabi00/english-mistakes",
            "dataset": "English-mistakes",  # a 'pretty' name for the training dataset
            "dataset_args": "config: eng, split: test",
            "language": "eng",
            "model_name": "Whisper Small Eng - Gabriel Mora",  # a 'pretty' name for our model
            "finetuned_from": "openai/whisper-small",
            "tasks": "automatic-speech-recognition",
        }

        trainer.push_to_hub(**kwargs)
        trainer.save_model()


if __name__ == '__main__':
    whisper_model = Whisper("openai/whisper-large-v3")
    common_voice = load_from_disk("map/")

    whisper_model.training(common_voice)