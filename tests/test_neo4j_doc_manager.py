"""Unit tests - Neo4j DocManager."""
import sys
import logging
import os
import time

sys.path[0:0] = [""]

from gridfs import GridFS
from pymongo import MongoClient
from py2neo import Graph

from tests import unittest
from mongo_connector.command_helper import CommandHelper
from mongo_connector.compat import u
from mongo_connector.connector import Connector
from mongo_connector.doc_managers.neo4j_doc_manager import DocManager
from mongo_connector.util import retry_until_ok


class Neo4jTestCase(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.graph = Graph()
    self.docman = DocManager('http://localhost:7474/db/suite', auto_commit_interval=0)

  def setUp(self):
    self.graph.delete_all()
    return

  def tearDown(self):
    self.graph.delete_all()

  def test_update(self):
    """Test the update method."""
    self.graph.delete_all()
    doc_id = 1
    docc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    update_spec = {"$set": {'room': 'Auditorium2'}}
    self.docman.update(doc_id, update_spec, 'test.talks', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    node = self.graph.find("talks", "room", "Auditorium2")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_upsert(self):
    docc = {'_id': '1', 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    self.docman.upsert(docc, 'test.talks', 1)
    result = self.graph.node_labels
    self.assertIn("talks", result)
    self.assertIn("speaker", result)
    self.assertIn("session", result)
    self.assertIn("Document", result)
    self.assertEqual(self.graph.size, 2)
    self.tearDown

  @unittest.skip("Not implmented yet")
  def test_bulk_upsert(self):
    return

  @unittest.skip("Not implmented yet")
  def test_remove(self):
    return

  @unittest.skip("Not implmented yet")
  def test_search(self):
    return

  @unittest.skip("Not implmented yet")
  def test_commands(self):
    return
    

if __name__ == '__main__':
  unittest.main()