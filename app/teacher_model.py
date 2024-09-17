import requests
import json

TYPE_MESSAGE = {"GET": "/models", "POST": "/chat/completions"}

class TeacherModel:
    def __init__(self, address="localhost", port=8000, model="Transducens/kind_teacher", temperature=1.0, top_p=0.7, max_tokens=150):
        try:
            self.port = port
            self.address = address
            self.type_message = TYPE_MESSAGE["POST"]
            self.url = f'http://{self.address}:{self.port}/v1{self.type_message}'
            self.headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            self.model = model # "../kind_teacher_server/models/llama3_q4_lora_chp1600_TheBigSix"
            self.temperature = temperature
            self.top_p = top_p
            self.max_tokens = max_tokens
        except:
            raise Exception("Cannot connect teacher")

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

    # Input type: [['Hello teacher', 'Hello student'], ['I need help with english', 'What problems do you have?'], ...]
    # Output type: [{'role': 'user', 'content': 'Hello teacher', 'tool_calls': []}, {'role': 'assistant', 'content': 'Hello student'}, ...]
    def format_messages(self, system_message="", messages=[]):
        print("====================================")
        print(messages)
        print("====================================")
        
        formatted_messages = []
        if system_message:
            formatted_message_system = {
                "role": "system",
                "content": system_message
            }
            formatted_messages.append(formatted_message_system)

        for message in messages:
            formatted_message_user = {
                "role": "user",    # "user", "assistant" or "system"
                "content": message[0],
                "tool_calls": []
            }
            
            formatted_messages.append(formatted_message_user)
            if len(message) == 2:
                formatted_message_assistant = {
                    "role": "assistant",
                    "content": message[1],
                }
            
                formatted_messages.append(formatted_message_assistant)

        print("====================================")
        print(formatted_messages)
        print("====================================")
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
        print("====================================")
        print(response)
        print("====================================")
        return response["choices"][0]["message"]["content"]



def test():
    teacher = TeacherModel()
    
    teacher.test_connection()
    
    messages = [
        {
            "role": "system",
            "content": "A friendly and supportive teacher guiding students patiently and encouraging their efforts."
        },
        {
            "role": "user",
            "content": "Hello, I am SPEAKER"
        },
        {
            "role": "assistant",
            "content": "Hello! I am your English tutor. I will help you to learn English. Are you ready?"
        },
        {
            "role": "user",
            "content": "I need help to understand the concept of gravity."
        }
    ]
    formatted_messages = teacher.format_messages(messages)
    response = teacher.get_response(formatted_messages)
    response = teacher.format_response(response)
    print(response)
    
    


# if __name__ == "__main__":
#     test()