# csv-formatter
Python tool to parse and format CSV

This file can be used as a python module or directly as an executable.
In the later case, it follows bash style covention for piping, with the two exemple sets provided :

    ./CSVformatter.py -i Agent_parsed.csv config_Agent_parsed.json > output_agent.ttl
    ./CSVformatter.py -i Agent_parsed.csv config_Agent_parsed.yml > output_agent.ttl
    
will write the result in an output_agent.ttl file
