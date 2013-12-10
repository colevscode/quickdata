__all__ = ['Model', 'ModelUnexpectedError']

from copy import copy
import inspect

from utils import error as errorutils
from utils import time as timeutils

## ERRORS ---------------------------------------------------------------------

class ModelUnexpectedError(errorutils.UnexpectedError):
    pass


## MODEL CLASSES --------------------------------------------------------------

class Model(dict):
    '''
    Abstract base model class. The Model is a subclass of dict, where any
    item in the dictionary will be saved in this model's database object.

    Models are members of a Collection. All the database CRUD functionality is 
    implemented on the collection.

    Subclasses may override the idField, which will determine what attribute
    is used as the primary key for the model.

    Subclasses may override the fields attribute in order to provide a list of 
    additional keys that will be stored in the database. This list also sets un
    dot notation so you can easily refer to elements in the dict. 

    Caution:
    Attributes not listed in the fields database won't be persisted if assigned 
    using dot notation. Instead they will just be added as regular untracked 
    attributes to the instance. Attributes added using dictionary key/value
    notation will always be persisted.

    example: 

    idField = 'userid'
    fields = ['name', 'address']

    ... will have and id field of 'userid', a required 'name' field and an
    optional 'address' field.

    A model's __init__ method is called both when a new Model is created, and
    when a model is fetched from the database. As a result init has a single
    **data parameter. Sometimes a subclass will want to provide custom __init__ 
    parameters. In that case it should override unpack() to call self.__init__, 
    filling in those parameters. Unpack is only called when creating models 
    from data fetched from the database.
    '''

    fields = ['id', 'created', 'modified', 'class']
    computed_fields = {}


    @classmethod
    def _accum_attr(cls, attr):
        values = None
        for supr in inspect.getmro(cls):
            if hasattr(supr, attr):
                thisval = getattr(supr, attr)
                if type(thisval) == list:
                    thisval = set(thisval)
                if values:
                    values.update(thisval)
                else:
                    values = thisval
        return list(values) if type(values) == set else values


    @classmethod
    def getFields(cls):
        return cls.getAllFields(include_computed=False)


    @classmethod
    def getAllFields(cls, include_computed=True):
        if not hasattr(cls, '_fields'):
            cls._fields = cls._accum_attr('fields')
        fields = copy(cls._fields)
        if include_computed:
            fields += cls.getComputedFields().keys()
        return fields


    @classmethod
    def getComputedFields(cls):
        try:
            return cls._computed_fields
        except AttributeError:
            cls._computed_fields = cls._accum_attr('computed_fields')
            return cls._computed_fields


    def computeField(self, attr):
        fn = self.getComputedFields()[attr]
        return fn(self)


    def __init__(self, **data):
        '''
        Initialize an instance of a Model from data.
        '''
        data = copy(data)

        # the id field should't contain an empty value
        try:
            if not data['id']:
                del data['id']
        except KeyError:
            pass

        super(Model, self).__init__(**data)


    def __unicode__(self):
        try:
            return unicode(self.id)
        except AttributeError:
            return super(Model, self).__unicode__()


    def __str__(self):
        return self.__unicode__().encode('utf-8')


    def unpack(self, **data):
        '''
        Initialize an instance of a Model from data. Called whenever a model is 
        fetched from the database.
        '''
        self.__init__(**data)


    def __getattr__(self, attr):
        ''' Maps dot notation to dict notation '''
        if attr in self.getAllFields():
            try:
                if attr in self.getComputedFields():
                    return self.computeField(attr)
                else:
                    return self[attr]
            except KeyError:
                raise AttributeError("Could not access attribute %s" % attr)
        else:
            raise AttributeError("Could not access attribute %s" % attr)


    def __setattr__(self, attr, value):
        ''' Maps dot notation to dict notation '''
        if attr in self.getAllFields():
            if attr in self.getComputedFields():
                raise AttributeError("Could not set computed attr %s" % attr)
            self[attr] = value
        else:
            return super(Model, self).__setattr__(attr, value)


    def __getitem__(self, key):
        if key in self.getComputedFields():
            return self.computeField(key)
        else:
            return super(Model, self).__getitem__(key)


    def __setitem__(self, key, value):
        if key in self.getComputedFields():
            raise KeyError("Could not set value for computed key %s" % key)
        super(Model, self).__setitem__(key, value)


    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, AttributeError):
            return default


    def toData(self, include_computed=False):
        ''' Returns a dictionary representation of the model's data.

        This representation will only include the model's fields and
        computed_fields.
        '''
        fields = self.getAllFields(include_computed=include_computed) + ['_id']
        if self._collection:
            fields += [self._collection.classField]
        cfields = self.getComputedFields().keys() if include_computed else []
        existing_fields = self.keys() + cfields

        class NoComputedValue(object): 
            pass

        getval = lambda k: self.get(k, NoComputedValue())
        result = list((k, getval(k)) for k in fields if k in existing_fields)
        result = dict(filter(lambda t: type(t[1]) != NoComputedValue, result))
        return result

    # def iterkeys(self):
    #     for k in super(Model, self).iterkeys():
    #         yield k
    #     for k in self.getComputedFields():
    #         yield k


    # def iteritems(self):
    #     for k, v in super(Model, self).iteritems():
    #         yield k, v
    #     for k in self.getComputedFields():
    #         yield k, self.computeField(k)


    # def itervalues(self):
    #     for v in super(Model, self).itervalues():
    #         yield v
    #     for k in self.getComputedFields():
    #         yield self.computeField(k)


    # def __iter__(self):
    #     for k in self.iterkeys():
    #         yield k


    # def keys(self):
    #     return list(self.iterkeys())


    # def items(self):
    #     return list(self.iteritems())


    # def values(self):
    #     return list(self.itervalues())


    def isNew(self):
        '''
        Returns true if the model hasn't yet been synchronized to the database.
        '''
        return not self.get('id')


    def _savePrep(self):
        '''
        prepares a model for saving
        '''
        if self._collection == None:
            raise ModelUnexpectedError("Model must be attached to a \
                                        Collection in order to be saved.")

        if self.isNew():
            self.created = timeutils.format_iso_now()
        self.modified = timeutils.format_iso_now()

        # set the id

        if not 'id' in self:
            self['id'] = self._collection.makeId(self)

        # set the class
        
        if not self._collection.classField in self:
            classname = self.__class__.__name__
            classes = [self._collection.modelClass]
            try:
                classes += self._collection.modelClasses
            except AttributeError:
                pass
            classnames = map(lambda x: x.__name__, classes)

            if classname in classnames:
                self[self._collection.classField] = classname
            else:
                raise ModelUnexpectedError("Model class must be one of collection's "+ \
                                           "modelClasses or modelClass")


    def save(self):
        '''
        Stores the model in a database. First creates an id for the model if
        one does not exist.
        '''
        self._savePrep()
        self._collection._do_saveModel(self)


    def fetch(self):
        '''
        Refreshes the model with data from the database. Returns self so it 
        can be chained.
        '''

        if self._collection == None:
            raise ModelUnexpectedError("Model must be attached to a "+\
                                       "Collection in order to be fetched.")

        self.unpack(**self._collection[self.id])

        return self


    def destroy(self):
        '''
        Just removes itself from the collection. Super classes may override
        to do more stuff, but should always call super().destroy()
        '''
        if self._collection:
            del self._collection[self.id]


