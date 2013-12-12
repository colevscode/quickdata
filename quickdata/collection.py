__all__ = ['Collection', 'CollectionError', 'CollectionUnexpectedError']

from utils import errorutils
from model import Model
from backends.default import DefaultBackend


class CollectionError(errorutils.UnexpectedError):
    pass

class CollectionUnexpectedError(errorutils.UnexpectedError):
    pass
    

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class Collection(object):
    '''
    Abstract base collection class. Subclasses should implement syncronizing the 
    collection with a database.
    '''
    __metaclass__ = Singleton

    modelClass = Model
    classField = 'class'
    backend = None


    def setBackend(self, backend=None, **kwargs):
        kwargs.update(colName=self.__class__.__name__)
        backend = DefaultBackend() if backend == None else backend(**kwargs)
        self.backend = backend


    def toModel(self, modelOrId):
        '''
        If passed an id, converts to the model for that id. If passed a model
        just returns the model. Primarily used internally.
        '''
        if isinstance(modelOrId, Model):
            return modelOrId
        else:
            return self[modelOrId]


    def toId(self, modelOrId):
        '''
        If passed a model, returns its id otherwise returns the id.
        Primarily used internally.
        '''
        if isinstance(modelOrId, Model):
            return modelOrId['id']
        else:
            return modelOrId


    def makeId(self, model):
        '''
        Generates a new unique id for this collection.
        '''
        while True:
            newid = self._do_makeId(model)
            try:
                exists = self[newid]
            except KeyError:
                return newid
            if not exists:
                return newid


    def createClass(self, cls, *args, **kwargs):
        '''
        Creates a new Model of the given class and adds it
        to the collection. Calls the Model's __init__ method.
        '''
        newModel = cls(*args, **kwargs)
        self.add(newModel)
        return newModel


    def create(self, *args, **kwargs):
        '''
        Creates a new Model of this collection's modelClass and adds it
        to the collection. Calls the Model's __init__ method.
        '''
        return self.createClass(self.modelClass, *args, **kwargs)


    def getClass(self, data):
        '''
        returns a model's class by selecting it from the list of modelClasses
        '''
        if not hasattr(self, 'modelClasses') or not self.modelClasses:
            return self.modelClass
        else:
            classnames = map(lambda x: (x.__name__, x), self.modelClasses)
            classname = data.get(self.classField)
            try:
                return dict(classnames)[classname]
            except KeyError:
                return classnames[0][1]


    def get(self, modelId, default=None):
        '''
        Gets a model stored in this collection by modelId
        '''
        try:
            return self[modelId]
        except KeyError:
            return default


    def add(self, model):
        '''
        Adds a model to this collection. Note: this leaves it up to the 
        subclass to assign an Id.
        '''

        # check to make sure the id is unique
        try:
            if model.id in self:
                raise CollectionError("id %s already exists in collection" %\
                                       model.id)
        except AttributeError:
            pass

        model._collection = self
        return self._do_add(model)


    def __contains__(self, modelOrId):
        modelId = self.toId(modelOrId)
        try:
            return self[modelId]
        except KeyError:
            return False


    def _modelFromData(self, data):
        modelclass = self.getClass(data)
        model = modelclass.__new__(modelclass)
        model.unpack(**data)
        model._collection = self
        return model


    def __getitem__(self, modelId):
        '''
        obviously this is quite inefficient. Later I should implement a simple
        cache to keep these accesses from hitting the db each time
        '''
        data = self._do_getItem(modelId)
        if not data:
            raise KeyError
        return self._modelFromData(data)


    def __iter__(self):
        for data in self._do_iter():
            yield self._modelFromData(data)


    def find(self, query, limit=None, **kwargs):
        params = {'limit':limit} if limit else {}
        params.update(**kwargs)

        for data in self._do_find(query, **params):
            yield self._modelFromData(data)


    def __delitem__(self, modelOrId):
        model = self.toModel(modelOrId)
        self._do_delete(model)



    # Backend functions to implement -----------------------

    def _check_backend(self):
        if not hasattr(self, 'backend') or self.backend == None:
            raise CollectionError("backend not configured")


    def _do_makeId(self, model):
        self._check_backend()
        return self.backend.make_Id(model)

    def _do_add(self, model):
        self._check_backend()
        return self.backend.add(model)

    def _do_saveModel(self, model):
        self._check_backend()
        return self.backend.saveModel(model)

    def _do_delete(self, model):
        self._check_backend()
        return self.backend.delete(model)

    def _do_getItem(self, modelId):
        self._check_backend()
        return self.backend.getItem(modelId)

    def _do_iter(self):
        self._check_backend()
        return self.backend.iter()

    def _do_find(self, query):
        self._check_backend()
        return self.backend.find(query)

    def __len__(self):
        self._check_backend()
        return self.backend.len()


