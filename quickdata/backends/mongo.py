__all__ = ['MongoBackend']

import string

from copy import copy
from utils import rand as randutils


class MongoBackend(object):
    '''
    Implements a collection using a mongo database backend. 
    '''

    idField = '_id'

    def __init__(self, mongo=None, host="localhost:27017", user="", passwd="", 
                 dbName="collections", colPrefix=""):
        from pymongo import MongoClient
        if not mongo:
            auth = '%s:%s@' % (user, passwd) if user else ''
            uri  = 'mongodb://' + auth + host
            self.mongo = MongoClient(host=uri)
        else:
            self.mongo = mongo
        self.dbName = dbName
        self.colName = colPrefix + self.__class__.__name__
        return self # for chaining


    # Backend functions -----------------------

    def _do_makeId(self, model):
        '''
        Creates a random uuid for an Id.
        '''
        return unicode(randutils.gen_random_str(12, string.ascii_lowercase+\
                                                string.digits))


    def _do_add(self, model):
        '''
        Adds a model to this collection and the database. Relies on the 
        super class' save functionality to assign an id.
        '''
        return model.save()


    def _do_saveModel(self, model):
        if 'id' in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop('id')
            model[self.idField] = idval
        return self.mongo[self.dbName][self.colName].save(model)


    def _do_getItem(self, modelId):
        '''
        obviously this is quite inefficient. Later I should implement a simple
        cache to keep these accesses from hitting the db each time
        '''
        model = self.mongo[self.dbName][self.colName].find_one(modelId)
        if self.idField in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop(self.idField)
            model['id'] = idval
        return model


    def _do_delete(self, model):
        return self.mongo[self.dbName][self.colName].remove(model.id)


    def __len__(self):
        return self.mongo[self.dbName][self.colName].count()


    def _do_iter(self):
        for data in self.mongo[self.dbName][self.colName].find():
            yield data


    def _do_find(self, query, limit=None):
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

    def __init__(self, *args, **kwargs):
        self.cachettl = kwargs.pop('cachettl', 300)
        super(CachedMongoBackend, self).__init__(self, *args, **kwargs)


    def _do_saveModel(self, model):
        
        
        if 'id' in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop('id')
            model[self.idField] = idval
        return self.mongo[self.dbName][self.colName].save(model)


    def _do_getItem(self, modelId):
        '''
        obviously this is quite inefficient. Later I should implement a simple
        cache to keep these accesses from hitting the db each time
        '''
        model = self.mongo[self.dbName][self.colName].find_one(modelId)
        if self.idField in model and self.idField != 'id':
            model = copy(model)
            idval = model.pop(self.idField)
            model['id'] = idval
        return model


    def _do_delete(self, model):
        return self.mongo[self.dbName][self.colName].remove(model.id)

