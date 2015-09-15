#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""Unit tests - Neo4j DocManager."""
import sys
import logging
import os
import time

sys.path[0:0] = [""]

from gridfs import GridFS
from pymongo import MongoClient
from py2neo import Graph, Node

from tests import unittest, doc_without_id, doc_test, doc_id, doc_array_test, simple_doc, doc_rel, doc_explicit_rel_id
from mongo_connector.command_helper import CommandHelper
from mongo_connector.compat import u
from mongo_connector.connector import Connector
from mongo_connector.doc_managers.neo4j_doc_manager import DocManager
from mongo_connector.util import retry_until_ok


class Neo4jTestCase(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.graph = Graph()
    self.docman = DocManager('http://localhost:7474/db/data', auto_commit_interval=0)

  def setUp(self):
    self.graph.delete_all()
    return

  def tearDown(self):
    self.graph.delete_all()

  def test_update(self):
    """Test the update method."""
    docc = doc_test
    update_spec = {"$set": {'room': 'Auditorium2'}}
    self.docman.update(doc_id, update_spec, 'test.talks', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    node = self.graph.find("talks", "room", "Auditorium2")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_update_new_property(self):
    """Test the update method."""
    docc = doc_without_id
    update_spec = {"$set": {'room': 'Auditorium2', 'level': 'intermediate'}}
    self.docman.update(doc_id, update_spec, 'test.talkss', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'level': 'intermediate', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    node = self.graph.find("talks", "level", "intermediate")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_update_many_properties(self):
    """Test the update method."""
    docc = doc_without_id
    update_spec = {"$set": {'room': 'Auditorium2', 'timeslot': 'Wed 29th, 09:00-10:30'}}
    self.docman.update(doc_id, update_spec, 'test.talkss', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'level': 'intermediate', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:00-10:30'}
    node = self.graph.find("talks", "room", "Auditorium2")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_upsert(self):
    docc = doc_test
    self.docman.upsert(docc, 'test.talks', 1)
    result = self.graph.node_labels
    self.assertIn("talks", result)
    self.assertIn("speaker", result)
    self.assertIn("session", result)
    self.assertIn("Document", result)
    self.assertEqual(self.graph.size, 2)
    self.tearDown

  def test_upsert_with_explicit_id(self):
    docc = doc_array_test
    self.docman.upsert(docc, 'test.talks', 1)
    result = self.graph.node_labels
    self.assertIn("talks", result)
    self.assertIn("tracks0", result)
    self.assertIn("tracks1", result)
    self.assertIn("speaker", result)
    self.assertIn("session", result)
    self.assertIn("Document", result)
    self.assertEqual(self.graph.size, 4)
    self.tearDown

  def test_upsert_with_json_array(self):
    docc = doc_rel
    self.docman.upsert(docc, 'test.places', 1)
    docc = doc_explicit_rel_id
    self.docman.upsert(docc, 'test.people', 1)
    result = self.graph.node_labels
    self.assertIn("places", result)
    self.assertIn("people", result)
    self.assertIn("Document", result)
    self.assertEqual(self.graph.size, 1)
    self.tearDown

  def test_upsert_with_null_reference(self):
    docc = {'_id': "123a456b", 'session': {'title': 'simpel title'}, 'a_null_prop': None }
    self.docman.upsert(docc, 'test.nullprop', 1)
    result = self.graph.node_labels
    self.assertNotIn("a_null_prop", result)
    self.assertEqual(self.graph.size, 1)
    self.tearDown

  def test_upsert_with_multidimensional_list(self):
    docc = {'_id': "123a456b", 'session': {'title': 'simple title'}, 'multi_lists': [[1,2], [3,4]] }
    self.docman.upsert(docc, 'test.multilists', 1)
    result = self.graph.node_labels
    self.assertEqual(self.graph.size, 1)
    self.tearDown

  @unittest.skip("Not implmented yet")
  def test_bulk_upsert(self):
    self.docman.update(doc_id, 'test.talks', 1)
    self.assertEqual(self.graph.size, 0)
    self.tearDown

  def test_remove(self):
    docc = simple_doc
    id = docc['_id']
    self.docman.upsert(docc, 'test.samples', 1)
    self.docman.remove(id, 'test.samples', 1)
    self.assertEqual(self.graph.size, 0)
    self.tearDown

  @unittest.skip("Not implmented yet")
  def test_search(self):
    return

  @unittest.skip("Not implmented yet")
  def test_commands(self):
    return
    

if __name__ == '__main__':
  unittest.main()