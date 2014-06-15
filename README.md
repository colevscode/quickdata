quickdata
==========

Python document based persistence inspired by backbone.js with dict and object syntax. 

## Use

Here's a typical setup:

	from quickdata import Collection, Model, CachedMongoBackend

	class Thing(Model):
	    pass

	class Things(Collection):
	    modelClass=Thing

	Things().setBackend(CachedMongoBackend, **mongo_stuff)




## Reference


## Credits


