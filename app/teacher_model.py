import requests
import json

TYPE_MESSAGE = {"GET": "/models", "POST": "/chat/completions"}

class TeacherModel:
    def __init__(self):
        self.port = 8000
        self.address = 'localhost'
        self.type_message = TYPE_MESSAGE["POST"]
        self.url = f'http://{self.address}:{self.port}/v1{self.type_message}'
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.model = "models/llama3_q4_lora_chp1600_TheBigSix"
        self.temperature = 1.0
        self.top_p = 0.7
        self.max_tokens = 150

    def test_connection(self):
        headers = {
            'accept': 'application/json'
        }
        self.update_url(type_message=TYPE_MESSAGE["GET"])
        response = requests.get(self.url, headers=headers)
        if response.status_code == 200:
            print("Connection successful")
            return True
        else:
            print(f"Error connection with teacher model: {response.status_code}")
            return False

    def update_url(self, address="", port="", type_message=""):
        self.address = address if address else self.address
        self.port = port if port else self.port
        self.type_message = type_message if type_message else self.type_message
        self.url = f'http://{self.address}:{self.port}/v1{self.type_message}'

    def format_messages(self, messages):
        formatted_messages = []
        for message in messages:
            formatted_message = {
                "role": message["role"],    # "user", "assistant" or "system"
                "content": message["content"],
                "tool_calls": []
            }
            formatted_messages.append(formatted_message)
        return formatted_messages    
    
    def get_response(self, messages):
        self.update_url(type_message=TYPE_MESSAGE["POST"])
        data = {
            "model": self.model,
            "messages": messages,   # messages must be formatted in the required format
            "tools": [],
            "do_sample": True,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": 1,                 # number of completions (responses) to generate
            "max_tokens": self.max_tokens,
            "stream": False
        }

        print(data)
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code}"
        
    def format_response(self, response):
        return response["choices"][0]["message"]["content"]



def test():
    teacher = TeacherModel()
    messages = [
        {
            "role": "system",
            "content": "You are a kind and helpful teacher who is always ready to help students with their questions."
        },
        {
            "role": "user",
            "content": "Hello teacher"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help you today?"
        },
        {
            "role": "user",
            "content": "I need help to understand the concept of gravity."
        }
    ]
    # formatted_messages = teacher.format_messages(messages)
    # response = teacher.get_response(formatted_messages)
    # response = teacher.format_response(response)
    # print(response)
    
    #teacher.test_connection()


if __name__ == "__main__":
    test()