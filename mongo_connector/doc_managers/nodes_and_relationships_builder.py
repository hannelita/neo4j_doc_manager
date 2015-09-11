"""
Class that builds Nodes and Relationships
according to a Mongo document.
"""
import re
import logging

LOG = logging.getLogger(__name__)

class NodesAndRelationshipsBuilder(object):
  def __init__(self, doc, doc_type, doc_id):
    self.query_nodes = {}
    self.doc_types = []
    self.explicit_ids = {}
    self.build_nodes_query(doc_type, doc, doc_id)
    self.parameters = {}
    
  def build_nodes_query(self, doc_type, document, id):
    self.doc_types.append(doc_type)
    self.parameters = {'_id':id}
    for key in document.keys():
      if self.is_reference(key):
        self.build_node_with_reference(key, document[key])
        continue
      if document[key] is None:
        continue
      elif self.is_dict(document[key]):
        self.build_nodes_query(key, document[key], id)
      elif self.is_json_array(document[key]):
        for json in document[key]:
          json_key = key + str(document[key].index(json))
          self.build_nodes_query(json_key, json, id)
      elif self.is_multimensional_array(document[key]):
        self.flatenned_property(key, document[key])
      else:
        self.parameters.update({ key: document[key] })
    query = "CREATE (c:Document:{doc_type} {{parameters}})".format(doc_type=doc_type)
    self.query_nodes.update({query: self.parameters})

  def build_node_with_reference(self, key, document_key):
    if document_key is None:
      return
    doc_type = key.split("_id")[0]
    parameters = {'_id':document_key}
    statement = "MERGE (d:Document:{doc_type} {{ _id: {{parameters}}._id}})".format(doc_type=doc_type)
    self.query_nodes.update({statement: parameters})
    self.explicit_ids.update({document_key: doc_type})

  def is_dict(self, doc_key):
    return (type(doc_key) is dict)

  def is_reference(self, key):
    return (re.search(r"_id$", key))

  def is_multimensional_array(self, doc_key):
    return ((type(doc_key) is list) and (doc_key) and (type(doc_key[0]) is list))

  def flatenned_property(self, key, doc_key):
    flattened_list = doc_key
    if ((type(flattened_list[0]) is list) and (flattened_list[0])):
      inner_list = flattened_list[0]
      if (type(inner_list[0]) is list):
        flattened_list = [val for sublist in flattened_list for val in sublist]
        self.flatenned_property(key, flattened_list)
      else: 
        for element in flattened_list:
          element_key = key + str(flattened_list.index(element))
          self.parameters.update({ element_key: element })

  def is_json_array(self, doc_key):
    return ((type(doc_key) is list) and (doc_key) and (type(doc_key[0]) is dict))

  def build_relationships_query(self, main_type, node_type):
    relationship_type = main_type + "_" + node_type
    statement = "MATCH (a:{main_type}), (b:{node_type}) WHERE a._id={{doc_id}} AND b._id ={{explicit_id}} CREATE (a)-[r:{relationship_type}]->(b)".format(main_type=main_type, node_type=node_type, relationship_type=relationship_type)
    return statement
