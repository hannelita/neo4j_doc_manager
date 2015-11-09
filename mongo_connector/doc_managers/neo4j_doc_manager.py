#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""
Neo4j implementation for the DocManager. Receives documents and 
communicates with Neo4j Server.
"""
import base64
import logging
import os
import os.path as path, sys

import bson.json_util

from mongo_connector.doc_managers.nodes_and_relationships_builder import NodesAndRelationshipsBuilder
from mongo_connector.doc_managers.nodes_and_relationships_updater import NodesAndRelationshipsUpdater
from mongo_connector.doc_managers.error_handler import ErrorHandler

from py2neo import Graph, authenticate


from mongo_connector import errors
from mongo_connector.compat import u
from mongo_connector.constants import (DEFAULT_COMMIT_INTERVAL,
                                       DEFAULT_MAX_BULK)
from mongo_connector.util import exception_wrapper, retry_until_ok
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DefaultDocumentFormatter

errors_handler = ErrorHandler()
wrap_exceptions = exception_wrapper(errors_handler.error_hash)

LOG = logging.getLogger(__name__)

class DocManager(DocManagerBase):
  """
  Neo4j implementation for the DocManager. Receives documents and 
  communicates with Neo4j Server.
  """

  def __init__(self, url, auto_commit_interval=DEFAULT_COMMIT_INTERVAL,
                 unique_key='_id', chunk_size=DEFAULT_MAX_BULK, **kwargs):
    
    self.graph = Graph(url)
    self.auto_commit_interval = auto_commit_interval
    self.unique_key = unique_key
    self.chunk_size = chunk_size
    self._formatter = DefaultDocumentFormatter()
    self.kwargs = kwargs.get("clientOptions")

  def apply_id_constraint(self, doc_types):
    for doc_type in doc_types:
      constraint = "CREATE CONSTRAINT ON (d:`%(doc_type)s`) ASSERT d._id IS UNIQUE" % locals()
      self.graph.cypher.execute(constraint)

  def stop(self):
    """Stop the auto-commit thread."""
    self.auto_commit_interval = None
  
  @wrap_exceptions
  def upsert(self, doc, namespace, timestamp):
    """Inserts a document into Neo4j."""
    index, doc_type = self._index_and_mapping(namespace)
    doc_id = u(doc.pop("_id"))
    metadata = { "_ts": timestamp }
    doc = self._formatter.format_document(doc)
    builder = NodesAndRelationshipsBuilder(doc, doc_type, doc_id, metadata)
    self.apply_id_constraint(builder.doc_types)
    tx = self.graph.cypher.begin()
    for statement in builder.query_nodes.keys():
      tx.append(statement, builder.query_nodes[statement])
    for relationship in builder.relationships_query.keys():
      tx.append(relationship, builder.relationships_query[relationship])
    tx.commit()

  @wrap_exceptions
  def bulk_upsert(self, docs, namespace, timestamp):
    """Insert multiple documents into Neo4j."""
    """Maximum chunk size is 1000. Transaction blocks won't have more than 1000 statements."""
    metadata = { "_ts": timestamp }
    tx = self.graph.cypher.begin()
    for doc in docs:
      index, doc_type = self._index_and_mapping(namespace)
      doc_id = u(doc.pop("_id"))
      doc = self._formatter.format_document(doc)
      builder = NodesAndRelationshipsBuilder(doc, doc_type, doc_id, metadata)
      self.apply_id_constraint(builder.doc_types)
      for statement in builder.query_nodes.keys():
        tx.append(statement, builder.query_nodes[statement])
      for relationship in builder.relationships_query.keys():
        tx.append(relationship, builder.relationships_query[relationship])
    tx.commit()

  @wrap_exceptions
  def update(self, document_id, update_spec, namespace, timestamp):
    doc_id = u(document_id)
    tx = self.graph.cypher.begin()
    index, doc_type = self._index_and_mapping(namespace)
    updater = NodesAndRelationshipsUpdater()
    updater.run_update(update_spec, doc_id, doc_type)
    for statement in updater.statements_with_params:
      for key in statement.keys():
        tx.append(key, statement[key])
    tx.commit()

  @wrap_exceptions
  def remove(self, document_id, namespace, timestamp):
    """Removes a document from Neo4j."""
    doc_id = u(document_id)
    index, doc_type = self._index_and_mapping(namespace)
    params_dict = {"doc_id": doc_id}
    tx = self.graph.cypher.begin()
    statement = "MATCH (d:Document) WHERE d._id={doc_id} OPTIONAL MATCH (d)-[r]-() DELETE d, r"
    tx.append(statement, params_dict)
    tx.commit()

  @wrap_exceptions
  def search(self, start_ts, end_ts):
    statement = "MATCH (d:Document) WHERE d._ts>=%(start_ts)s AND d._ts<=%(end_ts)s RETURN d" % locals()
    results = self.graph.cypher.execute(statement)
    return results


  def commit(self):
    LOG.error("Commit")
    

  @wrap_exceptions
  def get_last_doc(self):
    """Get the most recently modified node from Neo4j.
    This method is used to help define a time window within which documents
    may be in conflict after a MongoDB rollback.
    """
    LOG.error("Commit")    

    
  def handle_command(self, doc, namespace, timestamp):
    db = namespace.split('.', 1)[0]

  def _index_and_mapping(self, namespace):
    """Helper method for getting the index and type from a namespace."""
    index, doc_type = namespace.split('.', 1)
    return index.lower(), doc_type
