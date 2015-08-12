"""
Neo4j implementation for the DocManager. Receives documents and 
communicates with Neo4j Server.
"""
import base64
import logging

import os.path as path, sys

import bson.json_util

from py2neo import Graph, authenticate

from mongo_connector import errors
from mongo_connector.compat import u
from mongo_connector.constants import (DEFAULT_COMMIT_INTERVAL,
                                       DEFAULT_MAX_BULK)
from mongo_connector.util import exception_wrapper, retry_until_ok
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DefaultDocumentFormatter


LOG = logging.getLogger(__name__)

class DocManager(DocManagerBase):
  """
  Neo4j implementation for the DocManager. Receives documents and 
  communicates with Neo4j Server.
  """

  def __init__(self, url, auto_commit_interval=DEFAULT_COMMIT_INTERVAL,
                 unique_key='_id', chunk_size=DEFAULT_MAX_BULK, **kwargs):
    self.remote_graph = Graph(url, **kwargs.get('clientOptions', {}))
    self.graph = Graph()
    self.auto_commit_interval = auto_commit_interval
    self.unique_key = unique_key
    self.chunk_size = chunk_size
    if self.auto_commit_interval not in [None, 0]:
      self.run_auto_commit()
    self._formatter = DefaultDocumentFormatter()
    self.query_nodes = {}
    self.doc_types = []

  def apply_id_constraint(self, doc_type):
    constraint = "CREATE CONSTRAINT ON (d:{doc_type}) ASSERT d.id IS UNIQUE".format(doc_type=doc_type)
    self.graph.cypher.execute(constraint)

  def stop(self):
    """Stop the auto-commit thread."""
    self.auto_commit_interval = None
  
  def upsert(self, doc, namespace, timestamp):
    """Inserts a document into Neo4j."""
    index, doc_type = self._index_and_mapping(namespace)
    # No need to duplicate '_id' in source document
    doc_id = u(doc.pop("_id"))
    metadata = {
        "ns": namespace,
        "_ts": timestamp
    }
    doc = self._formatter.format_document(doc)
    self.store_nodes_and_relationships(doc, doc_type, doc_id)
    
  
  def store_nodes_and_relationships(self, doc, doc_type, doc_id):
    self.build_nodes(doc_type, doc, doc_id)
    for node_type in self.doc_types:
      self.apply_id_constraint(node_type)
    tx = self.graph.cypher.begin()
    for query in self.query_nodes.keys():
      tx.append(query, {"parameters":self.query_nodes[query]})
    main_type = self.doc_types.pop(0)
    for node_type in self.doc_types:
      tx.append(self.build_relationships(doc_id, main_type, node_type))
    tx.commit()

  def build_nodes(self, doc_type, hash, id):
    self.doc_types.append(doc_type)
    parameters = {'id':id}
    for key in hash.keys():
      if (type(hash[key]) is str) or (type(hash[key]) is list):
        value = hash[key]
        parameters.update({ key: value })
      else:
        self.build_nodes(key, hash[key], id)
    query = "CREATE (c:Document:{doc_type} {{parameters}})".format(doc_type=doc_type)
    self.query_nodes.update({query: parameters})

  def build_relationships(self, doc_id, main_type, node_type):
    relationship_type = main_type + "_" + node_type
    statement = "MATCH (a:{main_type}), (b:{node_type}) WHERE a.id = '{doc_id}' AND b.id = '{doc_id}' CREATE (a)-[r:{relationship_type}]->(b)".format(main_type=main_type, node_type=node_type, doc_id=doc_id, relationship_type=relationship_type)
    return statement

  def bulk_upsert(self, docs, namespace, timestamp):
    """Insert multiple documents into Neo4j."""
    LOG.error("Bulk")

  def update(self, document_id, update_spec, namespace, timestamp):
    self.commit()
    doc_id = u(document_id)
    update_value_list = update_spec['$set']
    index, doc_type = self._index_and_mapping(namespace)
    tx = self.graph.cypher.begin()
    for update_value in update_value_list.keys():
      statement = "MATCH (d:Document:{doc_type}) WHERE d.id = '{doc_id}' SET d.{update_value} = '{value}'".format(doc_type=doc_type, doc_id=doc_id, update_value=update_value, value=update_value_list[update_value])
      tx.append(statement)
    tx.commit()

  def remove(self, document_id, namespace, timestamp):
    LOG.error("remove")

  def search(self, start_ts, end_ts):
    LOG.error("Search")

  def commit(self):
    LOG.error("Commit")
    

  def get_last_doc(self):
    LOG.error("get last doc")
    

  def handle_command(self, doc, namespace, timestamp):
    db = namespace.split('.', 1)[0]


  def _index_and_mapping(self, namespace):
    """Helper method for getting the index and type from a namespace."""
    index, doc_type = namespace.split('.', 1)
    return index.lower(), doc_type
