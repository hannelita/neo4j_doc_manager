"""
Neo4j implementation for the DocManager. Receives documents and 
communicates with Neo4j Server.
"""
import base64
import logging
import os
import sys
# sys.path.append(os.path.join(os.path.dirname(file), '..', 'mongo_connector'))
import mongo_connector.doc_managers as doc_manager
import os.path as path, sys

# sys.stdout.write(path.join(path.dirname(doc_manager.__file__),'neo4j_doc_manager.py'))

from threading import Timer

import bson.json_util

from py2neo import Graph

from mongo_connector import errors
from mongo_connector.compat import u
from mongo_connector.constants import (DEFAULT_COMMIT_INTERVAL,
                                       DEFAULT_MAX_BULK)
from mongo_connector.util import exception_wrapper, retry_until_ok
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DefaultDocumentFormatter

# wrap_exceptions = exception_wrapper({
#     es_exceptions.ConnectionError: errors.ConnectionFailed,
#     es_exceptions.TransportError: errors.OperationFailed,
#     es_exceptions.NotFoundError: errors.OperationFailed,
#     es_exceptions.RequestError: errors.OperationFailed})

LOG = logging.getLogger(__name__)

class DocManager(DocManagerBase):
  """
  Neo4j implementation for the DocManager. Receives documents and 
  communicates with Neo4j Server.
  """

  def __init__(self, url, auto_commit_interval=DEFAULT_COMMIT_INTERVAL,
                 unique_key='_id', chunk_size=DEFAULT_MAX_BULK, **kwargs):
    LOG.debug('Init AAAA')
    self.remote_graph = Graph(url,
    **kwargs.get('clientOptions', {}))
  
  def stop(self):
    """Stop the auto-commit thread."""
    self.auto_commit_interval = None
  
  def upsert(self, doc, namespace, timestamp):
    """Inserts a document into Neo4j."""
    index, doc_type = self._index_and_mapping(namespace)
  
  def bulk_upsert(self, docs, namespace, timestamp):
    """Insert multiple documents into Neo4j."""

  def update(self, document_id, update_spec, namespace, timestamp):
    return

  def remove(self, document_id, namespace, timestamp):
    return

  def search(self, start_ts, end_ts):
    return

  def commit(self):
    return

  def get_last_doc(self):
    return

  def handle_command(self, doc, namespace, timestamp):
    return


  def _index_and_mapping(self, namespace):
      """Helper method for getting the index and type from a namespace."""
      index, doc_type = namespace.split('.', 1)
      return index.lower(), doc_type
