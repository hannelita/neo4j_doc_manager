#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""
Class that builds Nodes and Relationships
according to a Mongo document.
"""
import re
import logging
import codecs
from mongo_connector.compat import u

LOG = logging.getLogger(__name__)

class NodesAndRelationshipsBuilder(object):
  def __init__(self, doc, doc_type, doc_id, metadata={}, doc_types=[]):
    self.doc_id = doc_id
    self.query_nodes = {}
    self.relationships_query = {}
    self.metadata = metadata or {}
    self.doc_types = doc_types or []
    self.explicit_ids = {}
    self.build_nodes_query(doc_type, doc, doc_id)
    
  def build_nodes_query(self, doc_type, document, id):
    self.doc_types.append(doc_type)
    parameters = {'_id':id}
    if self.is_dict(self.metadata):
      parameters.update(self.metadata) 
    for key in document.keys():
      if self.is_reference(key):
        self.build_node_with_reference(doc_type, key, id, document[key])
        continue
      if document[key] is None:
        continue
      elif self.is_dict(document[key]):
        self.build_relationships_query(doc_type, key, id, id)
        self.build_nodes_query(key, document[key], id)
      elif self.is_json_array(document[key]):
        for json in self.format_params(document[key]):
          json_key = json_key = key + str(document[key].index(json))
          self.build_relationships_query(doc_type, json_key, id, id)
          self.build_nodes_query(json_key, json, id)
      elif self.is_multimensional_array(document[key]):
        parameters.update(self.flatenned_property(key, document[key]))
      else:
        parameters.update({ key: self.format_params(document[key]) })
    query = "CREATE (c:Document:`%(doc_type)s` {parameters})" % locals()
    self.query_nodes.update({query: {"parameters":parameters}})

  def format_params(self, params):
    if (type(params) is list):
      return list(filter(None, params))
    return params

  def build_node_with_reference(self, root_type, key, doc_id, document_key):
    if document_key is None:
      return
    doc_type = key.split("_id")[0]
    parameters = {'_id':document_key}
    statement = "MERGE (d:Document:`%(doc_type)s` { _id: {parameters}._id})" % locals()
    self.query_nodes.update({statement: {"parameters":parameters}})
    self.build_relationships_query(root_type, doc_type, doc_id, document_key)
    self.explicit_ids.update({document_key: doc_type})

  def is_dict(self, doc_key):
    return (type(doc_key) is dict)

  def is_reference(self, key):
    return (re.search(r"_id$", key))

  def is_multimensional_array(self, doc_key):
    return ((type(doc_key) is list) and (doc_key) and (type(doc_key[0]) is list))

  def flatenned_property(self, key, doc_key):
    parameters = {}
    flattened_list = doc_key
    if ((type(flattened_list[0]) is list) and (flattened_list[0])):
      inner_list = flattened_list[0]
      if (type(inner_list[0]) is list):
        flattened_list = [val for sublist in flattened_list for val in sublist]
        self.flatenned_property(key, flattened_list)
      else: 
        for element in flattened_list:
          element_key = key + str(flattened_list.index(element))
          parameters.update({ element_key: element })
    return parameters

  def is_json_array(self, doc_key):
    return ((type(doc_key) is list) and (doc_key) and (type(doc_key[0]) is dict))


  def build_relationships_query(self, main_type, node_type, doc_id, explicit_id):
    relationship_type = (main_type + "_" + node_type).encode("utf-8")
    statement = "MATCH (a:`%(main_type)s`), (b:`%(node_type)s`) WHERE a._id={doc_id} AND b._id ={explicit_id} CREATE (a)-[r:`%(relationship_type)s`]->(b)" % locals()
    params = {"doc_id": doc_id, "explicit_id": explicit_id}
    self.relationships_query.update({statement: params})
