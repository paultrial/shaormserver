from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import os

mongo_url = os.environ.get("DATABASE_URL", "mongodb+srv://wigleytrial:Aerht7pU7Xn8b11M@shaormappcluster.l7swt.mongodb.net/?retryWrites=true&w=majority&appName=shaormappCluster")

def _hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def _verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)


class mongoCRUD():
    def __init__(self, mongoURL, dbName, collection) -> None:
        # = "mongodb://localhost:27017/"
        self.client = MongoClient(mongoURL)
        self.db = self.client[dbName]
        try:
            users = self.db['users']
            if len(list(users.find())) == 0:
                users.insert_one(
                    {'username': 'admin', 'password': _hash_password('admin'), "name": 'Admin'})
            else:
                admin_user = users.find_one({'username': 'admin'})
                if admin_user is None:
                    users.insert_one(
                        {'username': 'admin', 'password': _hash_password('admin'), "name": 'Admin'})

        except Exception as e:
            print(f"Error loading or initialising users from database: {e}")
            exit()

    def check_pwd(self, username, pwd_hash):
        l = list(self.db['users'].find({"username": username}))
        if len(l) == 1:
            if _verify_password(l[0]["password"], pwd_hash):
                return True
        return False

    def _mongo_col_to_list_dict(self, mongo_cur):
        return self._list_to_ss_dict(
            [{k if k != "_id" else "mongo_id": str(d[k]) for k in d.keys()} for d in mongo_cur])

    def _mongo_col_to_dict(self, mongo_cur, single_field=None):
        l = [{k if k != "_id" else "mongo_id": str(
            d[k]) for k in d.keys()} for d in mongo_cur]
        if single_field:
            return {str(d["mongo_id"]): d[single_field] for d in l}
        else:
            return {str(d["mongo_id"]): d for d in l}

    def _list_to_ss_dict(self, list_dict):
        exclude = ["password"]
        ret = {}
        i = 0
        for e in list_dict:
            for x in exclude:
                if x in e:
                    del e[x]
            ret[str(i)] = e
            i += 1
        return ret

    def _create_mongo_update(self, ss_dict):
        return {
            "$set": {k: ss_dict[k] for k in ss_dict.keys() if k != "mongo_id"}
        }

    def _create_mongo_insert(self, ss_dict):
        return {k: ss_dict[k] for k in ss_dict.keys()}

    def add_mongo_doc(self, collection, ss_doc):
        res = self.db[collection].insert_one(self._create_mongo_insert(ss_doc))
        if res.inserted_id is not None:
            return str(res.inserted_id)
        return None

    def update_mongo_doc(self, colletion, ss_doc):
        if "mongo_id" not in ss_doc:
            return False
        ret = self.db[colletion].update_one(
            {"_id": ObjectId(ss_doc["mongo_id"])}, self._create_mongo_update(ss_doc))
        print(ret)
        return True

    def delete_mongo_doc(self, collection, mongo_id):
        res = self.db[collection].delete_one({"_id": ObjectId(mongo_id)})
        return res.deleted_count == 1

    def load_docs(self, collection, fields=None, filter=None):
        if filter:
            filter = {(k if k != "mongo_id" else "_id") : (v if k != "mongo_id" else ObjectId(v)) for k, v in filter.items()}
            return self._mongo_col_to_list_dict(self.db[collection].find(filter, projection=fields))
        else:
            return self._mongo_col_to_list_dict(self.db[collection].find(projection=fields))

    def load_docs_dict(self, collection, fields=None, filter=None):
        if filter:
            filter = {(k if k != "mongo_id" else "_id") : (v if k != "mongo_id" else ObjectId(v)) for k, v in filter.items()}
            return self._mongo_col_to_dict(self.db[collection].find(filter, projection=fields), None if fields is None or len(fields) > 1 else fields[0])
        else:
            return self._mongo_col_to_dict(self.db[collection].find(projection=fields), None if fields is None or len(fields) > 1 else fields[0])

    def add_doc(self, state, state_col_name, empty_doc):
        try:
            new_id = str(
                int(max(dict(state[state_col_name].items()).keys(), key=int)) + 1)
        except:
            new_id = "0"
        u = empty_doc
        id = self.add_mongo_doc(state_col_name, u)
        if id:
            u["mongo_id"] = id
            state[state_col_name][new_id] = u
        else:
            print("Error adding to", state_col_name)

    def save_doc(self, state_col_name, context):
        self.update_mongo_doc(state_col_name, context["item"])

    def delete_doc(self, state, state_col_name, context):
        try:
            if self.delete_mongo_doc(state_col_name, context["item"]["mongo_id"]):
                d = state[state_col_name].to_dict()
                del d[context["itemId"]]
                state[state_col_name] = d
            else:
                print("Error deleting from", state_col_name)
        except Exception as e:
            print("Error deleting from", state_col_name, ",", str(e))
