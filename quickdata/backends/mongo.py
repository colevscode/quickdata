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
        return self # for chaining


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
        if model and 'id' in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop('id')
            model[self.idField] = idval
        return self.mongo[self.dbName][self.colName].save(model)


    def getItem(self, modelId):
        '''
        obviously this is quite inefficient. Later I should implement a simple
        cache to keep these accesses from hitting the db each time
        '''
        model = self.mongo[self.dbName][self.colName].find_one(modelId)
        if model and self.idField in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop(self.idField)
            model['id'] = idval
        return model


    def delete(self, model):
        return self.mongo[self.dbName][self.colName].remove(model.id)


    def len(self):
        return self.mongo[self.dbName][self.colName].count()


    def iter(self):
        for data in self.mongo[self.dbName][self.colName].find():
            yield data


    def find(self, query, limit=None):
        if 'id' in query and self.idField != 'id':
            query = copy(query)
            query[self.idField] = query['id']
            del query['id']

        cursor = self.mongo[self.dbName][self.colName].find(query)
        if limit:
            cursor.limit(limit)
        for data in cursor:
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

