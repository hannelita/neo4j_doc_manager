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

from tests import unittest, doc_test_double_nested, double_nested_doc, doc_without_id, doc_test, doc_id, doc_array_test, simple_doc, doc_rel, doc_explicit_rel_id
from mongo_connector.command_helper import CommandHelper
from mongo_connector.compat import u
from mongo_connector.connector import Connector
from mongo_connector.doc_managers.neo4j_doc_manager import DocManager
from mongo_connector.util import retry_until_ok


class Neo4jTestCase(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    self.docman = DocManager('http://localhost:7474/db/data', auto_commit_interval=0)
    self.graph = self.docman.graph

  def setUp(self):
    self.graph.delete_all()
    return

  def tearDown(self):
    self.docman.graph.delete_all()
    self.graph.delete_all()
    self.docman = DocManager('http://localhost:7474/db/data', auto_commit_interval=0)
    self.graph = self.docman.graph

  def test_update(self):
    """Test the update method. Simple cause, single parameter to update with set"""
    docc = doc_test
    update_spec = {"$set": {'room': 'Auditorium2'}}
    self.docman.update(doc_id, update_spec, 'test.talks', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    node = self.graph.find("talks", "room", "Auditorium2")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_update_new_property(self):
    """Test the update method. Set creating a new property"""
    docc = doc_without_id
    update_spec = {"$set": {'room': 'Auditorium2', 'level': 'intermediate'}}
    self.docman.update(doc_id, update_spec, 'test.talkss', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'level': 'intermediate', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:30-10:30'}
    node = self.graph.find("talks", "level", "intermediate")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_update_empty(self):
    """Test the update method. No set or unset; all older properties must be erased"""
    docc = doc_without_id
    update_spec = {'level': 'intermediate'}
    self.docman.update(doc_id, update_spec, 'test.talkss', 1)
    node = self.graph.find_one("talkss", "room", "Auditorium")
    self.assertEqual(node, None)
    self.tearDown()

  def test_update_unset_property(self):
    """Test the update method. Simple case test for unset"""
    docc = doc_without_id
    update_spec = {"$unset": {'timeslot': True}}
    self.docman.update(doc_id, update_spec, 'test.talksunset', 1)
    node = self.graph.find_one("talksunset", "timeslot")
    self.assertIs(node, None)
    self.tearDown()
  
  def test_update_unset_removing_node(self):
    """Test the update method. Unset clause removing nested node and relationship"""
    docc = doc_without_id
    update_spec = {u'$unset': {u'session': True}}
    self.docman.update(doc_id, update_spec, 'test.talksunsetcomposite', 1)
    node = self.graph.find_one("talksunsetcomposite")
    self.assertIs(node, None)
    self.tearDown()

  def test_update_many_properties(self):
    """Test the update method. Many properties being sent at once"""
    docc = doc_without_id
    update_spec = {"$set": {'room': 'Auditorium2', 'timeslot': 'Wed 29th, 09:00-10:30'}}
    self.docman.update(doc_id, update_spec, 'test.talkss', 1)
    expected_doc = {'_id': doc_id, 'session': {'title': '12 Years of Spring: An Open Source Journey', 'abstract': 'Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015. This keynote reflects upon the journey so far, with a focus on the open source ecosystem that Spring lives within, including stories and anecdotes from the old days as well as from recent times. Not getting stuck in history, we’ll also look at the continuity of Spring’s philosophy and its immediate applicability to Java development challenges in 2015 and beyond.'}, 'room': 'Auditorium2', 'level': 'intermediate', 'topics': ['keynote', 'spring'], 'speaker': {'twitter': 'https://twitter.com/springjuergen', 'name': 'Juergen Hoeller', 'picture': 'http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg', 'bio': 'Juergen Hoeller is co-founder of the Spring Framework open source project and has been serving as the project lead and release manager for the core framework since 2003. Juergen is an experienced software architect and consultant with outstanding expertise in code organization, transaction management and enterprise messaging.'}, 'timeslot': 'Wed 29th, 09:00-10:30'}
    node = self.graph.find("talks", "room", "Auditorium2")
    self.assertIsNot(node, None)
    self.tearDown()

  def test_update_nested_properties(self):
    """Test the update method for nested properties. A new node and a new relationship must be created."""
    docc = double_nested_doc
    update_spec = {"$set": {'details': {'model': '14Q3', 'make': 'xyz'}, 'level': 'intermediate'}}
    self.docman.update(doc_id, update_spec, 'test.talksnesteds', 1)
    node = self.graph.find("details", "model", "14Q3")
    self.assertIsNot(node, None)
    labels = self.graph.node_labels
    self.assertIn("details", labels)
    self.tearDown()

  def test_update_inner_nested_properties(self):
    """Test the update method for nested properties. A new node and a new relationship must be created. Also tests inner node chain"""
    docc = double_nested_doc
    update_spec = {u'$set': {u'test': {u'city': u'London', u'outer': {u'level': u'two'}, u'level': u'One'}}}
    self.docman.update(doc_id, update_spec, 'test.talksinnernesteds', 1)
    node = self.graph.find("test", "city", "London")
    self.assertIsNot(node, None)
    labels = self.graph.node_labels
    self.assertIn("test", labels)
    self.assertIn("outer", labels)
    self.tearDown()

  def test_update_relationship_simple_removal(self):
    """Test the update method without set or unset (doc will be replaced). Simple nested doc is being passed"""
    docc = double_nested_doc
    update_spec = {u'conference': {u'city': u'London', u'name': u'GraphConnect'}}
    self.docman.update(doc_id, update_spec, 'test.talksupdate', 1)
    node = self.graph.find("conference", "city", "London")
    self.assertIsNot(node, None)
    labels = self.graph.node_labels
    self.assertIn("conference", labels)
    self.tearDown()

  def test_update_relationship_composite_removal(self):
    """Test the update method without set or unset (doc will be replaced). Nested doc is being passed plus an extra arg to the root node"""
    docc = double_nested_doc
    update_spec = {u'conference': {u'city': u'London', u'name': u'GraphConnect'}, u'level': u'intermediate'}
    self.docman.update(doc_id, update_spec, 'test.talksupdatecomposite', 1)
    node = self.graph.find("conference", "city", "London")
    self.assertIsNot(node, None)
    talks = self.graph.find("talksupdatecomposite", "level", "intermediate")
    self.assertIsNot(talks, None)
    labels = self.graph.node_labels
    self.assertIn("conference", labels)
    self.tearDown()

  def test_upsert(self):
    docc = doc_test
    self.docman.upsert(docc, 'test.talksone', 1)
    result = self.graph.node_labels
    self.assertIn("talksone", result)
    self.assertIn("speaker", result)
    self.assertIn("session", result)
    self.assertIn("Document", result)
    self.assertEqual(self.graph.size, 2)
    root = self.graph.find_one("talksone")['timeslot']
    self.assertEqual("Wed 29th, 09:30-10:30", root)
    inner = self.graph.find_one("speaker")['name']
    self.assertEqual("Juergen Hoeller", inner)
    inner = self.graph.find_one("session")['title']
    self.assertEqual("12 Years of Spring: An Open Source Journey", inner)
    self.tearDown()

  def test_upsert_double_nested(self):
    docc = double_nested_doc
    self.docman.upsert(docc, 'test.doublenestedtalks', 1)
    result = self.graph.node_labels
    self.assertIn("session", result)
    self.assertIn("inner", result)
    self.assertIn("Document", result)
    inner = self.graph.find_one("inner")['propr']
    self.assertEqual("abc", inner)
    outer = self.graph.find_one("doublenestedtalks")['propr']
    self.assertEqual(None, outer)
    self.assertEqual(self.graph.size, 2)
    self.tearDown()

  def test_upsert_inner_nested(self):
    docc = doc_test_double_nested
    self.docman.upsert(docc, 'test.innernestedtalks', 1)
    result = self.graph.node_labels
    self.assertIn("session", result)
    self.assertIn("conference", result)
    self.assertIn("Document", result)
    node = self.graph.find("conference", "city", "London")
    self.assertIsNot(node, None)
    self.assertEqual(self.graph.size, 3)
    self.tearDown()

  def test_upsert_with_json_array(self):
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
    self.tearDown()

  def test_upsert_with_explicit_id(self):
    docc = doc_rel
    self.docman.upsert(docc, 'test.places', 1)
    docc2 = doc_explicit_rel_id
    self.docman.upsert(docc2, 'test.people', 1)
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