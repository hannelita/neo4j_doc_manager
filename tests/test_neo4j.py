#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""Integration tests - Neo4j and mongo-connector"""
import base64
import os
import sys
import time

from py2neo import Graph, authenticate
from pymongo import MongoClient
from gridfs import GridFS
from tests import neo4j_pair

sys.path[0:0] = [""]

from tests.setup_cluster import ReplicaSet
from mongo_connector.doc_managers.neo4j_doc_manager import DocManager
from mongo_connector.connector import Connector
from mongo_connector.util import retry_until_ok
from tests.util import assert_soon
from tests import unittest


class Neo4jTestCase(unittest.TestCase):
  """Integration tests for Neo4j TestCases."""

  @classmethod
  def setUpClass(cls):
    cls.neo4j_conn = Graph('http://localhost:7474/db/data')
    cls.docman = DocManager('http://localhost:7474/db/data', auto_commit_interval=0)

  def _count(cls):
    return cls.neo4j_conn.order

  def query(cls):
    return cls.neo4j_conn.find_one("test", "name", "paulie")


class TestNeo4j(Neo4jTestCase):
    """Integration tests for mongo-connector + Neo4j."""

    @classmethod
    def setUpClass(cls):
      """Start the cluster."""
      Neo4jTestCase.setUpClass()
      cls.repl_set = ReplicaSet().start()
      cls.conn = cls.repl_set.client()

    @classmethod
    def tearDownClass(cls):
      """Kill the cluster."""
      cls.repl_set.stop()

    def tearDown(self):
      """Stop the Connector thread."""
      super(TestNeo4j, self).tearDown()
      self.connector.join()
      time.sleep(10)

    def setUp(self):
      """Start a new Connector for each test."""
      try:
          os.unlink("oplog.timestamp")
      except OSError:
          pass
      open("oplog.timestamp", "w").close()
      docman = DocManager('http://localhost:7474/db/data',auto_commit_interval=0)
      self.connector = Connector(
          mongo_address=self.repl_set.uri,
          ns_set=['test.test'],
          doc_managers=(docman,),
          gridfs_set=['test.test']
      )

      self.conn.test.test.drop()
      self.conn.test.test.files.drop()
      self.conn.test.test.chunks.drop()
      self.connector.start()
      self.neo4j_conn.delete_all()
      assert_soon(lambda: len(self.connector.shard_set) > 0)
      assert_soon(lambda: self._count() == 0)
      time.sleep(5)

    def test_insert(self):
      """Test insert operations."""
      self.conn['test']['test'].insert({'name': 'paulie'})
      result_set_2 = self.conn['test']['test'].find_one()
      self.connector.doc_managers[0].upsert({'_id': str(result_set_2['_id']),'name': 'paulie'}, "test.test", 1)
      assert_soon(lambda: self._count() > 0)
      result_set_1 = self.neo4j_conn.find_one("test")
      self.assertNotEqual(result_set_1, None)
      self.assertEqual(result_set_1['_id'], str(result_set_2['_id']))
      self.assertEqual(result_set_1['name'], result_set_2['name'])
      self.connector.doc_managers[0].graph.delete_all()

    def test_remove(self):
      """Tests remove operations."""
      self.conn['test']['test'].insert({'name': 'paulie'})
      result_set = self.conn['test']['test'].find_one()
      # self.connector.doc_managers[0].upsert({'_id': str(result_set['_id']),'name': 'paulie'}, "test.test", 1)
      assert_soon(lambda: self._count() == 1)
      self.conn['test']['test'].remove({'name': 'paulie'})
      assert_soon(lambda: self._count() != 1)
      self.connector.doc_managers[0].remove(str(result_set['_id']), 'test.test', 1)
      self.assertEqual(self._count(), 0)
      self.connector.doc_managers[0].graph.delete_all()

    def test_update(self):
      """Test update operations."""
      # Insert
      self.connector.doc_managers[0].graph.delete_all()
      self.conn['test']['updt'].insert({"a": 0})
      result_set = self.conn['test']['updt'].find_one()
      self.connector.doc_managers[0].upsert({'_id': str(result_set['_id']),'a': '0'}, "test.updt", 1)
      assert_soon(lambda: self._count() == 1)

      def check_update(update_spec):
        updated = self.conn.test.updt.find_and_modify(
            {"a": 0},
            update_spec,
            new=True
        )
        # Stringify _id to match what will be retrieved from ES
        updated['_id'] = str(updated['_id'])
        # Allow some time for update to propagate
        time.sleep(5)
        replicated = self.neo4j_conn.find_one("updt")['_id']
        self.assertEqual(replicated, updated['_id'])

      # Update by adding a field. Note that ES can't mix types within an array
      check_update({"$set": {"b": [{"c": 10}, {"d": 11}]}})

      # Update by setting an attribute of a sub-document beyond end of array.
      check_update({"$set": {"b.10.c": 42}})

      # Update by changing a value within a sub-document (contains array)
      check_update({"$inc": {"b.0.c": 1}})

      # Update by changing the value within an array
      check_update({"$inc": {"b.1.f": 12}})

      # Update by adding new bucket to list
      check_update({"$push": {"b": {"e": 12}}})

      # Update by changing an entire sub-document
      check_update({"$set": {"b.0": {"e": 4}}})

      # Update by adding a sub-document
      check_update({"$set": {"b": {"0": {"c": 100}}}})

      # Update whole document
      check_update({"a": 0, "b": {"1": {"d": 10000}}})

      self.connector.doc_managers[0].graph.delete_all()

    
    def test_bad_int_value(self):
      self.conn['test']['test'].insert({'inf': float('inf'), 'nan': float('nan'),
          'still_exists': True})
      result_set = self.conn['test']['test'].find_one()
      self.connector.doc_managers[0].upsert({'_id': str(result_set['_id']), 'inf': float('inf'), 'nan': float('nan'),
          'still_exists': True }, "test.test", 1)
      assert_soon(lambda: self._count() > 0)
      doc = self.neo4j_conn.find_one("test")
      self.assertNotIn('inf', doc)
      self.assertNotIn('nan', doc)
      self.assertTrue(doc['still_exists'])
      
    # def test_rollback(self):
    #   """Test behavior during a MongoDB rollback.
    #   We force a rollback by adding a doc, killing the primary,
    #   adding another doc, killing the new primary, and then
    #   restarting both.
    #   """
    #   primary_conn = self.repl_set.primary.client()

    #   self.conn['test']['test'].insert({'name': 'paul'})
    #   result_set = self.conn['test']['test'].find_one()
    #   condition1 = lambda: self.conn['test']['test'].find(
    #       {'name': 'paul'}).count() == 1
    #   condition2 = lambda: self._count() == 1
    #   assert_soon(condition1)
    #   assert_soon(condition2)

    #   self.repl_set.primary.stop(destroy=False)

    #   new_primary_conn = self.repl_set.secondary.client()

    #   admin = new_primary_conn['admin']
    #   assert_soon(lambda: admin.command("isMaster")['ismaster'])
    #   time.sleep(5)
    #   retry_until_ok(self.conn.test.test.insert, {'name': 'pauline'})
    #   assert_soon(lambda: self._count() == 2)
    #   result_set_1 = self.neo4j_conn.find_one("test")
    #   result_set_2 = self.conn['test']['test'].find_one({'name': 'pauline'})
      # self.assertEqual(len(result_set_1), 2)
      #make sure pauline is there
      # for item in result_set_1:
      #     if item['name'] == 'pauline':
      #         self.assertEqual(item['_id'], str(result_set_2['_id']))
      # self.repl_set.secondary.stop(destroy=False)

      # self.repl_set.primary.start()
      # while primary_conn['admin'].command("isMaster")['ismaster'] is False:
      #     time.sleep(1)

      # self.repl_set.secondary.start()

      # time.sleep(2)
      # result_set_1 = list(self._search())
      # self.assertEqual(len(result_set_1), 1)

      # for item in result_set_1:
      #     self.assertEqual(item['name'], 'paul')
      # find_cursor = retry_until_ok(self.conn['test']['test'].find)
      # self.assertEqual(retry_until_ok(find_cursor.count), 1)


if __name__ == '__main__':
    unittest.main()