"""
Class that handles Nodes and Relationships
updates from a Mongo document.
"""
import re
import logging

from mongo_connector.doc_managers.nodes_and_relationships_builder import NodesAndRelationshipsBuilder

LOG = logging.getLogger(__name__)

class NodesAndRelationshipsUpdater(object):
  def __init__(self):
    self.statements_with_params = []

  def run_update(self, update_spec, doc_id, doc_type):
    params_dict = {"doc_id": doc_id}
    set_dict = {}
    for spec in update_spec.keys():
      if spec=='$set':
        update_value_list = update_spec['$set']
        for update_value in update_value_list.keys():
          if (self.is_relationship_update(update_value_list[update_value])):
            self.update_relationship(update_value_list[update_value], doc_type, update_value, doc_id)
          else:
            set_dict.update({update_value: update_value_list[update_value]})
        params_dict.update({"set_parameter": set_dict})
        statement = "MATCH (d:Document:{doc_type}) WHERE d._id={{doc_id}} SET d+={{set_parameter}}".format(doc_type=doc_type)
        self.statements_with_params.append({statement: params_dict})
      elif spec=='$unset':
        update_value_list = update_spec['$unset']
        for update_value in update_value_list.keys():
          statement = "MATCH (d:Document:{doc_type}), (c:Document:{update_value}) WHERE d._id={{doc_id}} OPTIONAL MATCH (d)-[r]-(c) DELETE r WITH d, c OPTIONAL MATCH (c)-[s]-() WITH d,c,s, CASE WHEN s IS NULL THEN c ELSE NULL END AS n DELETE n".format(doc_type=doc_type, update_value=update_value)
          self.statements_with_params.append({statement: params_dict})
          statement = "MATCH (d:Document:{doc_type} {{ _id: {{doc_id}} }} ) REMOVE d.{remove_parameter} ".format(doc_type=doc_type, remove_parameter=update_value)
          self.statements_with_params.append({statement: params_dict})
      else:
        self.handle_replacement(update_spec, doc_id, doc_type)
        break

  def handle_replacement(self, update_spec, doc_id, doc_type):
    params_dict = {"doc_id": doc_id}
    self.remove_legacy_nodes(doc_id, doc_type)
    for spec in update_spec.keys():
      if self.drop_id_spec(spec):
        if (self.is_relationship_update(update_spec[spec])):
          self.clear_node(doc_type, doc_id)
          self.update_relationship(update_spec[spec], doc_type, spec, doc_id)
        else:
          params_dict.update({"set_parameter": {spec: update_spec[spec]}})
          statement = "MATCH (d:Document:{doc_type}) WHERE d._id={{doc_id}} SET d={{set_parameter}}".format(doc_type=doc_type)      
          self.statements_with_params.append({statement: params_dict})

  def is_relationship_update(self, update_param):
    return (type(update_param) is dict)

  def update_relationship(self, document, root_type, doc_type, doc_id):
    builder = NodesAndRelationshipsBuilder(document, doc_type, doc_id, [root_type])
    builder.build_relationships_query(root_type, doc_type, doc_id, doc_id)
    self.statements_with_params.append(builder.query_nodes)
    self.statements_with_params.append(builder.relationships_query)

  def remove_legacy_nodes(self, doc_id, doc_type):
    params_dict = {"doc_id": doc_id}
    statement = "MATCH (d:Document:{doc_type}) WHERE d._id={{doc_id}} OPTIONAL MATCH (d)-[r]-(c) DELETE r WITH d, c OPTIONAL MATCH (c)-[s]-() WITH d,c,s, CASE WHEN s IS NULL THEN c ELSE NULL END AS n DELETE n".format(doc_type=doc_type)
    self.statements_with_params.append({statement: params_dict})

  def clear_node(self, doc_type, doc_id):
    params_dict = {"doc_id": doc_id}
    params_dict.update({"parameters": {"_id": doc_id}})
    statement = "MATCH (d:Document:{doc_type}) WHERE d._id={{doc_id}} SET d={{}} SET d={{parameters}}".format(doc_type=doc_type)     
    self.statements_with_params.append({statement: params_dict})

  def drop_id_spec(self, spec):
    if spec=='_id':
      return False
    return True


    

