
from thoughts.cortex import Cortex

class Nova:
    '''Nova is an AI assistant designed to help with various tasks.'''
    
    cortex = Cortex("nova")

    def respond(self, prompt):
        '''Generate a response from Nova based on the given prompt.'''
        response = self.cortex.respond(prompt)
        return response
    
    def chat(self):
        '''Start an interactive chat session with Nova.'''
        print("Welcome to Nova! Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            response = self.respond(user_input)
            print(f"Nova: {response}")