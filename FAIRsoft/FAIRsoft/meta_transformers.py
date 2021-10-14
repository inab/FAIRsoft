import json
import pickle
import re
from munch import munchify
from pymongo import MongoClient

from FAIRsoft.utils import toolGenerator


global webTypes
webTypes = ['rest', 'web', 'app', 'suite', 'workbench', 'db', 'soap', 'sparql']


def extract_ids(id_):
    #extract ids from metrics @id
    fields = id_.split('/')
    if len(fields)>6:
        name = fields[5].split(':')[1]
        if len(fields[5].split(':'))>2:
            version = fields[5].split(':')[2]
        else:
            version = None
        type_ = fields[6]
    
        ids = {
            'name' : name,
            'version' : version,
            'type' : type_
        }

        return(ids)
    
    return


def cleanVersion(version):
    if version != None:
        if '.' in version:
            #print(version.split('.')[0]+'.'+ version.split('.')[1])
            return(version.split('.')[0]+'.'+ version.split('.')[1])
        else:
            return(version)
    else:
        return(version)

def get_repo_name_version_type(id_):
    fields = id_.split('/')
    name_plus = fields[5]
    name_plus_fields=name_plus.split(':')
    name=name_plus_fields[1]
    if len(name_plus_fields)>2:
        version=name_plus.split(':')[2]
    else:
        version=None 

    if len(fields)>6:
        type_=fields[6]
    else:
        type_=None
     
    return({'name':name, 'version':version, 'type':type_})


class repositoryToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'repository'):
        toolGenerator.__init__(self, tools, source)
        self.instSet = setOfInstances('repository')

        for tool in self.tools:
            # We skip generic entries
            if len(tool['@id'].split('/'))<7:
                continue
            else:
                id_data = get_repo_name_version_type(tool['@id'])
                name = clean_name(id_data['name'].lower())
                version = id_data['version']
                if version == None:
                    version = 'unknown'
                type_=id_data['type']
                if type_ == None:
                    type_ = 'unknown'

                newInst = instance(name, type_, [version])
                # there are several versions, to simplify integration, we want one instance per version
                if 'versions' in  tool['repos'][0]['res'].keys():
                    versions = tool['repos'][0]['res']['versions']
                else:
                    versions = [version]

                for v in versions:
                    newInst = instance(name, type_, versions)
                    
                    if tool['repos'][0]['res'].get('desc'):
                        newInst.description = [tool['repos'][0]['res'].get('desc')]
                    newInst.links = tool['entry_links']
                    newInst.publication =  None

                    binary_uri = tool['repos'][0]['res'].get('binary_uri')
                    source_uri = tool['repos'][0]['res'].get('source_uri')
                    download = [binary_uri, source_uri]
                    if None in download:
                        download.remove(None)
                    if source_uri or binary_uri:
                        newInst.download = download
                    else:
                        newInst.download = []  # list of lists: [[type, url], [], ...]
                    
                    newInst.inst_instr =  tool['repos'][0]['res'].get('has_tutorial')
                    newInst.test = None
                    try:
                        src = [tool['repos'][0]['res'].get('source_uri')]
                    except:
                        newInst.src = []
                    else:
                        if tool['repos'][0]['res'].get('source_uri')!=None:
                            newInst.src = src

                    if newInst.src:
                        newInst.os = ['Linux', 'Mac', 'Windows']
                    else:
                        newInst.os = None

                    newInst.input = None # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
                    newInst.output = None  # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> }
                    newInst.dependencies = None # list of strings
                    if tool['repos'][0]['res'].get('readmeFile'):
                        newInst.documentation = [['readme', tool['repos'][0]['res'].get('readmeFile')]] # list of lists [[type, url], [type, rul], ...]
                    if tool['repos'][0]['res'].get('source_license'):
                        newInst.license = [tool['repos'][0]['res'].get('source_license')] 
                        newInst.termsUse = [tool['repos'][0]['res'].get('source_license')] 
                    newInst.contribPolicy = None

                    auths = []
                    authors_l = tool['repos'][0]['res'].get('tool_developers')
                    if authors_l:
                        for author in authors_l:
                            auths.append('username')
                    newInst.authors = auths

                    newInst.repository = tool['entry_links']
                    newInst.source = [tool['repos'][0]['kind']] #string
                    newInst.bioschemas = None
                    newInst.https = None
                    newInst.operational = None
                    newInst.ssl = None
            
                    self.instSet.instances.append(newInst)


def clean_name(name):
    #TODO: clean emboss:  and emboss__ too
    name=name.lower()
    print(name)
    bioconductor=re.search("^bioconductor-", name)
    if bioconductor:
        name=name[bioconductor.end():]
    emboss_dots=re.search("^emboss: ", name)
    if emboss_dots:
        name=name[emboss_dots.end():]
    emboss_unders=re.search("^emboss__", name)
    if emboss_unders:
        name=name[emboss_unders.end():]
    return(name)

def set_type_bioconda(id_):
    if 'bioconductor' in id_:
        return('lib')
    else:
        return('cmd')


class biocondaRecipesToolsGenerator(toolGenerator):
    def __init__(self, tools, source="bioconda_recipes"):
        toolGenerator.__init__(self, tools, source)
        self.instSet = setOfInstances('bioconda_recipes')

        for tool in self.tools:
            name = clean_name(tool['name'])
            
            version = tool['@id'].split('/')[5].split(':')[2]
            type_ = tool['@id'].split('/')[6]
            if type_ == None:
                type_ =  set_type_bioconda(tool['@id'])

            if version == None:
                version = 'unknown'
            if type_ == None:
                type_ = 'unknown'
            
            newInst = instance(name, type_, [version])
            try:
                description = tool['about']['description']
            except:
                newInst.description = []
            else:
                if description:
                    newInst.description = [description] # string
            
            links = []
            if 'about' in tool.keys() and tool['about']:
                if 'home' in tool['about'].keys() and tool['about']['home']:
                    if tool['about']['home']:
                        links.append(tool['about']['home'])
        
            src = []
            if 'source' in tool.keys() and tool['source']:
                if 'url' in tool['source'] and tool['source']['url']:
                    
                    src = tool['source']['url']
                    if type(tool['source']['url'])==list:
                        for l in tool['source']['url']:
                            links.append(l)

                    else:
                        links.append(tool['source']['url'])


            
            try:
                doc_url = tool['about']['doc_url']
            except:
                pass
            else:
                if doc_url:
                    for d in doc_url:
                        links.append(d)

            newInst.links = links
            newInst.publication =  None # number of related publications [by now, for simplicity]
            if src:
                if type(src) != list:
                    src = [src]
                
                newInst.download = src
                
            newInst.inst_instr = True # boolean // FUTURE: u'ri or text
            newInst.test = None
            if 'test' in tool.keys():
                if tool['test']:
                    if 'commands' in tool['test'].keys():
                        newInst.test = True
            newInst.src = src # string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            newInst.input = [] # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
            newInst.output = [] # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> }
            deps = [] 
            if 'requirements' in tool.keys() and tool['requirements']:
                for req_k in tool['requirements'].keys():
                    if tool['requirements'][req_k]:
                        for dep in tool['requirements'][req_k]:
                            deps.append(dep)

            newInst.dependencies = deps # list of strings
            documentation = []
            try:
                doc = ['documentation',tool['about']['docs']]
                documentation.append(doc)
            except:
                pass

            try:
                doc = ['documentation', tool['about']['doc_url']]
                documentation.append(doc)
            except:
                pass

            newInst.documentation = documentation # list of lists [[type, url], [type, rul], ...]
            if 'about' in tool.keys():
                if tool['about'].get('license'):
                    newInst.license = [tool['about'].get('license')] 
                    newInst.termsUse = [tool['about'].get('license')] #
            newInst.contribPolicy = False
            credit = []
            try:
                auth=tool['about']['author']
            except:
                pass
            else:
                credit.append(auth)
            try:
                mantainers = tool['about']['mantainers']
            except:
                mantainers = None
            else:
                for m in mantainers:
                    credit.append(m)

            newInst.authors = credit # list of strings
            repository = []
            for l in links:
                if l:
                    if 'github' in l:
                        repository.append(l)
                    elif 'bitbucket' in l:
                        repository.append(l)
                    elif 'sourceforge' in l:
                        repository.append(l)

            newInst.repository = repository
            newInst.source = ['bioconda_recipes'] #string
            newInst.bioschemas = None
            newInst.https = None
            newInst.operational = None
            newInst.ssl = None

            self.instSet.instances.append(newInst)

class bioconda_conda_ToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'bioconda_conda'):
        toolGenerator.__init__(self, tools, source)
        self.instSet = setOfInstances('bioconda_conda')

        for tool in self.tools:
            id_info = extract_ids(tool['@id'])
            name = clean_name(id_info['name'])
            version = id_info['version']
            if version == None:
                version = 'unknown'
    
            type_ = set_type_bioconda(tool['@id'])
            if type_ == None:
                type_ = 'cmd'
            elif type_ == 'unknown':
                type_ = 'cmd'

            newInst = instance(name, type_, [version])

            newInst.description = None # string
            newInst.version = [version]
            newInst.type = type_
            newInst.links =[tool['url']]
            newInst.publication =  None # number of related publications [by now, for simplicity]
            newInst.download = [tool['url']]  # list of lists: [[type, url], [], ...]
            newInst.inst_instr = True # boolean // FUTURE: uri or text
            newInst.test = None # boolean // FUTURE: uri or text
            newInst.src = [] # string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            newInst.input = [] # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
            newInst.output = [] # list of dictionaries biotools-like {'format' : <format> , 'uri' : <uri> }
            newInst.dependencies = tool['dependencies'] # list of strings
            newInst.documentation = [] # list of lists [[type, url], [type, rul], ...]
            if 'license' in tool.keys():
                newInst.license = [tool['license']] # string
            newInst.termsUse = None #
            newInst.contribPolicy = None
            newInst.authors = [] # list of strings
            newInst.repository = []
            newInst.source = ['bioconda_conda'] #string
            newInst.bioschemas = None
            newInst.https = None
            newInst.operational = None
            newInst.ssl = None

            self.instSet.instances.append(newInst)




class biocondaToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'bioconda'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('bioconda')

        #names = [a['name'].lower() for a in self.tools]
        #print('diferent names in bioconda tools: ' + str(len(set(names))))

        for tool in self.tools:
            name = clean_name(tool['@label'])
            
            version = cleanVersion(tool['@version'])
            if version == None:
                version = 'unknown'
            type_ = 'cmd' # all biocondas are cmd

            newInst = instance(name, type_, [version])
            if 'description' in tool.keys():
                newInst.description = [tool['description']] # string
            if tool['web']['homepage']:
                newInst.links = [tool['web']['homepage']] #list
            else:
                newInst.links = []
            newInst.publication =  tool['publications'] 

            download = []
            for k in tool['distributions'].keys():
                for link in tool['distributions'][k]:
                    download.append(link)

            newInst.download = download

            newSrc = []
            for down in tool['distributions'].keys():
                if 'source' in down:
                    if len(tool['distributions'][down])>0:
                        for u in tool['distributions'][down]:
                            newSrc.append(u)
            newInst.src = newSrc 

            if 'license' in tool.keys() and tool['license']!='':
                newInst.license = [tool['license']] # string
            newInst.repository = tool['repositories']
            newInst.source = ['bioconda']
            newInst.links.append(tool['web']['homepage'])
            if tool['repositories']:
                for a in tool['repositories']:
                    newInst.links.append(a)

            self.instSet.instances.append(newInst)



class bioconductorToolsGenerator(toolGenerator):
    def __init__(self, tools, source='bioconductor'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('bioconductor')

        for tool in self.tools:
            type_= 'lib'
            version = cleanVersion(tool['Version'])
            if version == None:
                version = 'unknown'
            name = clean_name(tool['name'])
            newInst = instance(name, type_, [version])
            newInst.description = [tool['description']] # string
            if tool['URL']:
                newInst.links = [tool['URL']]
            else:
                newInst.links = []
            newInst.publication =  [tool['publication']] 
            download = []
            for a in ["Windows Binary", "Source Package", "Mac OS X 10 10.11 (El Capitan)"]:
                if a in tool.keys() and tool[a]:
                    download.append(tool['Package Short Url'] + tool[a])

            newInst.download = download
            newInst.inst_instr = tool['Installation instructions'] #
            newInst.src = [ a for a in newInst.download if a[0] == "Source Package"[0] ]# string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            if tool['Depends']:
                deps = tool['Depends']
            else:
                deps = []
            if tool['Imports']:
                impo = tool['Imports'].split(',')
            else:
                impo = []

            newInst.dependencies = [item for sublist in [deps+impo] for item in sublist] # list of strings

            newInst.documentation = [[ a, a[0] ] for a in tool['documentation']] # list of lists [[type, url], [type, rul], ...]
            if tool['License']!='':
                newInst.license = [tool['License']] # string
            else:
                newInst.license = False
            newInst.authors = [a.lstrip() for a in tool['authors']] # list of strings
            newInst.repository = [tool['Source Repository'].split('gitclone')[1]]
            newInst.description = [tool['description']]
            newInst.source = ['bioconductor'] #string

            self.instSet.instances.append(newInst)


def constrFormatsConfig(formatList):
    '''
    From an input that is a str to a biotools kind of format
    '''
    notFormats = ['data']
    newFormats = []
    seenForms = []
    for formt in formatList:
        if formt not in seenForms:
            if ',' in formt:
                formats = formt.split(',')
                for f in formats:
                    if f not in notFormats:
                        newFormats.append({ 'format' : {'term' : f , 'uri' :  None }})
                        seenForms.append(formt)
            else:
                if formt not in notFormats:
                    newFormats.append({ 'format' :  {'term' : formt , 'uri' :  None }})
                    seenForms.append(formt)
        else:
            continue
    return(newFormats)


class biotoolsOPEBToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'biotoolsOPEB'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('biotoolsOPEB')

        for tool in self.tools:
            if tool['@label']:
                name = clean_name(tool['@label'])
                type_ = tool['@type']
                version = cleanVersion(tool['@version'])
                if version == None:
                    version = 'unknown'
                if type_ == None:
                    type_ = 'unknown'

                newInst = instance(name, type_, [version])

                newInst.description = [tool['description']] # string
                newInst.publication = tool['publications']
                newInst.test = False
                if 'license' in tool.keys():
                    newInst.license = [tool['license']]
                newInst.input = []
                newInst.output = []
                if 'documentation' in tool.keys():
                    if 'general' in tool['documentation'].keys():
                        newInst.documentation = [['general', tool['documentation']['general']]]
                newInst.source = ['biotools']
                os = []
                if 'os' in tool.keys():
                    for o in tool['os']:
                        os.append(o)
                    newInst.os = os
                newInst.repository = tool['repositories']

                newInst.links.append(tool['web']['homepage'])
                if tool['repositories']:
                    for a in tool['repositories']:
                        newInst.links.append(a)

                if tool['semantics']:
                    if tool['semantics']['inputs']:
                        newInst.input = tool['semantics']['inputs']
                    if tool['semantics']['outputs']:
                        newInst.output = tool['semantics']['outputs']
                newInst.semantics = tool['semantics']

                newAuth = []
                for dic in tool['credits']:
                    if dic.get('name'):
                        if dic['name'] not in newAuth and dic['name']!=None:
                            newAuth.append(dic['name'])
                newInst.authors = newAuth

                self.instSet.instances.append(newInst)



class sourceforgeToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'sourceforge'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('sourceforge')

        for tool in self.tools:
            name = tool['@source_url'].split('/')[-1]
            
            name = name.lower()
            type_ = 'unknown'
            version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.source = ['sourceforge']
            os = []
            if 'operating_system' in tool.keys():
                for o in tool['operating_system']:
                    os.append(o)
                newInst.os = os
            newInst.repository = [tool['repository']]
            newInst.download = [tool['@source_url']]
            newInst.repository = [tool['@source_url']]
            newInst.links.append(tool['homepage'])

            self.instSet.instances.append(newInst)



class galaxyOPEBToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'galaxyOPEB'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('galaxyOPEB')

        for tool in self.tools:
        
            name = clean_name(tool['name'].lower())
            name=name.replace(' ','_') #so it is coherent with opeb metrics nameszz

            type_ = 'web'
            version = tool['@version']
            if version == None:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.description = [tool['description']] # string
            newInst.source = ['galaxy']
            newInst.os = ['Mac', 'Linux']
            newInst.repository = tool['repositories']
            if 'license' in tool.keys():
                newInst.license = [tool['license']]
            newInst.publication = tool['publications']

            self.instSet.instances.append(newInst)


class metricsOPEBToolsGenerator(toolGenerator):
    # TODO: obtain citations
    def __init__(self, tools, source = 'opeb_metrics'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('opeb_metrics')
        for tool in self.tools:
            ids = extract_ids(tool['@id'])
            if ids:
                version = ids['version']
                type_ = ids['type']
                # type needs to be corrected for galaxy tools from workflow to web
                if ids['type'] == 'workflow' and 'galaxy' in tool['@id']:
                    type_='web'
                if version == None:
                    version = 'unknown'
                if type_ == None:
                    type_ = 'unknown'
                name = clean_name(ids['name'].lower())
                newInst = instance(name, type_, [version])
                newInst.source = ['opeb_metrics']
                if tool['project'].get('website'):
                    newInst.bioschemas = tool['project']['website'].get('bioschemas')
                    newInst.https = tool['project']['website'].get('https')
                    newInst.ssl = tool['project']['website'].get('ssl')
                    if tool['project']['website'].get('operational') == 200:
                        newInst.operational = True
                    else:
                        newInst.operational = False
                if tool['project'].get('publications'):
                    newInst.publication = tool['project']['publications']
                    
                
                self.instSet.instances.append(newInst)


class galaxyShedToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'galaxyShed'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('toolshed')

        for tool in self.tools:
            name = clean_name(tool['name'].lower())
            type_ = 'cmd'
            if 'version' in tool.keys():
                version = cleanVersion(tool['version'])
            else:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.description = [tool['description']] # string
            newInst.inst_instr = True # Since this is installable through ToolShed
            if len(tool['tests'])>0:
                newInst.test = True # boolean
            else:
                newInst.test = False

            newInst.dependencies = [a['name'] for a in tool['requirements']] # list of strings
            newInst.repository = [] ### FILL!!!!!!!!!!!
            newInst.links = [] ### FILL!!!!!!!!!!!!
            newInst.source = ['toolshed']#string
            newInst.os = ['Linux', 'Mac']

            self.instSet.instances.append(newInst)


class galaxyMetadataGenerator(toolGenerator):
    def __init__(self, tools, source = 'galaxy_metadata'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('galaxy_metadata')

        for tool in self.tools:
            name = clean_name(tool['name'].lower())
            type_ = 'cmd'
            if 'version' in tool.keys():
                version = cleanVersion(tool['version'])
            else:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.dependencies = tool['dependencies'] # list of strings
            newInst.source = ['galaxy_metadata']

            self.instSet.instances.append(newInst)


class galaxyConfigToolsGenerator(toolGenerator):
    def __init__(self, tools, source = 'toolshed'):
        toolGenerator.__init__(self, tools, source)

        self.instSet = setOfInstances('toolshed')

        for tool in self.tools:
            if tool['name']:
                name = clean_name(tool['name'].lower())

                type_ = 'cmd'

                version = cleanVersion(tool['version'])
                if version == None:
                    version = 'unknown'

                newInst = instance(name, type_, [version])

                if tool['description']:
                    newInst.description = [tool['description']] # string

                if tool['citation']:
                    newInst.publication =  [tool['citation']] 

                newInst.test = tool['tests'] # boolean

                if len(tool['dataFormats']['inputs'])>0:
                    newInst.input = constrFormatsConfig(tool['dataFormats']['inputs']) # list of strings

                if len(tool['dataFormats']['outputs'])>0:
                    newInst.output = constrFormatsConfig(tool['dataFormats']['outputs']) # list of strings

                docu = []
                if tool['readme'] == True:
                    docu.append(['readme', None])
                if tool['help']:
                    docu.append(['help', tool['help'].lstrip()])

                newInst.documentation = docu # list of lists [[type, url], [type, url], ...]

                newInst.source = ['toolshed'] #string

                self.instSet.instances.append(newInst)



def lowerInputs(listInputs):
    newList = []
    if len(listInputs)>0:
        for format in listInputs:
            newFormat = {}
            for a in format.keys():
                newInner = {}
                if format[a] != []:
                    #print(format[a])
                    if type(format[a]) == list:
                        for eachdict in format[a]:
                            for e in eachdict.keys():
                                newInner[e] = eachdict[e].lower()
                            newFormat[a] = newInner
                    else:
                        for e in format[a].keys():
                            newInner[e] = format[a][e].lower()
                        newFormat[a] = newInner
        newList.append(newFormat)
    else:
        return([])
    return(newList)


# TODO" refactor this
class biotoolsToolsGenerator(toolGenerator):

    def __init__(self, tools, source = 'biotools'):

        toolGenerator.__init__(self, tools, source)

        self.splitInstances()


    def splitInstances(self):
        '''
        newInst.splitInstances returns the set of instances
        '''
        self.instSet = setOfInstances('biotools')
        names = [a['biotoolsID'].lower for a in self.tools]
        #print('diferent names in biotools tools: ' + str(len(set(names))))
        #print('diferent insatances in biotools tools: ' + len(names))
        for tool in self.tools:
            if len(tool['toolType']) > 0:
                for type_ in tool['toolType']:
                    vers = []
                    if len(tool['version']) > 0:
                        for version in tool['version']:

                            name = tool['@label'].lower()

                            newInst = instance(name, type_, [cleanVersion(version)])

                            newInst.description = tool['description']

                            newInst.homepage = tool['homepage']

                            newInst.publication = len(tool['publication'])
                            

                            newInst.download = [ [tol['type'], tol['url']] for tol in tool['download'] ]

                            src = []
                            for down in [a for a in tool['download'] if a['type'] == 'Source package']:
                                src.append(down['url'])
                            newInst.src =src

                            newInst.os = tool['operatingSystem']

                            inputs = []
                            if len(tool['function'])>0:
                                inputs = [f['input'] for f in tool['function']]
                                newInst.input = lowerInputs(inputs[0])
                            else:
                                newInst.input = []

                            outputs = []
                            if len(tool['function'])>0:
                                outputs = [f['input'] for f in tool['function']]
                                newInst.output = lowerInputs(outputs[0])
                            else:
                                newInst.output = []



                            newInst.documentation = [ [doc['type'], doc['url']] for doc in tool['documentation']]

                            if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                                newInst.inst_instr = True

                            newInst.license = tool['license']

                            newAuth = []
                            for dic in tool['credit']:
                                if dic['name'] not in newAuth and dic['name']!=None:
                                    newAuth.append(dic['name'])
                            newInst.authors = newAuth

                            repos = []
                            for link in tool['link']:
                                if link['type'] == "Repository":
                                    repos.append(link['url'])
                            newInst.repository = repos

                            newInst.description = tool['description']

                            newInst.source = ['biotools']

                            self.instSet.instances.append(newInst)


                    else:
                        version = None
                        name = tool['biotoolsID'].lower()
                        newInst = instance(name, type_, [cleanVersion(version)])

                        newInst.description = tool['description']

                        newInst.homepage = tool['homepage']

                        newInst.publication = len(tool['publication'])

                        newInst.download = [ [tol['type'], tol['url']] for tol in tool['download'] ]

                        src = []
                        for down in [a for a in tool['download'] if a['type'] == 'Source package']:
                            src.append(down['url'])
                        newInst.src =src

                        newInst.os = tool['operatingSystem']

                        inputs = []
                        inputs = [f['input'] for f in tool['function']]
                        if len(tool['function'])>0:
                            inputs = [f['input'] for f in tool['function']]
                            newInst.input = lowerInputs(inputs[0])
                        else:
                            newInst.input = []

                        outputs = []
                        if len(tool['function'])>0:
                            outputs = [f['input'] for f in tool['function']]
                            newInst.output = lowerInputs(outputs[0])
                        else:
                            newInst.output = []

                        newInst.documentation = [ [doc['type'], doc['url']] for doc in tool['documentation']]

                        if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                            newInst.inst_instr = True

                        newInst.license = tool['license']

                        newAuth = []
                        for dic in tool['credit']:
                            if dic['name'] not in newAuth and dic['name']!=None:
                                newAuth.append(dic['name'])
                        newInst.authors = newAuth

                        repos = []
                        for link in tool['link']:
                            if link['type'] == "Repository":
                                repos.append(link['url'])
                        newInst.repository = repos

                        newInst.description = tool['description']

                        newInst.source = ['biotools']

                        self.instSet.instances.append(newInst)

            else:
                type_ = None
                if len(tool['version']) > 0:
                    for version in tool['version']:

                        name = tool['biotoolsID'].lower()
                        newInst = instance(name, type_, [cleanVersion(version)])

                        newInst.description = tool['description']

                        newInst.homepage = tool['homepage']

                        newInst.publication = len(tool['publication'])

                        newInst.download = [ [tol['type'], tol['url']] for tol in tool['download'] ]

                        src = []
                        for down in [a for a in tool['download'] if a['type'] == 'Source package']:
                            src.append(down['url'])
                        newInst.src =src

                        newInst.os = tool['operatingSystem']

                        inputs = []
                        if len(tool['function'])>0:
                            inputs = [f['input'] for f in tool['function']]
                            newInst.input = lowerInputs(inputs[0])
                        else:
                            newInst.input = []

                        outputs = []
                        if len(tool['function'])>0:
                            outputs = [f['input'] for f in tool['function']]
                            newInst.output = lowerInputs(outputs[0])
                        else:
                            newInst.output = []

                        newInst.documentation = [ [doc['type'], doc['url']] for doc in tool['documentation']]

                        if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                            newInst.inst_instr = True

                        newInst.license = tool['license']

                        newAuth = []
                        for dic in tool['credit']:
                            if dic['name'] not in newAuth and dic['name']!=None:
                                newAuth.append(dic['name'])
                        newInst.authors = newAuth

                        repos = []
                        for link in tool['link']:
                            if link['type'] == "Repository":
                                repos.append(link['url'])
                        newInst.repository = repos

                        newInst.source = ['biotools']

                        self.instSet.instances.append(newInst)

                else:
                    version = None
                    name = tool['biotoolsID'].lower()
                    newInst = instance(name, type_, [cleanVersion(version)])

                    newInst.description = tool['description']

                    newInst.homepage = tool['homepage']

                    newInst.publication = len(tool['publication'])

                    newInst.download = [ [tol['type'], tol['url']] for tol in tool['download'] ]

                    src = []
                    for down in [a for a in tool['download'] if a['type'] == 'Source package']:
                        src.append(down['url'])

                    newInst.src =src

                    newInst.os = tool['operatingSystem']

                    inputs = []
                    if len(tool['function'])>0:
                        inputs = [f['input'] for f in tool['function']]
                        newInst.input = lowerInputs(inputs[0])
                    else:
                        newInst.input = []

                    outputs = []
                    if len(tool['function'])>0:
                        outputs = [f['input'] for f in tool['function']]
                        newInst.output = lowerInputs(outputs[0])
                    else:
                        newInst.output = []

                    newInst.documentation = [ [doc['type'], doc['url']] for doc in tool['documentation']]

                    if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                        newInst.inst_instr = True

                    newInst.license = tool['license']

                    newAuth = []
                    for dic in tool['credit']:
                        if dic['name'] not in newAuth and dic['name']!=None:
                            newAuth.append(dic['name'])
                    newInst.authors = newAuth

                    repos = []
                    for link in tool['link']:
                        if link['type'] == "Repository":
                            repos.append(link['url'])
                    newInst.repository = repos

                    newInst.source = ['biotools']

                    self.instSet.instances.append(newInst)


tool_generators = {
        'bioconductor' : bioconductorToolsGenerator,
        'biotools' : biotoolsOPEBToolsGenerator,
        'bioconda' : biocondaToolsGenerator,
        'toolshed' : galaxyConfigToolsGenerator,
        'galaxy_metadata' : galaxyMetadataGenerator,
        'sourceforge' : sourceforgeToolsGenerator,
        'galaxy' : galaxyOPEBToolsGenerator,
        'opeb_metrics' : metricsOPEBToolsGenerator,
        'bioconda_recipes': biocondaRecipesToolsGenerator,
        'bioconda_conda': bioconda_conda_ToolsGenerator,
        'repository': repositoryToolsGenerator,
}


