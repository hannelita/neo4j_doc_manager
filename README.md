![](https://travis-ci.org/neo4j-contrib/neo4j_doc_manager.svg)

# Overview

The main idea of [Neo4j](http://neo4j.com/) Doc Manager is to make Mongo information available into a Neo4j graph structure, following the format specified by [Mongo Connector](https://github.com/10gen-labs/mongo-connector).

#Use case

We assume that you are willing to have Mongo and Neo4j up and running into your project. We must then cover the following scenarios:
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
Neo4j Doc Manager will turn keys into graph nodes. The values contained on each key will become properties. 

### New Data
We assume that if a new information comes to Mongo and it successfully saves, then it goes to Neo4j. Future versions shall contain a more flexible way to handle new information.

# Using Neo4j Doc Manager

After cloning this repository, run:

```
mongo-connector -m localhost:27017 -t localhost:7474/db/test -d neo4j_doc_manager

```

**-m** provides Mongo endpoint
**-t** provides Neo4j endpoint
**-d** specifies Neo4j Doc Manager.
