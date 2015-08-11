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
    tx = self.graph.cypher.begin()
    parameters = {'id':doc_id}
    for key in doc.keys():
      if (type(doc[key]) is str):
        value = doc[key]
      else:
        value = ""
      parameters.update({ key: value })
    query = "CREATE (c:Document:{doc_type} {{parameters}})".format(doc_type=doc_type)
    tx.append(query, {"parameters":parameters})
    tx.commit()

  def bulk_upsert(self, docs, namespace, timestamp):
    """Insert multiple documents into Neo4j."""
    LOG.error("Bulk")

  def update(self, document_id, update_spec, namespace, timestamp):
    LOG.error("Update")

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
