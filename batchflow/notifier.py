from abc import ABCMeta, abstractmethod
import tqdm

class Notifier(metaclass=ABCMeta):
    """ Abstract class for notifiers. """
    
    @abstractmethod
    def close(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def update(self, *args, **kwargs):
        pass

class TqdmNotifier(tqdm.tqdm, Notifier):
    """ Notifier wrapper for tqdm.tqdm. """

class TqdmNotebookNotifier(Notifier):
    """ Notifier wrapper for tqdm.tqdm_notebook. """
    def __init__(self, *args, **kwargs):
        self._notifier = tqdm.tqdm_notebook(*args, **kwargs)
    
    def close(self):
        self._notifier.close()
    
    def update(self, n):
        self._notifier.update(n)
    
    def __iter__(self):
        return iter(self._notifier)
