#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This module aims at converting a csv file into a set of customs rules.
    More specificly it will read the columns and parse them using the given associative array
"""
__author__ = "Guilhem Heinrich"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Guilhem Heinrich"
__email__ = "guilhem.heinrich@inra.fr"
__status__ = "Prototype"

import argparse
import datetime
import csv
import yaml
import uuid
import re
import io
from string import Formatter

""" Unicode dict reader, from <https://stackoverflow.com/questions/5004687/python-csv-dictreader-with-utf-8-data>"""
def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    print(csv_reader)
    for row in csv_reader:
        print(row)
        # python2 => python3 row.iteritems() => row.items()
        yield {str(key, 'utf-8'):str(value, 'utf-8') for key, value in row.items()}

class CSVFormatter(object):
    """ A class to convert a csv to a rdf turtle file"""
    """ Initialize the attributes's instance with corresponding values"""
    def __init__(self, prefix="", postfix = "", assocRules=[], grouping={}):
        self.assoc_rules = assocRules
        self.prefix = prefix
        self.postfix = postfix
        self.grouping = grouping
        AllUuidPerRow = []
        for rule in self.assoc_rules:
            AllUuidPerRow += re.findall(r'\{(uuid_\d+)\}', rule)
        self.uuid_per_row = set(AllUuidPerRow)
    """ Intern method responsable of writing the 'agregated' or 'grouped' values"""
    def __computeGrouping(self, csvFile):
        groups_uuid = {}
        group_prefix = []
        with open(csvFile) as csvfile:
            reader = csv.DictReader(csvfile)
            for colKey in self.grouping.keys():
                group = self.grouping[colKey]
                groups_uuid[colKey] = {}
                ## dateNow need to be consistent across all rows of a grouping
                dateNow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                last_grouping_column_value = None 
                for row in reader:
                    for rowKey in row.keys():
                        ## Handle multiline string as litteral, clear unused space
                        if isinstance(row[rowKey], str):
                            row[rowKey] = ' '.join(row[rowKey].split())
                    if last_grouping_column_value == None:
                        group_uuid = str(uuid.uuid4())
                        last_grouping_column_value = row[colKey]
                    elif last_grouping_column_value != row[colKey]:
                        group_uuid = str(uuid.uuid4())
                    ## Added for further reference of the grouping inside the grouping rules
                    row['dateNow'] = dateNow
                    row['group_uuid'] = group_uuid
                    groups_uuid[colKey][row[colKey]] = group_uuid
                    line = ''
                    for rule in group:
                        line += rule.format(**row) + "\n"
                    # Removed python2 => 3
                    # line = line.encode('ascii', 'ignore')
                    group_prefix.append(line)
                    last_grouping_column_value = row[colKey]
            group_prefix = set(group_prefix)
        return groups_uuid, "\n".join(group_prefix)
    """ Intern method responsable of writing a single row"""
    def __processRow(self, row, stream, cpt, groups_uuid):
        # Handle multiline string as litteral
        for key in row.keys():
            if isinstance(row[key], str):
                row[key] = ' '.join(row[key].split())
        row['dateNow'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        # Handle grouping (uuid per column)
        for col in self.grouping:
            row[col] = groups_uuid[col][row[col]]
        # Handle uuid per row 
        for key in self.uuid_per_row:
            row[key] = str(uuid.uuid4())
        # Add an identifier for the row index
        row['row'] = cpt
        # Fullfil the rules
        for rule in self.assoc_rules:
            skip = False
            for value in Formatter().parse(rule):
                if value[1] is not None:  
                    if row[value[1]] is '':
                        skip = True
                        break
            if skip:
                continue
            line = rule.format(**row) + "\n"
            # Removed python2 => 3
            # line = line.encode('utf-8', 'ignore')
            stream.write(line)
        # stream.write('\n')
    """ Main public method, parsing a $csvFile into $outputstream""" 
    def parse_csv(self, csvFile, encoding='utf-8'):
        # """This function read a csv file and parse its content from as a turtle rdf file"""
        groups_uuid, group_prefix = self.__computeGrouping(csvFile)
        with open(csvFile, encoding=encoding) as csvfile:
            outputstream = io.StringIO()
            reader = csv.DictReader(csvfile)
            outputstream.write(self.prefix)
            outputstream.write('\n')
            outputstream.write(group_prefix)
            outputstream.write('\n')
            cpt = 0
            for row in reader:
                self.__processRow(row, outputstream, cpt, groups_uuid)
                cpt += 1
            outputstream.write(self.postfix)
        return outputstream


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = """ This module aims at converting a csv file into a text (or any extension) file.
    More specificly it will read the rows and columns and parse them using the given a parameter file.
    This parameter file precise prefixes, suffixes, the rules to execute every lines and the rules to execute only once.

    More specically, the config.yml file MAY have a prefix array and a postfix array, and a groupingRules dictionary.
    It MUST have an associative rules array.

    Each lines of the prefix, postfix, associtive array, and arrays in each entry of the groupingRules dictionary
    will be parse using the python string.format, whith python formating field delimiter : \{ ... \}.

    When specifying 'rules' to be parsed, the field between \{\} you should provide the columns names, or one 
    of the special values :
        'dateNow' => will output the current machine timestamp
        'row' => the actual row index
        'uuid_X' where X is one or more digit => a unique uuid generated every rows
    Inside the groupingRules, uuid_X and row are not supported, but the 'group_uuid' is available.
    This special field name will generate a unique value based on the key corresponding to the grouping rule.

    Here is a complete example config file :

    ---
    prefix:
    ## WILL BE PARSED ONCE, WRITING IT AT THE BEGINNING OF THE FILE
        PREFIX eventOntology: <http://www.phenome-fppn.fr/vocabulary/m3p/2015/event#> 
        PREFIX owl: <http://www.w3.org/2002/07/owl#> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX oa: <http://www.w3.org/ns/oa#> 
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX phenology: <http://www.phenome-fppn.fr/vocabulary/m3p/2018/phenology#>
        PREFIX time: <http://www.w3.org/2006/time#> 
        PREFIX agent: <http://www.phenome-fppn.fr/id/agent/> 
        PREFIX annotation: <http://www.phenome-fppn.fr/id/annotation/> 
        PREFIX instant: <http://www.phenome-fppn.fr/id/instant/> 
        PREFIX event: <http://www.phenome-fppn.fr/id/event/> 
    ## WILL BE PARSED ONCE, WRITING IT AT THE END OF THE FILE
    postfix:
    - ''
    ## WILL BE PARSED ONCE FOR EVERY DIFFERENT VALUE OF THE KEY, WRITING IT AT THE BEGIN OF THE FILE
    ## EACH ENTRY IN THE DICTIONARY IS THE NAME OF THE COLUMN USED FOR AGGREGATION
    groupingRules:
    Content:
    - annotation:{group_uuid} rdf:type oa:Annotation ;
    - '   oa:bodyValue "{Content}"^^xsd:string ;'
    - "   oa:motivatedBy oa:describing ;"
    - "   dcterms:creator agent:{Creator} ;"
    - '   dcterms:created "{Created}"^^xsd:dateTimeStamp .'
    ## WILL BE PARSED EVERY ROW
    associativeRules:
    - instant:{uuid_1} rdf:type time:Instant ;
    - '   time:inXSDDateTimeStamp "{Date event}"^^xsd:dateTimeStamp ;'
    - event:{uuid_1} rdf:type eventOntology:{RDFType} ;
    - "   time:hasTime instant:{uuid_1} ;"
    - "   eventOntology:concern <{uri}> ;"
    - '   eventOntology:hasPest "{RDFLabel}"^^xsd:string .'
    - annotation:{Content} oa:hasTarget event:{uuid_1} .


""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('configYAML', help="""Path to the configuration file to parse the csv, in yaml format.""")
    parser.add_argument('-i', dest = 'input', help="""Path to the input CSV file""")
    parser.add_argument('-e', dest = 'encoding', help="""Encoding of the CSV file""", default='utf-8')
    # parser.add_argument('-o', dest = 'output', help="""Path to the output turtle file""")
    args = parser.parse_args()
    with open(args.configYAML, 'r') as yamlconfigfile:
        config = yaml.load(yamlconfigfile)
        prefix = '\n'
        if ('prefix' in config):
            if isinstance(config['prefix'], str):
                prefix = config['prefix']
            else:
                prefix = ' \n'.join(config['prefix'])
        postfix = '\n'
        if ('postfix' in config):
            if isinstance(config['postfix'], str):
                postfix = config['postfix']
            else:
                postfix = ' \n'.join(config['postfix'])
        converter = CSVFormatter(\
        prefix,\
        postfix,\
        config['associativeRules'],\
        config['groupingRules'] if 'groupingRules' in config else {})
        output = converter.parse_csv(args.input, args.encoding)
        print(output.getvalue())
