from datetime import datetime
from time import sleep
from abc import ABC, abstractmethod

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

class SystemMessage(PromptMessage):
    def __init__(self, content: str = None):
        self._content = content
        self._embedding = None
        self.message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self._message_id = str(self.message_time)
    def format_for_api(self):
        # return {"system": self._content}
        return {"role": "system", "content": self._content}
    
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

class AIMessage(PromptMessage):
    def __init__(self, content: str = None):
        self._content = content
        self._embedding = None
        self.message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self._message_id = str(self.message_time)
    def format_for_api(self):
        return {"role": "assistant", "content": self._content}
    @property
    def content(self):
        return self._content
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
        
def create_message(speaker: str, text: str):
    message_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    return {"speaker": speaker, "text": text, "time": message_time}

def console_type(message: PromptMessage, typing_speed: int = 0):
    print("")
    if typing_speed is 0:
        print(message.content)
    else:
        message_text = message.content
        print(f'{message.speaker}:', end=" ")
        for char in message_text:
            print(char, end="")
            sleep(typing_speed)

def console_input(console_prompt: str = "YOU:"):
    print("")
    text = input(console_prompt + " ")
    message = HumanMessage(content=text)
    # message = create_message("Human", text)
    return message