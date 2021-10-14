from munch import munchify
from pymongo import MongoClient
import json
from FAIRsoft.utils import instance
from FAIRsoft.integration import prepFAIRcomp

client = MongoClient(port=27017)
db = client.OPEB
tools = db.tools


def convert_dict2intance(tool):
    NewInst = instance(tool['name'], tool['type'], tool['version'])
    NewInst.__dict__ = munchify(tool)
    NewInst.set_super_type()

    return(NewInst)

def computeFAIR(instances):
    for ins in instances:
        ins.generateFAIRMetrics()
        ins.FAIRscores()

def save_metrics_scores(intances, out_path):
    out_inst_metrics_scr = []
    for ins in intances:
        dic = { **ins.metrics.__dict__, **ins.scores.__dict__ }
        # name, version, type are needed to identify the instance
        dic['name'] = ins.name
        dic['type'] = ins.type
        dic['version'] = ins.version
        out_inst_metrics_scr.append(dic)
       
    with open(out_path, 'w') as outfile:
        json.dump(out_inst_metrics_scr, outfile)


instances = []

for tool in tools.find():
    Inst = convert_dict2intance(tool)
    instances.append(Inst)

print('All dicts converted to instances')
prepFAIRcomp(instances)
print('Computing metrics and scores ...')
computeFAIR(instances)
print('Saving metrics and scores')
save_metrics_scores(instances, 'metrics_scores.json')
print('Done')
