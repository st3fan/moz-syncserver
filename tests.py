#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import uuid
import time
import unittest
import urllib2

import hawk
import requests
import requests.exceptions

DEFAULT_SORTINDEX = 0
DEFAULT_TTL = 2100000000

SERVER = "https://sync.sateh.com"

def call_token_server(server, assertion):
    url = server + "/token/1.0/sync/1.5"
    r = requests.get(url, headers={"Authorization": "BrowserID " + assertion})
    r.raise_for_status()
    return r.json()

def call_mockmyid_server(email, audience):
    url = "http://127.0.0.1:8080/assertion"
    r = requests.get(url, params={"email":email, "audience":audience})
    r.raise_for_status()
    return r.json().get("assertion")

def get_object(token, collection_name, object_id):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, object_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json()

def put_object(token, collection_name, o_id, o):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, o_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "PUT", {"credentials": hawk_credentials, "ext":""})
    r = requests.put(url, headers={"Authorization":hawk_header["field"]}, data=json.dumps(o))
    r.raise_for_status()
    return float(r.text)

def delete_object(token, collection_name, object_id):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, object_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "DELETE", {"credentials": hawk_credentials, "ext":""})
    r = requests.delete(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json()

def post_objects(token, collection_name, objects):
    url = token["api_endpoint"] + "/storage/%s" % collection_name
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "POST", {"credentials": hawk_credentials, "ext":""})
    r = requests.post(url, headers={"Authorization":hawk_header["field"],"Content-Type":"application/json"}, data=json.dumps(objects))
    r.raise_for_status()
    return r.json()

def get_info_collections(token):
    url = token["api_endpoint"] + "/info/collections"
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json()

def random_id():
    return str(uuid.uuid4())

def random_object():
    return {"payload":"This is some payload at %f" % time.time()}

class StorageTest(unittest.TestCase):

    def setUp(self):
        self.email = "%.4f@mockmyid.com" % time.time()
        self.assertion = call_mockmyid_server(self.email, SERVER)
        self.token = call_token_server(SERVER, self.assertion)

    def test_put_object_partial(self):
        # Put a new object
        modified = put_object(self.token, "things", "testid1", {"payload":"testpayload1"})
        self.assertTrue(modified != 0)
        # Fetch it and see if it is correctly filled in
        object = get_object(self.token, "things", "testid1")
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload1")
        self.assertTrue(object["sortindex"] == DEFAULT_SORTINDEX)
        self.assertTrue(object["ttl"] == DEFAULT_TTL)
        self.assertTrue(object["id"] == "testid1")
        self.assertTrue(object["modified"] == modified)

    def test_put_object_full(self):
        # Put a new object
        modified = put_object(self.token, "things", "testid2", {"payload":"testpayload2", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Fetch it and see if it is correctly filled in
        object = get_object(self.token, "things", "testid2")
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload2")
        self.assertTrue(object["sortindex"] == 100)
        self.assertTrue(object["ttl"] == 3600)
        self.assertTrue(object["id"] == "testid2")
        self.assertTrue(object["modified"] == modified)

    def test_put_object_update(self):
        # Put a new object
        modified = put_object(self.token, "things", "testid3", {"payload":"testpayload3", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Put it again with updated fields
        modified = put_object(self.token, "things", "testid3", {"payload":"testpayload3updated"})
        # Fetch it and see if it is correctly filled in
        object = get_object(self.token, "things", "testid3")
        self.assertTrue(modified != 0)
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload3updated")
        self.assertTrue(object["sortindex"] == 100)
        self.assertTrue(object["ttl"] == 3600)
        self.assertTrue(object["id"] == "testid3")
        self.assertTrue(object["modified"] == modified)

    def test_delete_object_existing(self):
        # Put a new object
        modified = put_object(self.token, "things", "testid4", {"payload":"testpayload3", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Delete it
        delete_object(self.token, "things", "testid4")

    def test_delete_object_unknown_collection(self):
        # Delete it with bad collection
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            delete_object(self.token, "thingzzz", "testid4")
        self.assertEqual(context.exception.response.status_code, 404)

    def test_delete_object_unknown_object(self):
        # Delete it with bad collection
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            delete_object(self.token, "things", "testid4zzz")
        self.assertEqual(context.exception.response.status_code, 404)

    # Tests from server-syncstorage/syncstorage/tests/functional/test_storage.py

    def test_get_info_collections(self):
        # Create two collections
        modified1 = put_object(self.token, "col1", random_id(), random_object())
        modified2 = put_object(self.token, "col2", random_id(), random_object())
        # Only those two should be in /info/collections
        collections = get_info_collections(self.token)
        self.assertEqual(len(collections), 2)
        self.assertEqual(collections["col1"], modified1)
        self.assertEqual(collections["col2"], modified2)

if __name__ == "__main__":
    unittest.main()
