__all__ = ['MongoBackend', 'CachedMongoBackend']

import string

from copy import copy
from ..utils import randutils
from ..utils.cacheutils import memoize_with_expiry

from base import BaseBackend

class MongoBackend(BaseBackend):
    '''
    Implements a collection using a mongo database backend. 
    '''

    idField = '_id'


    def _id2idfield(self, data):
        if data and 'id' in data and self.idField != 'id':
            data = copy(data)
            idval = data.pop('id')
            data[self.idField] = idval
        return data


    def _idfield2id(self, data):
        if data and self.idField in data and self.idField != 'id':
            data = copy(data)
            idval = data.pop(self.idField)
            data['id'] = idval
        return data


    def __init__(self, colName, 
                 mongo=None, host="localhost:27017", 
                 user="", passwd="", dbName="collections"):

        from pymongo import MongoClient
        if not mongo:
            auth = '%s:%s@' % (user, passwd) if user else ''
            uri  = 'mongodb://' + auth + host + "/" + dbName
            self.mongo = MongoClient(host=uri)
        else:
            self.mongo = mongo
        self.dbName = dbName
        super(MongoBackend, self).__init__(colName)


    # Backend functions -----------------------

    def makeId(self, model):
        '''
        Creates a random uuid for an Id.
        '''
        return unicode(randutils.gen_random_str(12, string.ascii_lowercase+\
                                                string.digits))


    def add(self, model):
        '''
        Adds a model to this collection and the database. Relies on the 
        super class' save functionality to assign an id.
        '''
        return model.save()


    def saveModel(self, model):
        model = self._id2idfield(model)
        return self.mongo[self.dbName][self.colName].save(model)


    def getItem(self, modelId):
        '''
        obviously this is quite inefficient. Later I should implement a simple
        cache to keep these accesses from hitting the db each time
        '''
        model = self.mongo[self.dbName][self.colName].find_one(modelId)
        model = self._idfield2id(model)
        return model


    def delete(self, model):
        return self.mongo[self.dbName][self.colName].remove(model.id)


    def len(self):
        return self.mongo[self.dbName][self.colName].count()


    def iter(self):
        for data in self.mongo[self.dbName][self.colName].find():
            yield data


    def find(self, query, limit=None):
        query = self._id2idfield(query)
        cursor = self.mongo[self.dbName][self.colName].find(query)
        if limit:
            cursor.limit(limit)
        for data in cursor:
            data = self._idfield2id(data)
            yield data


class CachedMongoBackend(MongoBackend):
    '''
    Implements a collection using a mongo database backend. 
    '''
    cache = {}

    def __init__(self, cachettl=300, **kwargs):
        super(CachedMongoBackend, self).__init__(**kwargs)
        wrapper = memoize_with_expiry(self.cache, expiry_time=cachettl)
        self.getItem = wrapper(self.getItem)

