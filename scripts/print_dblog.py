from replit import db
from replit.database.database import ObservedList

for x in db['x:logger']:
    if (type(x) is ObservedList):
        print(list(x))
    else:
        print(x)
