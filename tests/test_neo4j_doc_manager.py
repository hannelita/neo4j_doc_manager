"""Unit tests - Neo4j DocManager."""
import base64
import sys
import time

sys.path[0:0] = [""]

from mongo_connector.command_helper import CommandHelper
from mongo_connector.doc_managers.elastic_doc_manager import DocManager


class TestNeo4jDocManager(Neo4jTestCase):
  def test_update(self):
    """Test the update method."""
    doc_id = 1
    doc = {"_id": doc_id, "speaker": 1, "sessions": 2}
    self.assertEqual(doc, {"_id": '1', "sessions": 3})

  def test_upsert(self):
    docc = {'_id': '1', 'name': 'John'}
    

  def test_bulk_upsert(self):
    doc_id = 1
    doc = {"_id": doc_id, "speaker": 1, "sessions": 2}
    self.assertEqual(doc, {"_id": '1', "sessions": 3})

  def test_remove(self):
    doc_id = 1
    doc = {"_id": doc_id, "speaker": 1, "sessions": 2}
    self.assertEqual(doc, {"_id": '1', "sessions": 3})

  def test_search(self):
    doc_id = 1
    doc = {"_id": doc_id, "speaker": 1, "sessions": 2}
    self.assertEqual(doc, {"_id": '1', "sessions": 3})

  def test_commands(self):
    doc_id = 1
    doc = {"_id": doc_id, "speaker": 1, "sessions": 2}
    self.assertEqual(doc, {"_id": '1', "sessions": 3})
    

if __name__ == '__main__':
    unittest.main()