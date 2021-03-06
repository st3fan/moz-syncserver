#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import uuid
import time
import unittest
import urllib
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
    return r.json(),r

def call_mockmyid_server(email, audience):
    url = "http://127.0.0.1:8080/assertion"
    r = requests.get(url, params={"email":email, "audience":audience})
    r.raise_for_status()
    return r.json().get("assertion"),r

def delete_collection(token, collection_name, ids=None):
    params = {}
    if ids:
        params["ids"] = ",".join(ids)
    url = token["api_endpoint"] + "/storage/%s" % collection_name
    if len(params) != 0:
        url += "?" + urllib.urlencode(params)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "DELETE", {"credentials": hawk_credentials, "ext":""})
    r = requests.delete(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r

def delete_storage(token):
    url = token["api_endpoint"] + "/storage"
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "DELETE", {"credentials": hawk_credentials, "ext":""})
    r = requests.delete(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r


def get_object(token, collection_name, object_id):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, object_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r

def put_object(token, collection_name, o_id, o):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, o_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "PUT", {"credentials": hawk_credentials, "ext":""})
    r = requests.put(url, headers={"Authorization":hawk_header["field"]}, data=json.dumps(o))
    r.raise_for_status()
    return float(r.text),r

def delete_object(token, collection_name, object_id):
    url = token["api_endpoint"] + "/storage/%s/%s" % (collection_name, object_id)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "DELETE", {"credentials": hawk_credentials, "ext":""})
    r = requests.delete(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r

def post_objects(token, collection_name, objects, content_type="application/json"):
    url = token["api_endpoint"] + "/storage/%s" % collection_name
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "POST", {"credentials": hawk_credentials, "ext":""})
    r = requests.post(url, headers={"Authorization":hawk_header["field"],"Content-Type":content_type}, data=json.dumps(objects))
    #print r.status_code, r.reason, r.text
    r.raise_for_status()
    return r.json(),r

def get_info_collections(token):
    url = token["api_endpoint"] + "/info/collections"
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r

def get_info_collection_counts(token):
    url = token["api_endpoint"] + "/info/collection_counts"
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"]})
    r.raise_for_status()
    return r.json(),r

def get_objects(token, collection_name, full=None, newer=None, limit=None, offset=None, ids=None, accepts="application/json"):
    params={}
    if full:
        params["full"] = "1"
    if newer:
        params["newer"] = ("%.2f" % newer)
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    if ids:
        params["ids"] = ",".join(ids)
    url = token["api_endpoint"] + "/storage/%s" % collection_name + "?" + urllib.urlencode(params)
    hawk_credentials = {"id": str(token["id"]), "key": str(token["key"]), "algorithm":"sha256"}
    hawk_header = hawk.client.header(url, "GET", {"credentials": hawk_credentials, "ext":""})
    r = requests.get(url, headers={"Authorization":hawk_header["field"],"Accepts":accepts})
    r.raise_for_status()
    return r.json(),r


def random_id():
    return str(uuid.uuid4())

def random_object():
    return {"payload":"This is some payload at %f" % time.time()}

def random_object_with_id():
    return {"payload":"This is some payload at %f" % time.time(), "id": random_id()}

def random_objects(n):
    return [{"payload":"This is some payload at %f" % time.time(), "id":random_id()} for i in range(n)]

class StorageTestCase(unittest.TestCase):

    def setUp(self):
        self.email = "%.4f@mockmyid.com" % time.time()
        self.assertion,r = call_mockmyid_server(self.email, SERVER)
        self.token,r = call_token_server(SERVER, self.assertion)

    def test_put_object_partial(self):
        # Put a new object
        modified,r = put_object(self.token, "things", "testid1", {"payload":"testpayload1"})
        self.assertTrue(modified != 0)
        # Fetch it and see if it is correctly filled in
        object,r = get_object(self.token, "things", "testid1")
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload1")
        self.assertTrue(object["sortindex"] == DEFAULT_SORTINDEX)
        self.assertTrue(object["ttl"] == DEFAULT_TTL)
        self.assertTrue(object["id"] == "testid1")
        self.assertTrue(object["modified"] == modified)

    def test_put_object_full(self):
        # Put a new object
        modified,r = put_object(self.token, "things", "testid2", {"payload":"testpayload2", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Fetch it and see if it is correctly filled in
        object,r = get_object(self.token, "things", "testid2")
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload2")
        self.assertTrue(object["sortindex"] == 100)
        self.assertTrue(object["ttl"] == 3600)
        self.assertTrue(object["id"] == "testid2")
        self.assertTrue(object["modified"] == modified)

    def test_put_object_update(self):
        # Put a new object
        modified,r = put_object(self.token, "things", "testid3", {"payload":"testpayload3", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Put it again with updated fields
        modified,r = put_object(self.token, "things", "testid3", {"payload":"testpayload3updated"})
        # Fetch it and see if it is correctly filled in
        object,r = get_object(self.token, "things", "testid3")
        self.assertTrue(modified != 0)
        self.assertTrue(object is not None)
        self.assertTrue(object["payload"] == "testpayload3updated")
        self.assertTrue(object["sortindex"] == 100)
        self.assertTrue(object["ttl"] == 3600)
        self.assertTrue(object["id"] == "testid3")
        self.assertTrue(object["modified"] == modified)

    def test_delete_object_existing(self):
        # Put a new object
        modified,r = put_object(self.token, "things", "testid4", {"payload":"testpayload3", "sortindex":100, "ttl": 3600})
        self.assertTrue(modified != 0)
        # Delete it
        r = delete_object(self.token, "things", "testid4")

    def test_delete_object_unknown_collection(self):
        # Delete it with bad collection
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            r = delete_object(self.token, "thingzzz", "testid4")
        self.assertEqual(context.exception.response.status_code, 404)

    def test_delete_object_unknown_object(self):
        # Delete it with bad collection
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            r = delete_object(self.token, "things", "testid4zzz")
        self.assertEqual(context.exception.response.status_code, 404)

    # Tests from server-syncstorage/syncstorage/tests/functional/test_storage.py

    def test_get_info_collections(self):
        # Create two collections
        modified1,r = put_object(self.token, "col1", random_id(), random_object())
        modified2,r = put_object(self.token, "col2", random_id(), random_object())
        # Only those two should be in /info/collections
        collections,r = get_info_collections(self.token)
        self.assertEqual(len(collections), 2)
        self.assertEqual(collections["col1"], modified1)
        self.assertEqual(collections["col2"], modified2)

    def test_get_info_collection_counts(self):
        # Create two collections
        for i in range(0,3):
            put_object(self.token, "col1", random_id(), random_object())
        for i in range(0,5):
            put_object(self.token, "col2", random_id(), random_object())
        # Only those two should be in /info/collection_counts
        collections,r = get_info_collection_counts(self.token)
        self.assertEqual(len(collections), 2)
        self.assertEqual(collections["col1"], 3)
        self.assertEqual(collections["col2"], 5)

    def test_bad_cache(self):
        put_object(self.token, "col1", random_id(), random_object())
        collections1,r = get_info_collections(self.token)
        put_object(self.token, "col2", random_id(), random_object())
        collections2,r = get_info_collections(self.token)
        self.assertEquals(len(collections2), len(collections1)+1)

    def test_get_collection(self):
        # Create a collection
        for i in range(5):
            put_object(self.token, "col1", str(i), random_object())
        # Non-existent collections appear as empty
        objects,r = get_objects(self.token, "doesnotexist")
        self.assertEquals(objects, [])
        # Get the object ids
        object_ids,r = get_objects(self.token, "col1")
        object_ids.sort()
        self.assertEquals(object_ids, ['0', '1', '2', '3', '4'])
        self.assertEquals(int(r.headers.get("X-Weave-Records", 0)), 5)

    def test_get_collection_ids(self):
        # Test ids
        for i in range(5):
            put_object(self.token, "col1", str(i), random_object())
        object_ids,r = get_objects(self.token, "col1", ids=["1","3","17"])
        object_ids.sort()
        self.assertEquals(object_ids, ["1", "3"])
        self.assertEquals(int(r.headers["X-Weave-Records"]), 2)

    def test_newer(self):
        # Test newer
        ts1,r = put_object(self.token, "test", "id1", random_object())
        ts2,r = put_object(self.token, "test", "id2", random_object())
        self.assertTrue(ts1 != 0)
        self.assertTrue(ts2 != 0)
        self.assertTrue(ts1 < ts2)

        object_ids,r = get_objects(self.token, "test", newer=ts1)
        self.assertEquals(object_ids, ['id2'])

        object_ids,r = get_objects(self.token, "test", newer=ts2)
        self.assertEquals(object_ids, [])

        object_ids,r = get_objects(self.token, "test", newer=(ts1-1))
        self.assertEquals(sorted(object_ids), ['id1', 'id2'])

    def test_full(self):
        put_object(self.token, "test", random_id(), random_object())
        put_object(self.token, "test", random_id(), random_object())

        objects,r = get_objects(self.token, "test", full=True)
        self.assertTrue(isinstance(objects, list))
        self.assertEquals(len(objects), 2)
        self.assertEquals(int(r.headers["X-Weave-Records"]), 2)

        for o in objects:
            for wanted in ('id', 'modified', 'payload'):
                self.assertTrue(wanted in o)

    # def test_get_collection_sort(self):
    #     for i in range(10):
    #         put_object(self.token, "test", str(i), {"payload":"foo", "sortindex":i})
    #     objects,r = get_objects(self.token, "test", full=True)
    #     self.assertEquals(len(objects), 10)
    #     for i in range(10):
    #         self.assertEquals(objects[i]["sortindex"], i)

    def test_get_collection_ids_limit(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        object_ids,r = get_objects(self.token, "test", limit=2)
        self.assertEquals(int(r.headers["X-Weave-Next-Offset"]), 2)
        self.assertEquals(len(object_ids), 2)
        self.assertEquals(object_ids[0], "0")
        self.assertEquals(object_ids[1], "1")

    def test_get_collection_ids_limit_zero_offset(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        object_ids,r = get_objects(self.token, "test", limit=5)
        self.assertTrue(r.headers.get("X-Weave-Next-Offset") is None)
        self.assertEquals(len(object_ids), 5)
        self.assertEquals(object_ids[0], "0")
        self.assertEquals(object_ids[1], "1")
        self.assertEquals(object_ids[2], "2")
        self.assertEquals(object_ids[3], "3")
        self.assertEquals(object_ids[4], "4")

    def test_get_collection_full_limit(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        objects,r = get_objects(self.token, "test", limit=2, full=1)
        self.assertEquals(int(r.headers["X-Weave-Next-Offset"]), 2)
        self.assertEquals(len(objects), 2)
        self.assertEquals(objects[0]["id"], "0")
        self.assertEquals(objects[1]["id"], "1")

    def test_get_collection_full_limit_zero_offset(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        objects,r = get_objects(self.token, "test", limit=5, full=1)
        self.assertTrue(r.headers.get("X-Weave-Next-Offset") is None)
        self.assertEquals(len(objects), 5)
        self.assertEquals(objects[0]["id"], "0")
        self.assertEquals(objects[1]["id"], "1")
        self.assertEquals(objects[2]["id"], "2")
        self.assertEquals(objects[3]["id"], "3")
        self.assertEquals(objects[4]["id"], "4")

    def test_get_collection_offset_ids(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        ids,r = get_objects(self.token, "test", offset=2)
        self.assertTrue(r.headers.get("X-Weave-Next-Offset") is None)
        self.assertEquals(len(ids), 3)
        self.assertEquals(ids[0], "2")
        self.assertEquals(ids[1], "3")
        self.assertEquals(ids[2], "4")

    def test_get_collection_offset_full(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        objects,r = get_objects(self.token, "test", offset=2, full=1)
        self.assertTrue(r.headers.get("X-Weave-Next-Offset") is None)
        self.assertEquals(len(objects), 3)
        self.assertEquals(objects[0]["id"], "2")
        self.assertEquals(objects[1]["id"], "3")
        self.assertEquals(objects[2]["id"], "4")

    def test_get_collection_paging(self):
        for i in range(83):
            put_object(self.token, "test", "%.4d" % i, random_object())
        ids1,r = get_objects(self.token, "test", limit=30, offset=0)
        ids2,r = get_objects(self.token, "test", limit=30, offset=int(r.headers["x-weave-next-offset"]))
        ids3,r = get_objects(self.token, "test", limit=30, offset=int(r.headers["x-weave-next-offset"]))
        self.assertEquals(len(ids1), 30)
        self.assertEquals(len(ids2), 30)
        self.assertEquals(len(ids3), 23)

    def test_get_collection_paging_outofbounds(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        ids,r = get_objects(self.token, "test", offset=7)
        self.assertEquals(len(ids), 0)
        self.assertTrue(r.headers.get("X-Weave-Next-Offset") is None)

    def test_get_collection_accepts(self):
        # Unsupported Accepts should result in a 406
        put_object(self.token, "test", random_id(), random_object())
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            ids,r = get_objects(self.token, "test", accepts="application/cheese")
        self.assertEqual(context.exception.response.status_code, 406)

    # Tests for POST /storage/collection

    def test_post_objects(self):
        # Post two objects
        o1 = random_object_with_id()
        o2 = random_object_with_id()
        j,r = post_objects(self.token, "test", [o1, o2])
        # Check if the response looks ok
        for field in ("failed", "modified", "success"):
            self.assertTrue(field in j)
        # Check if they are in there
        no1,r = get_object(self.token, "test", o1["id"])
        self.assertEquals(no1["payload"], o1["payload"])
        self.assertEquals(no1["modified"], j["modified"])
        no2,r = get_object(self.token, "test", o2["id"])
        self.assertEquals(no2["payload"], o2["payload"])
        self.assertEquals(no2["modified"], j["modified"])
        # Post again with change to the payload
        o1["payload"] = "cheese"
        j,r = post_objects(self.token, "test", [o1, o2])
        # Check if good
        no1,r = get_object(self.token, "test", o1["id"])
        self.assertEquals(no1["payload"], o1["payload"])
        self.assertEquals(no1["modified"], j["modified"])
        no2,r = get_object(self.token, "test", o2["id"])
        self.assertEquals(no2["payload"], o2["payload"])
        self.assertEquals(no2["modified"], j["modified"])

    def test_post_objects_content_type(self):
        # Both tex/plain and application/json should be supported
        for content_type in ("text/plain", "application/json"):
            o = random_object_with_id()
            j,r = post_objects(self.token, "test", [o], content_type=content_type)
            o,r = get_object(self.token, "test", o["id"])
        # Unsupported content type results in a 416
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            j,r = post_objects(self.token, "test", [random_object_with_id()], content_type="application/cheese")
        self.assertEqual(context.exception.response.status_code, 415)

    # def test_post_objects_bad_objects(self):
    #     bad_objects = [
    #         # Bad sortindex
    #         {"payload": "foo", "sortindex": "NOPE"},
    #         {"payload": "foo", "sortindex": None},
    #         # Bad payload
    #         {"payload": None},
    #         {"payload": 1234},
    #     ]
    #     for o in bad_objects:
    #         j,r = post_objects(self.token, "test", [o])
    #         self.assertTrue("bad1" in j["failed"])
    #         with self.assertRaises(requests.exceptions.HTTPError) as context:
    #             o,r = get_object(self.token, "test", "bad1")
    #         self.assertEqual(context.exception.response.status_code, 404)


    # Tests for DELETE /storage/<collection>/<object>

    def test_delete_objects(self):
        # Put some objects in the collection
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        objects,r = get_objects(self.token, "test")
        self.assertEquals(len(objects), 5)
        # Delete some objects
        ts1, r = delete_object(self.token, "test", "1")
        ts2, r = delete_object(self.token, "test", "3")
        # Make sure they are gone
        ids,r = get_objects(self.token, "test")
        self.assertEquals(len(ids), 3)
        self.assertEquals(sorted(ids), ['0', '2', '4'])

    # Tests for DELETE /storage/<collection>

    def test_delete_collection(self):
        # Make sure the collection does not exist
        collections,r = get_info_collections(self.token)
        self.assertTrue("test" not in collections)
        # Create a collection
        put_object(self.token, "test", "1", random_object())
        collections,r = get_info_collections(self.token)
        self.assertTrue("test" in collections)
        # Delete the collection
        j, r = delete_collection(self.token, "test")
        self.assertTrue("modified" in j)
        self.assertTrue("X-Last-Modified" in r.headers)
        self.assertEquals(j["modified"], float(r.headers["X-Last-Modified"]))
        # TODO Can we predict what modified should be?
        # Make sure it is gone
        collections,r = get_info_collections(self.token)
        self.assertTrue("test" not in collections)
        # Make sure we cannot retrieve the object
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            o, r = get_object(self.token, "test", "1")
        self.assertEqual(context.exception.response.status_code, 404)

    def test_delete_collection_that_does_not_exist(self):
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            r = delete_collection(self.token, "doesnotexist")
        self.assertEqual(context.exception.response.status_code, 404)

    # Tests for DELETE /storage/<collection>?ids=

    def test_delete_collection_ids(self):
        # Put some objects in the collection
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        objects,r = get_objects(self.token, "test")
        self.assertEquals(len(objects), 5)
        # Delete some objects
        j, r = delete_collection(self.token, "test", ids=["1","3"])
        self.assertTrue("modified" in j)
        self.assertTrue("X-Last-Modified" in r.headers)
        self.assertEquals(j["modified"], float(r.headers["X-Last-Modified"]))
        # TODO Can we predict what modified should be?
        # Make sure they are gone
        ids,r = get_objects(self.token, "test")
        self.assertEquals(len(ids), 3)
        self.assertEquals(sorted(ids), ['0', '2', '4'])

    def test_delete_collection_ids_that_does_not_exist(self):
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            r = delete_collection(self.token, "doesnotexist", ids=["1","2","3"])
        self.assertEqual(context.exception.response.status_code, 404)

    # Tests for DELETE /storage

    def test_delete_storage(self):
        for i in range(5):
            put_object(self.token, "test", str(i), random_object())
        # Delete it all
        j,r = delete_storage(self.token)
        # Make sure it is gone
        objects,r = get_objects(self.token, "test")
        self.assertEquals(len(objects), 0)
        collections,r = get_info_collections(self.token)
        self.assertTrue("test" not in collections)



if __name__ == "__main__":
    unittest.main()
