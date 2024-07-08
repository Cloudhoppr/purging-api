import pymongo
import pprint

client = pymongo.MongoClient()

db = client.learningdb

coll = db.users

# insert_data = coll.insert_one({ "firstname" : "Trivikram", "age" : 17})
data = coll.find_one({ "age" : 17 })
data_id = data["_id"]

""" print(data, "\n")
pprint.pprint(data)
print()
print(data_id, "\n")
pprint.pprint(data_id) """

# coll.delete_many({"age":17})

for i in coll.find():
    pprint.pprint(i)
