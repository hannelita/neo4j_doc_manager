#!/usr/bin/env ruby

require 'json'

# Simple parser to collect mongo-connector.log output and create nodes markup on Arrows

# Expected input: paste the raw mongo-conector log create queties on a file called log

# Markup output will be held into a file called markup

# Arrows - http://www.apcjones.com/arrows/#
# Only nodes are created. Relationships must be manually stablished according to the markup synthax
# <li class="relationship" data-from="0" data-to="1">
#    <span class="type">talks_session</span>
#  </li>
# Remind to change node element ids

@@shared_id_counter = 0
@@rel_hash = {}


def self.analyse(cypher_query)
  node_label = /u\'CREATE \((.*)\`/
  label_str = node_label.match(cypher_query)
  if label_str
    label = ((label_str[0].split(" (c"))[1]).tr("`", "")
    li = "<li class=\"node\" data-node-id=\"#{@@shared_id_counter}\"> <span class=\"caption\">#{label}</span><dl class=\"properties\">"
    node_props = /\{\'parameters\': (.*)/
    node_props_str = node_props.match(cypher_query)
    props = ((((node_props_str[0].split("{\'parameters\': "))[1]).gsub("u'", "'")).chomp("}")).gsub("'", "\"")
    json_hash = JSON.parse(props)
    json_hash.each do |key, value|
        dt = "<dt>#{key}</dt><dd>#{value}</dd>"
        li << dt
    end
    li << "</li>\n"
    File.open("markup", 'a') { |file| file.write(li) }
    type = label.split(":Document:")[1]
    id = @@shared_id_counter
    @@rel_hash.store(id, type)
    @@shared_id_counter += 1
  end
end

def self.process(line)
  res = line.split("append ")
  self.analyse(res[1])
end

# def self.build_rel
#   li = "<li class="relationship" data-from="1" data-to="2"> <span class="type">talks_session</span></li>"
# end


File.open("log", "r") do |f|
  f.each_line do |line|
    self.process(line)
  end
 print @@rel_hash
end


