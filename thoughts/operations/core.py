from abc import abstractmethod

class Operation():
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass