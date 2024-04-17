from app.rag.RAGFactory import RAGFactory
from app.audio_downloader import AudioDownloader
from app.audio_extractor import AudioExtractor
from app.chat_llm import Chat
from app.file_manager import FileManager
import os
import shutil

from app.study_plan_creator import StudyPlanCreator


class EnglishTutor:
    def __init__(self, llm_model_id="google/gemma-1.1-2b-it", rag_engine="ragatouille"):
        # LLM
        self.__llm_model_id = llm_model_id
        self.__chat_llm = None

        # RAG
        self.__rag_engine = rag_engine
        self.__rag_factory = RAGFactory()

        self.__speakers_context = None
        self.__audio_extractor = None
        self.__audio_downloader = None
        self.__file_manager = FileManager()

        self.cache_files_paths = {'diarization_result': 'cache/diarization_result.json',
                                  'study_plan': 'cache/study_plan.json'}

    def __get_rag_engine(self):
        return self.__rag_factory.get_instance(self.__rag_engine)

    def __get_chat_llm(self):
        if self.__chat_llm is None:
            self.__chat_llm = Chat(self.__llm_model_id)

        print(f"Model {self.__llm_model_id} loaded for Chat LLM")
        return self.__chat_llm

    def __get_audio_downloader(self):
        if self.__audio_downloader is None:
            self.__audio_downloader = AudioDownloader()

        return self.__audio_downloader

    # ====================
    # = Audio Extractor Region
    # ====================

    def get_speakers_context(self, file_name="audio/extracted_audio.wav"):
        if self.__speakers_context is None:
            if self.__audio_extractor is None:
                self.__audio_extractor = AudioExtractor()

            diarization = self.__file_manager.read_from_json_file(self.cache_files_paths['diarization_result'])

            if diarization is None:
                diarization = self.__audio_extractor.perform_diarization(file_name)
                self.__file_manager.save_to_json_file(self.cache_files_paths['diarization_result'], diarization)

            if diarization is not None:
                self.__speakers_context = self.__audio_extractor.get_diarization_grouped_by_speaker(diarization)

        return self.__speakers_context

    def clean_cache(self):
        self.__speakers_context = None
        chat_llm = self.__get_chat_llm()
        chat_llm.clean_chat_history()

        cache_folder = 'cache'
        if os.path.isdir(cache_folder):
            for filename in os.listdir(cache_folder):
                file_path = os.path.join(cache_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f'Can\'t delete {file_path}. The reason: {e}')

        ragatouille_folder = '.ragatouille/colbert/indexes/tutor/'
        if os.path.isdir(ragatouille_folder):
            try:
                shutil.rmtree(ragatouille_folder)
                print(f"Successfully deleted the folder: {ragatouille_folder}")
            except Exception as e:
                print(f'Failed to delete the folder {ragatouille_folder}. Reason: {e}')

    def get_llm_model_id(self):
        return self.__llm_model_id

    def get_rag_engine_id(self):
        return self.__rag_engine

    # ====================
    # = Chat LLM Region
    # ====================

    def get_answer(self, content, max_new_tokens=250):
        chat_llm = self.__get_chat_llm()
        return chat_llm.get_answer(content, max_new_tokens)

    def update_chat_history(self, text):
        chat_llm = self.__get_chat_llm()
        return chat_llm.update_chat_history(text)

    def get_chat_history(self):
        chat_llm = self.__get_chat_llm()
        return chat_llm.get_chat_history()

    # ====================
    # = Rag FAISS Region
    # ====================

    def search_in_index(self, query, k=5):
        rag_engine = self.__get_rag_engine()
        return rag_engine.search(query, k)

    def get_supported_rag_engines(self):
        return self.__rag_factory.get_supported_types()

    def set_rag_engine(self, rag_engine):
        self.__rag_engine = rag_engine

    def set_llm_model_id(self, llm_model_id):
        self.__llm_model_id = llm_model_id
        self.__chat_llm = None

    # ====================
    # = AudioDownloader Region
    # ====================
    def download_audio(self, video_url, output_filename="audio/extracted_audio"):
        audio_downloader = self.__get_audio_downloader()
        audio_downloader.download_audio(video_url, output_filename)

    def get_video_info(self, video_url):
        audio_downloader = self.__get_audio_downloader()
        return audio_downloader.get_video_info(video_url)

    def get_study_plan(self, speakerId: str) -> list:
        study_plan = self.__file_manager.read_from_json_file(self.cache_files_paths['study_plan'])

        if study_plan:
            print("Study plan loaded from file.")
            return study_plan

        chat_llm = self.__get_chat_llm()
        plan_creator = StudyPlanCreator(chat_llm)
        speakers_context = self.get_speakers_context()
        study_plan = plan_creator.create_study_plan(speakers_context, speakerId)

        self.__file_manager.save_to_json_file(self.cache_files_paths['study_plan'], study_plan)
        return study_plan
