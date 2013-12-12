__all__ = ['BaseBackend']

class BaseBackend(object):
    '''
    Does nothing. 
    '''

    def __init__(self, colName, *args, **kwargs):
        self.colName = colName
        super(BaseBackend, self).__init__(*args, **kwargs)

    def makeId(self, model):
        raise NotImplementedError()

    def add(self, model):
        raise NotImplementedError()

    def saveModel(self, model):
        raise NotImplementedError()

    def getItem(self, modelId):
        raise NotImplementedError()

    def delete(self, model):
        raise NotImplementedError()

    def len(self):
        raise NotImplementedError()

    def iter(self):
        raise NotImplementedError()

    def find(self, query, limit=None):
        raise NotImplementedError()


