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
          statement = "MATCH (d:Document:{doc_type} {{ _id: {{doc_id}} }} ) REMOVE d.{remove_parameter} ".format(doc_type=doc_type, remove_parameter=update_value)
          self.statements_with_params.append({statement: params_dict})
      else:
        if self.drop_id_spec(spec):
          set_dict.update({spec: update_spec[spec]})
        params_dict.update({"set_parameter": set_dict})
        statement = "MATCH (d:Document:{doc_type}) WHERE d._id={{doc_id}} SET d={{set_parameter}}".format(doc_type=doc_type)      
        self.statements_with_params.append({statement: params_dict})

  def is_relationship_update(self, update_param):
    return (type(update_param) is dict)

  def update_relationship(self, document, root_type, doc_type, doc_id):
    builder = NodesAndRelationshipsBuilder(document, doc_type, doc_id, [root_type])
    self.statements_with_params.append(builder.query_nodes)
    self.statements_with_params.append(builder.relationships_query)


  def drop_id_spec(self, spec):
    if spec=='_id':
      return False
    return True


    

