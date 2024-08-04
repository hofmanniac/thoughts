from datetime import datetime
from time import sleep
from abc import ABC, abstractmethod

from openai import Stream

class PromptMessage(ABC):
    
    @abstractmethod
    def format_for_api(self):
        pass

    @property
    @abstractmethod
    def content(self):
        pass
    
    @property
    @abstractmethod
    def speaker(self):
        pass

    @property
    @abstractmethod
    def embedding(self):
        pass

    @property
    @abstractmethod
    def message_id(self):
        pass

    @abstractmethod
    def print_content(self):
        pass

class SystemMessage(PromptMessage):
    def __init__(self, content: str = None):
        self._content = content
        self._embedding = None
        self.message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self._message_id = str(self.message_time)
    def format_for_api(self):
        # return {"system": self._content}
        return {"role": "system", "content": self._content}

    def print_content(self, speed: int = 0):
        if self.content is not None:
            print(f'{self.speaker}:', end=" ")
            console_type(text=self.content, typing_speed=speed)

    @property
    def content(self):
        return self._content
    
    @content.setter
    def content(self, value):
        self._content = value

    @property
    def speaker(self):
        return "System"
    
    @property
    def embedding(self):
        return self._embedding
    
    @embedding.setter
    def embedding(self, value):
        self._embedding = value

    @property
    def message_id(self):
        return self._message_id
    
    @message_id.setter
    def message_id(self, value):
        self._message_id = value

class HumanMessage(PromptMessage):

    def __init__(self, content: str = None):
        self._content = content
        self._embedding = None
        self.message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self._message_id = str(self.message_time)
    
    def format_for_api(self):
        return {"role": "user", "content": self._content}

    def print_content(self, speed: int = 0):
        if self.content is not None:
            print(f'{self.speaker}:', end=" ")
            console_type(text=self.content, typing_speed=speed)

    @property
    def content(self):
        return self._content
    
    @content.setter
    def content(self, value):
        self._content = value

    @property
    def speaker(self):
        return "Human"
    
    @property
    def embedding(self):
        return self._embedding
    
    @embedding.setter
    def embedding(self, value):
        self._embedding = value

    @property
    def message_id(self):
        return self._message_id
    
    @message_id.setter
    def message_id(self, value):
        self._message_id = value

    def to_dict(self):
        return {
            "message-id": self.message_id,
            "speaker": self.speaker,
            "message-time": self.message_time,
            "content": self.content,
            "embedding": self.embedding,
            '__class__': self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        result = HumanMessage(content=data["content"])

        result.message_id = data["message-id"]
        result.message_time = data["message-time"]
        result.embedding = data["embedding"]
        
        return result
    
class AIMessage(PromptMessage):
    def __init__(self, content: str = None, completion: Stream = None):
        self._content = content
        self._embedding = None
        self.message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self._message_id = str(self.message_time)
        self.completion = completion

    def format_for_api(self):
        return {"role": "assistant", "content": self._content}
    
    def _get_content(self, print_content: bool = False, speed: int = 0):
        if print_content:
            print("")
        if self._content is not None:
            if print_content:
                print(f'{self.speaker}:', end=" ")
                console_type(text=self._content, typing_speed=speed)
                print("")
        elif self.completion is not None:
            response_text = ""
            for chunk in self.completion:
                if len(chunk.choices) == 0:
                    continue
                if chunk.choices[0].delta.content:
                    # print(chunk.choices[0].delta.content, end="", flush=True)
                    delta_content = chunk.choices[0].delta.content
                    response_text += delta_content
                    if print_content:
                        console_type(text=delta_content, typing_speed=speed)
            if print_content:
                print("")
            self._content = response_text
        return self._content

    def print_content(self, speed: int = 0):
        self._get_content(print_content=True, speed=speed)

    @property
    def content(self):
        return self._get_content()
    @content.setter
    def content(self, value):
        self._content = value

    @property
    def speaker(self):
        return "AI"

    @property
    def embedding(self):
        return self._embedding 
    @embedding.setter
    def embedding(self, value):
        self._embedding = value

    @property
    def message_id(self):
        return self._message_id
    @message_id.setter
    def message_id(self, value):
        self._message_id = value

    def to_dict(self):
        return {
            "message-id": self.message_id,
            "speaker": self.speaker,
            "message-time": self.message_time,
            "content": self.content,
            "embedding": self.embedding,
            '__class__': self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        result = AIMessage(content=data["content"])

        result.message_id = data["message-id"]
        result.message_time = data["message-time"]
        result.embedding = data["embedding"]

        return result

        # return cls(name=data['name'], age=data['age'])
        
# def create_message(speaker: str, text: str):
#     message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
#     return {"speaker": speaker, "text": text, "time": message_time}

def console_type(text: str, typing_speed: int = 0):
    if typing_speed == 0:
        print(text)
    else:
        message_text = text
        for char in message_text:
            print(char, end="")
            sleep(typing_speed)

def console_input(console_prompt: str = "YOU:"):
    print("")
    text = input(console_prompt + " ")
    message = HumanMessage(content=text)
    # message = create_message("Human", text)
    return message