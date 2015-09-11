![](https://travis-ci.org/neo4j-contrib/neo4j_doc_manager.svg)

# Overview

The [Neo4j](http://neo4j.com/) Doc Manager takes MongoDB documents and makes it easy to query them for relationships by making  them available in a Neo4j graph structure, following the format specified by [Mongo Connector](https://github.com/10gen-labs/mongo-connector).  It is intended for live one-way syncronization from MongoDB to Neo4j, where you have both databases running and take advantage of each databases' strength in your application (polyglot persistance).

# Installing

You must have Python installed in order to use this project. Python 3 is recommended.

First, install mongo-connector:
```
pip install mongo-connector
```
Now install neo4j_doc_manager:

Clone this repository and set PYTHONPATH to it's local directory by running
```
export PYTHONPATH=.
```

## Using Neo4j Doc Manager

If you have authentication enabled for Neo4j, be sure to set **NEO4J_AUTH** environment variable, containing your user and password. 

```
export NEO4J_AUTH=user:password
```

After installing the package or cloning this repository, run:

```
mongo-connector -m localhost:27017 -t http://localhost:7474/db/test -d neo4j_doc_manager

```

**-m** provides Mongo endpoint
**-t** provides Neo4j endpoint. Specify the protocol (http) and also the database name (in our example we use __test__)
**-d** specifies Neo4j Doc Manager.


# Use case

We assume that you will have both Mongo and Neo4j running for your project. The syncronization process must cover both existing and new data.

### Existing data
Assuming that you might already have information on your Mongo Database, you should migrate these data to Neo4j graph structure.
For instance, let's consider the following JSON structure for your Mongo information:
```
{
  "session": {
    "title": "12 Years of Spring: An Open Source Journey",
    "abstract": "Spring emerged as a core open source project in early 2003 and evolved to a broad portfolio ..."
  },
  "topics":  ["keynote", "spring"], 
  "room": "Auditorium",
  "timeslot": "Wed 29th, 09:30-10:30",
  "speaker": {
    "name": "Juergen Hoeller",
    "bio": "Juergen Hoeller is co-founder of the Spring Framework open source project and ....",
    "twitter": "https://twitter.com/springjuergen",
    "picture": "http://www.springio.net/wp-content/uploads/2014/11/juergen_hoeller-220x220.jpeg"
  }
}
```
Neo4j Doc Manager will turn keys into graph nodes. Nested values on each key will become properties. 

### New Data
The current version takes any new information which is committed to Mongo and saves it to Neo4j. Future versions shall contain a more flexible way to handle new information.

