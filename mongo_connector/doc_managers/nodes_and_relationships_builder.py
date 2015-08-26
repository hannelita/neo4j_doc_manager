"""
Class that builds Nodes and Relationships
according to a Mongo document.
"""

class NodesAndRelationshipsBuilder():
  def __init__(self, doc, doc_type, doc_id):
    self.query_nodes = {}
    self.doc_types = []
    self.build_nodes_query(doc_type, doc, doc_id)
    
  def build_nodes_query(self, doc_type, document, id):
    self.doc_types.append(doc_type)
    parameters = {'_id':id}
    for key in document.keys():
      if self.is_dict(document[key]):
        self.build_nodes_query(key, document[key], id)
      elif self.is_json_array(document[key]):
        for json in document[key]:
          json_key = key + str(document[key].index(json))
          self.build_nodes_query(json_key, json, id)
      else:
        parameters.update({ key: document[key] })
    query = "CREATE (c:Document:{doc_type} {{parameters}})".format(doc_type=doc_type)
    self.query_nodes.update({query: parameters})

  def is_dict(self, doc_key):
    return (type(doc_key) is dict)

  def is_json_array(self, doc_key):
    return ((type(doc_key) is list) and (type(doc_key[0]) is dict))

  def build_relationships_query(self, main_type, node_type):
    relationship_type = main_type + "_" + node_type
    statement = "MATCH (a:{main_type}), (b:{node_type}) WHERE a._id={{doc_id}} AND b._id ={{doc_id}} CREATE (a)-[r:{relationship_type}]->(b)".format(main_type=main_type, node_type=node_type, relationship_type=relationship_type)
    return statement
