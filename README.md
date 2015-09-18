![](https://travis-ci.org/neo4j-contrib/neo4j_doc_manager.svg)

# ALPHA STATE - NOT YET FOR PRODUCTION

# Overview

The [Neo4j](http://neo4j.com/) Doc Manager takes MongoDB documents and makes it easy to query them for relationships by making  them available in a Neo4j graph structure, following the format specified by [Mongo Connector](https://github.com/10gen-labs/mongo-connector).  It is intended for live one-way syncronization from MongoDB to Neo4j, where you have both databases running and take advantage of each databases' strength in your application (polyglot persistance).

# Installing

You must have Python installed in order to use this project. Python 3 is recommended.

First, install neo4j_doc_manager with pip:

```
pip install neo4j-doc-manager --pre
```

(You might need sudo privileges).

Refer to  [this document](https://github.com/neo4j-contrib/neo4j_doc_manager/blob/master/docs/neo4j_doc_manager_doc.adoc#21-setup) for more information if you experience any difficulties installing with pip. 

## Using Neo4j Doc Manager

Ensure that you have a Neo4j instance up and running. If you have authentication enabled (version 2.2+) for Neo4j, be sure to set **NEO4J_AUTH** environment variable, containing your user and password. 

```
export NEO4J_AUTH=user:password
```

Ensure that mongo is running a *replica set*. To initiate a replica set start mongo with:

```
mongod --replSet myDevReplSet
```


Then open [**mongo-shell**](http://docs.mongodb.org/master/tutorial/getting-started-with-the-mongo-shell/) and run:

```
rs.initiate()
```

Please refer to [Mongo Connector FAQ](https://github.com/10gen-labs/mongo-connector/wiki/FAQ) for more information. 


Start the mongo-connector service with the following command:

```
mongo-connector -m localhost:27017 -t http://localhost:7474/db/data -d neo4j_doc_manager
```

**-m** provides Mongo endpoint
**-t** provides Neo4j endpoint. Be sure to specify the protocol (http).
**-d** specifies Neo4j Doc Manager.


# Data synchronization

With the `neo4j_doc_manager` service running, any documents inserted into mongo will be converted into a graph structure and immediately inserted into Neo4j as well. Neo4j Doc Manager will turn keys into graph nodes. Nested values on each key will become properties.

To see this in action, insert the following document into mongo using the [mongo-shell](http://docs.mongodb.org/master/tutorial/getting-started-with-the-mongo-shell/):

~~~
db.talks.insert(  { "session": { "title": "12 Years of Spring: An Open Source Journey", "abstract": "Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio of open source projects up until 2015." }, "topics":  ["keynote", "spring"], "room": "Auditorium", "timeslot": "Wed 29th, 09:30-10:30", "speaker": { "name": "Juergen Hoeller", "bio": "Juergen Hoeller is co-founder of the Spring Framework open source project.", "twitter": "https://twitter.com/springjuergen", "picture": "http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg" } } );
~~~

This document will be converted to a graph structure and immediately inserted into Neo4j. Refer to [this document](https://github.com/neo4j-contrib/neo4j_doc_manager/blob/master/docs/neo4j_doc_manager_doc.adoc) for more information and examples.
