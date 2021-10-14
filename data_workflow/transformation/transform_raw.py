import sys
import argparse
import importlib

import yaml
import json

from bs4 import BeautifulSoup
from pymongo import MongoClient

import FAIRsoft.meta_transformers as MT

def get_config(args):
    config_file = args[1]
    with open(config_file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return(config)
        except yaml.YAMLError as exc:
            print(exc)
    
    return(config)

def connect_mongo():
    client = MongoClient(port=27017)
    db = client.OPEB
    alambique = db.alambique
    pretools = db.pretools
    return(alambique, pretools)


if __name__ == '__main__':

    
    config = get_config(sys.argv)
    
    alambique, pretools = connect_mongo()
    

    ######----------- Data restructuring ------------------------------------##########
    def raw2tools(source):
        c = alambique.count({"@data_source":source})
        p = "{} entries from {}"
        print(p.format(c, source))
        if  c >0:
            raw = alambique.find({"@data_source":source})
            insts = MT.tool_generators[source](raw).instSet.instances #list of instances
            insts = [i.__dict__ for i in insts ]
            pretools.insert_many(insts)

    sources_to_integrate = config['source']

    for source in sources_to_integrate:
        print(source)
        raw2tools(source)
    
