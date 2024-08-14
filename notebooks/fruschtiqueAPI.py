#### Imports

import os
from pathlib import Path
import math
from xml.etree import ElementTree as ET
import urllib.parse
from urllib.request import pathname2url
import json
import codecs
import subprocess
import networkx as nx
from networkx.algorithms import bipartite
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from scipy.stats import entropy
from collections import Counter
import locale
import requests
from bs4 import BeautifulSoup
import uuid
from time import *
locale.setlocale(locale.LC_ALL, 'de-DE.utf-8')
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

####
#### CulinaryCollection class and its methods
####

class CulinaryCollection:
    
    def __init__(self, graphLab_path=None, descript_fn=None, igdtCat_path=None, working_dir=None):
        
        def subcoll_rcp (f_names):
            rcp_list = []
            for fn_rcp in f_names:
                with open(fn_rcp, 'r', encoding='utf-8') as f:
                    rcp_in = ET.parse(f)
                    rcp_root = rcp_in.getroot()
                    rcp_name = rcp_root.find('fr:recipeName', self.ns).text
                    rcp_list.append(rcp_name)
            return rcp_list
        
        # check for missing parameters
        if graphLab_path == None:
            print ('Specify path to graphLab.')
            return None
        if descript_fn == None:
            print ('Specify descriptor filename.')
            return None
        if igdtCat_path == None:
            print ('Specify path to ingredients catalogue.')
            return None
        if working_dir == None:
            print ('Specify working directory.')
            return None
        
        # set namespaces
        self.ns = {'fr': 'http://fruschtique.de/ns/recipe', 'fe': 'http://fruschtique.de/ns/fe', 'ns0': 'http://fruschtique.de/ns/recipe'}
        # set object variables
        self.graphLab_path = graphLab_path
        self.descript_fn   = descript_fn
        self.igdtCat_path  = igdtCat_path
        self.working_dir   = working_dir
        # read descriptor file
        descriptor = graphLab_path + descript_fn
        with open(descriptor, 'r', encoding='utf-8') as d:
            descript = ET.parse(d)
            self.d_root = descript.getroot()
            self.exp_name = self.d_root.find('fe:experimentName', self.ns).text
        # read ingredients catalogue   
        with open(igdtCat_path, encoding='utf-8') as file:
            self.cat            = json.load(file)
            self.catIngredients = self.cat.get('ingredients')
            self.catClasses     = self.cat.get('classes')
            self.noRefIgts      = self.cat.get('noRefIgts')
        # read list of recipes in collection
        file_in = graphLab_path + self.d_root.find('fe:experimentPath', self.ns).text + 'catalogue.xml'
        with open(file_in, 'r', encoding='utf-8') as f:
            list_in = ET.parse(f)
            root_in = list_in.getroot()
        self.in_files = [urllib.parse.unquote(doc.get("href")[8:], encoding="utf-8") for doc in root_in.findall('doc')]
        # check for subcollections
        if self.d_root.find('fe:A-collection', self.ns) != None and self.d_root.find('fe:B-collection', self.ns) != None:
            self.collType = 'double'
            coll_A = self.d_root.find('fe:A-collection', self.ns)
            author_A = coll_A.find('fe:A-author', self.ns).text
            collName_A = coll_A.find('fe:A-name', self.ns).text
            coll_B = self.d_root.find('fe:B-collection', self.ns)
            author_B = coll_B.find('fe:B-author', self.ns).text
            collName_B = coll_B.find('fe:B-name', self.ns).text
            # check for subcollection directories
            common = os.path.commonpath(self.in_files)
            os.chdir (common)
            sub_paths = [p for p in os.listdir() if os.path.isdir(p)]
            if len(sub_paths) == 2:
                self.subCollLtrs = sub_paths
            elif len(sub_paths) == 1 or len(sub_paths) > 2:
                print ('Wrong number of subcollection dir_paths.')
                return None
            elif len(sub_paths) == 0:
                self.subCollLtrs = []
            if self.subCollLtrs[0] != None:
                collDir_A = self.subCollLtrs[0]
            else:
                print ('No directory for subcollection A.')
                return None
            if self.subCollLtrs[1] != None:
                collDir_B = self.subCollLtrs[1]
            else:
                print ('No directory for subcollection B.')
                return None
        else:
            self.collType = 'single'
        # get metadata from descriptor
        title = self.d_root.find('fe:fullTitle', self.ns).text
        # collect recipe names and related ingredients
        self.full_rcp_list = []
        for fn_rcp in self.in_files:
            with open(fn_rcp, 'r', encoding='utf-8') as f:
                rcp_in = ET.parse(f)
                rcp_root = rcp_in.getroot()
                rcp_name = rcp_root.find('fr:recipeName', self.ns).text
                igdts = []
                igdts_elem = rcp_root.findall('.//fr:igdtName',self.ns)
                xx = [(igt.get("ref"),igt.text.lower()) for igt in igdts_elem]
                for (ref, igt_name) in xx:
                    if ref == None:
                        raise Exception(f"Missing reference to ingredients catalogue for {igt_name.upper()} in recipe {rcp_name.upper()}")
                        return
                    elif ref == '':
                        found = False
                        for noRef in self.noRefIgts:
                            if noRef in igt_name:
                                found = True
                                break
                        if found == False: 
                            raise Exception(f"Null reference to ingredients catalogue for {igt_name.upper()} in recipe {rcp_name.upper()}")
                            return
                    else:
                        igdts.append(ref) 
                igdts = list(set(igdts))                                
                rcp = {'recipeName' : rcp_name, 'ingredients' : igdts}
                self.full_rcp_list.append(rcp)          
        # get subcollection files and prepare collection entry for coll_data.json
        meta = dict(title=title,collType=self.collType)
        if self.collType == 'double':
            f_names_A = [fn for fn in self.in_files if os.path.basename(os.path.dirname(fn)) == self.subCollLtrs[0]]
            f_names_B = [fn for fn in self.in_files if os.path.basename(os.path.dirname(fn)) == self.subCollLtrs[1]]        
            # create recipe and subcollection lists
            sub_coll_rcp_A = subcoll_rcp (f_names_A)
            sub_coll_rcp_B = subcoll_rcp (f_names_B)       
            rcp_dict = {'meta':meta, 'collections':{sub_paths[0]:{'name':collName_A, 'author':author_A,'recipes':sub_coll_rcp_A}, \
                                                    sub_paths[1]:{'name':collName_B, 'author':author_B,'recipes':sub_coll_rcp_B}}, \
                                                    'recipes': self.full_rcp_list}    
        elif self.collType == 'single':
            rcp_dict = dict(meta=meta, recipes=self.full_rcp_list)
        else:
            print ('Unknown error.')
            return
        # write rcp_dict to json
        outfile = f"{os.path.join(self.working_dir,self.exp_name)} coll data.json"
        with open(outfile, 'w', encoding ='utf8') as f:
            json.dump(rcp_dict, f, ensure_ascii=False)
        # read coll_data.json  
        with open(outfile, 'r', encoding='utf-8') as file:
            self.coll = json.load(file) 
        self.recipes     = [rcp for rcp in self.coll.get('recipes')]
        self.ingredients = list(set(igt for rcp in self.recipes for igt in rcp.get('ingredients')))
        #create the inverted index as dict
        self.index = dict()
        for igt in self.catIngredients.items():
            x = dict()
            k = igt[0]
            x = {k:k}
            self.index.update(x)
            y = dict()
            for syn in igt[1].get('synonyms'):
                y = {syn:k}
                self.index.update(y)     
        return
            
    def __str__(self):
        exp = f"Experiment: {self.exp_name}"
        if self.collType == 'single':
            print_str = f"{exp}\n{self.exp_name} has a collection with {len(self.recipes)} recipes with {len(self.ingredients)} distinct ingredients\nsupported by an ingredients catalog with {len(self.catIngredients)} entries in {len(self.catClasses)} classes\n"
        elif self.collType == 'double':
            print_str = f"{exp}\nCollection with {len(self.recipes)} recipes in {len(self.subCollLtrs)} subcollections with {len(self.ingredients)} distinct ingredients\nsupported by an ingredients catalog with {len(self.catIngredients)} entries in {len(self.catClasses)} classes\n"
        else:
            print ('Unknown error.')
            return None
        return print_str
    
    def listSubcolls (self):
        if self.collType == 'double':
            xx = [{'letter':k, 'name':self.coll.get('collections').get(k,v).get('name'), \
                    'author':self.coll.get('collections').get(k,v).get('author'), \
                    'rcpCount':len(self.listRecipes(k)), \
                    'igtCount':len(self.listIngredients(k)) \
                    } \
                    for (k,v) in self.coll.get('collections').items()]
            return xx
        else:
            print ('No subcollections in this collection.')
            return None
        
    def listRecipes (self,coll=None):
        if (self.collType == 'single') and (coll==None):
            return self.recipes
        elif (self.collType == 'double') and (coll in self.subCollLtrs):
            return self.coll.get('collections').get(coll).get('recipes')
        else:
            return []
        
    def listIngredients (self,coll=None):
        if (self.collType == 'single') and (coll==None):
            return self.ingredients
        elif self.collType == 'double' and coll in self.subCollLtrs:
            xx = [rcp for rcp in self.coll.get('collections').get(coll).get('recipes')]
            yy = [igt for rcp in self.coll.get("recipes") if rcp.get('recipeName') in xx for igt in rcp.get('ingredients')]
            zz = list(set(yy))
            zz.sort(key=locale.strxfrm)
            return zz
        else:
            return []
                
    def listIngredientsCatalog (self, select=None):
        xx = list (self.catClasses.keys())
        if select == None:
            return [igt for igt in self.cat]
        elif type(select) is str and select in xx:
            return [igt for igt in self.cat.get('ingredients') if self.cat.get('ingredients').get(igt).get('i-class') == select]
        elif type(select) is list:
            return [self.catIngredients.get(s) for s in select]
        
    def cosine_sim (self):

        def co_sim (a,b):
            return dot(a, b)/(norm(a)*norm(b))
        
        def vec (occ_d=None):
            d = {}
            for i in self.ingredients:
                d[i] = 0
            for k,v in occ_d.items():
                d[k] = v        
            vector = dict(sorted(d.items()))
            return list(vector.values())
        
        if self.collType != 'double':
            print ("Cosine similarity computation available only for collections with two subcollections.")
            return None
        rcp_A  = self.listRecipes(self.subCollLtrs[0])
        rcp_B  = self.listRecipes(self.subCollLtrs[1])
        occ_dict_A = Counter([igt for rcp in self.recipes if rcp.get('recipeName') in rcp_A for igt in rcp.get('ingredients')])
        occ_dict_B = Counter([igt for rcp in self.recipes if rcp.get('recipeName') in rcp_B for igt in rcp.get('ingredients')])
        vec_A     = vec(occ_dict_A)
        vec_B     = vec(occ_dict_B)
        sim_total = co_sim(vec_A, vec_B)
        res = {'total':sim_total}
        for c in list(self.catClasses.keys()):
            occ_dict_A_class = Counter([igt for rcp in self.coll.get("recipes") if rcp.get('recipeName') in rcp_A for igt in rcp.get('ingredients') if self.catIngredients.get(igt).get('i-class') == c])
            if sum(occ_dict_A_class.values()) != 0:
                occ_dict_B_class = Counter([igt for rcp in self.coll.get("recipes") if rcp.get('recipeName') in rcp_B for igt in rcp.get('ingredients') if self.catIngredients.get(igt).get('i-class') == c])
                if sum(occ_dict_B_class.values()) != 0:
                    vec_A_class = vec(occ_dict_A_class)
                    vec_B_class = vec(occ_dict_B_class)
                    sim_class   = co_sim(vec_A_class, vec_B_class)
                    res.update({c:sim_class}) 
        return res
    
    def entropy(self):
        if self.collType == 'single':
            p = list(Counter([igt for rcp in self.coll.get("recipes") for igt in rcp.get('ingredients')]).values())
            return {'entropy':entropy(p, base=2)}
        elif self.collType == 'double':
            rcp_A  = self.listRecipes(self.subCollLtrs[0])
            rcp_B  = self.listRecipes(self.subCollLtrs[1])
            p_A = list(Counter([igt for rcp in self.coll.get("recipes") if rcp.get('recipeName') in rcp_A for igt in rcp.get('ingredients')]).values())
            p_B = list(Counter([igt for rcp in self.coll.get("recipes") if rcp.get('recipeName') in rcp_B for igt in rcp.get('ingredients')]).values())
            return {'entropy_A':entropy(p_A, base=2), 'entropy_B':entropy(p_B, base=2)}
        else:
            print ('Unknown error.')
            return None
        
    def toGraph (self, coll=None):
        
        def igtGraph (i2r):
            B = nx.Graph(from_coll=coll,created_by='fruschtique CulinaryCollection')
            X = nx.Graph(from_coll=coll,created_by='fruschtique CulinaryCollection')
            top = [rcp.get('recipeName') for rcp in i2r]
            bottom = list(set([igt for rcp in i2r for igt in rcp.get('ingredients')]))
            e_list = []
            for rcp in i2r:
                name = rcp.get('recipeName')
                for igt in rcp.get('ingredients'):
                    e_list.append((name,igt))
                    if igt=='öl':
                        print (igt, name)
            B.add_nodes_from(top, bipartite=0)
            B.add_nodes_from(bottom, bipartite=1)
            B.add_edges_from(e_list)
            X = bipartite.weighted_projected_graph(B, bottom)
            #print ([igt for igt in bottom])
            attr_dict = {igt: {'i-name':self.catIngredients[igt].get('i-name'),'i-class':self.catIngredients[igt].get('i-class')} for igt in bottom}
            occ_list = [igt for rcp in i2r for igt in rcp.get('ingredients')]
            self.occ_dict = Counter(occ_list)
            occ_attr = {k:{'occ':self.occ_dict.get(k)} for k in self.occ_dict.keys()}
            nx.set_node_attributes(X, attr_dict)
            nx.set_node_attributes(X, occ_attr)
            e_attr = {}
            for e in list(X.edges(data=True)):
                x = [e[0],e[1]]
                x.sort(key=locale.strxfrm)
                id = str(x[0]) + '--' + str(x[1])
                xx = (e[0],e[1])
                e_attr[xx] = {'id':id}
            nx.set_edge_attributes(X, e_attr)
            return X
        
        # create graph for collection with no subcollections
        if self.collType == 'single':
            if coll != None:
                print('Misplaced subcollection specification. Aborted.')
                return None
            else:
                i2r = [rcp for rcp in self.coll.get('recipes')]
                G1 = igtGraph(i2r)
                # add sub attribute to nodes
                sub_dict = {nd:{'sub':'A'} for nd in list(G1.nodes())}
                nx.set_node_attributes(G1,sub_dict)
                # add sub attribute to edges 
                sub_dict = {ed:{'sub':'A'} for ed in list(G1.edges())}
                nx.set_edge_attributes(G1,sub_dict)
                return G1  
        # create graph for collection with subcollections
        elif self.collType == 'double':
            if type(coll) is str:
                if len(coll) != 1:
                    print('Use a single character for subcollection specification.')
                else:
                    # create graph from single subcollection
                    xx = [rcp for rcp in self.coll.get('collections').get(coll).get('recipes')]
                    i2r = [rcp for rcp in self.coll.get("recipes") if rcp.get('recipeName') in xx]
                    G1 = igtGraph(i2r)
                    # add sub attribute to nodes
                    sub_dict = {nd:{'sub':coll} for nd in list(G1.nodes())}
                    nx.set_node_attributes(G1,sub_dict)
                    # add sub attribute to edges 
                    sub_dict = {ed:{'sub':coll} for ed in list(G1.edges())}
                    nx.set_edge_attributes(G1,sub_dict)
                    return G1
            elif type(coll) is list:
                if len(coll) > 2:
                    print('Two subcollections is maximum for graph creation.')
                    return None
                elif not(coll[0] in self.subCollLtrs):
                    print (f"The subcollection {coll[0]} is not contained in this collection.")
                    return None
                elif not(coll[1] in self.subCollLtrs):
                    print (f"The subcollection {coll[1]} is not contained in this collection.")
                    return None
                else:
                    i2r = [rcp for rcp in self.coll.get("recipes")]
                    GG = igtGraph(i2r)
                    Aingredients = set(self.listIngredients('A'))
                    Bingredients = set(self.listIngredients('B'))
                    ABingredients = Aingredients.intersection(Bingredients)
                    Aingredients_pure = Aingredients.difference(ABingredients)
                    Bingredients_pure = Bingredients.difference(ABingredients)
                    Asub_dict = {igt: {'sub':'A'} for igt in Aingredients_pure}
                    Bsub_dict = {igt: {'sub':'B'} for igt in Bingredients_pure}
                    ABsub_dict = {igt: {'sub':'AB'} for igt in ABingredients}
                    sub_dict = {**Asub_dict, **Bsub_dict, **ABsub_dict}
                    nx.set_node_attributes(GG, sub_dict)
                    A_attr   = {(e[0],e[1]):{'sub': 'A'}   for e in list(GG.edges(data=True)) if (e[0] in Aingredients_pure and e[1] in Aingredients_pure)}
                    AAB_attr = {(e[0],e[1]):{'sub': 'AAB'} for e in list(GG.edges(data=True)) if (e[0] in Aingredients_pure and e[1] in ABingredients) or (e[0] in ABingredients and e[1] in Aingredients_pure)}
                    B_attr   = {(e[0],e[1]):{'sub': 'B'}   for e in list(GG.edges(data=True)) if (e[0] in Bingredients_pure and e[1] in Bingredients_pure)}
                    BAB_attr = {(e[0],e[1]):{'sub': 'BAB'} for e in list(GG.edges(data=True)) if (e[0] in Bingredients_pure and e[1] in ABingredients) or (e[0] in ABingredients and e[1] in Bingredients_pure)}
                    AB_attr  = {(e[0],e[1]):{'sub': 'AB'}  for e in list(GG.edges(data=True)) if e[0] in ABingredients and e[1] in ABingredients}
                    e_attr = {**A_attr,**AAB_attr,**B_attr,**BAB_attr,**AB_attr}
                    nx.set_edge_attributes(GG, e_attr)
                    return GG        
            else:
                print ('Unknown error.')
        
    def nodeSets(self,graph=None,coll=None):
        if graph == None:
            print ('Specify graph.')
            return None
        elif coll == None:
            return graph.nodes(data=True)
        elif type(coll) is str:
            if len(coll) != 1:
                print('Use a single character for subcollection specification.')
                return None
            elif not(coll in self.subCollLtrs):
                print(f"Subcollection {coll} does not exist.")
                return None
            else:
                self.A_nodes = set ([n for n,attr in graph.nodes(data=True) if attr.get('sub') == coll])
                return list(self.A_nodes)
        elif type(coll) is list:
            if len(coll) > 2:
                print('Two subcollections is maximum for node set generation.')
                return None
            elif not(coll[0] in self.subCollLtrs):
                print (f"The subcollection {coll[0]} is not contained in this collection.")
                return None
            elif not(coll[1] in self.subCollLtrs):
                print (f"The subcollection {coll[1]} is not contained in this collection.")
                return None
            else:
                xx = f"{coll[0]}{coll[1]}"
                self.AB_nodes = [n for (n,attr) in graph.nodes(data=True) if attr.get('sub') == xx]
                return self.AB_nodes
        else:
            return None
    
    def edgeSets(self,graph=None,coll=None):         
        if graph == None:
            print ('Specify graph.')
            return None
        elif coll == None:
            return graph.edges(data=True)
        if type(coll) is str:
            if len(coll) != 1:
                print('Use a single character for subcollection specification.')
                return None
            elif not(coll in self.subCollLtrs):
                print(f"Subcollection {coll} does not exist.")
                return None
            else:
                n_A  = [n for n,attr in graph.nodes(data=True) if attr.get('sub') == coll]
                A_e_pure  = [e for e in graph.edges(data=True) if e[0] in n_A and e[1] in n_A]
                return A_e_pure  
        elif type(coll) is list:
            if len(coll) > 2:
                print('Two subcollections is maximum for edge set generation.')
                return None
            elif not(coll[0] in self.subCollLtrs):
                print (f"The subcollection {coll[0]} is not contained in this collection.")
                return None
            elif not(coll[1] in self.subCollLtrs):
                print (f"The subcollection {coll[1]} is not contained in this collection.")
                return None
            else:
                n_A  = [n for n,attr in graph.nodes(data=True) if attr.get('sub') == coll[0]]
                n_B  = [n for n,attr in graph.nodes(data=True) if attr.get('sub') == coll[1]]
                n_AB = [n for n,attr in graph.nodes(data=True) if attr.get('sub') == f"{coll[0]}{coll[1]}"]
                A_edges        = [e for e in graph.edges(data=True) if e[0] in n_A and e[1] in n_A]
                B_edges        = [e for e in graph.edges(data=True) if e[0] in n_B and e[1] in n_B]
                AAB_edges      = [e for e in graph.edges(data=True) if (e[0] in n_A and e[1] in n_AB) or (e[1] in n_A and e[0] in n_AB)]
                BAB_edges      = [e for e in graph.edges(data=True) if (e[0] in n_B and e[1] in n_AB) or (e[1] in n_B and e[0] in n_AB)]
                AB_edges = [e for e in graph.edges(data=True) if e[0] in n_AB and e[1] in n_AB]
                return {'A_edges' : A_edges, 'B_edges' : B_edges, 'AAB_edges' : AAB_edges, 'BAB_edges' : BAB_edges, 'AB_edges' : AB_edges}
        else:
            return None
    
    def Krack(self,graph=None):

        def Krack (EL,IL):
            return (EL-IL)/(EL+IL)
        
        # parameter checking
        if self.collType != 'double':
            print ('Krackhardt index computation available only for collections with subcollections.')
            return
        elif graph == None:
            print ('Missing graph specification.')
            return
        else:
            nodes_A = self.listIngredients('A')
            nodes_B = self.listIngredients('B')
            IL_A    = len([attr.get("id") for n1,n2,attr in graph.edges(data=True) \
                if (n1 in nodes_A) and (n2 in nodes_A)])
            EL_A    = len([attr.get("id") for n1,n2,attr in graph.edges(data=True) \
                if ((n1 in nodes_A) and not(n2 in nodes_A)) or ((not(n1 in nodes_A)) and (n2 in nodes_A))])
            IL_B    = len([attr.get("id") for n1,n2,attr in graph.edges(data=True) \
                if (n1 in nodes_B) and (n2 in nodes_B)])
            EL_B    = len([attr.get("id") for n1,n2,attr in graph.edges(data=True) \
                if ((n1 in nodes_B) and not(n2 in nodes_B)) or ((not(n1 in nodes_B)) and (n2 in nodes_B))])              
            #print ('IL_A: ',IL_A)
            #print ('EL_A: ',EL_A)
            #print ('IL_B: ',IL_B)
            #print ('EL_B: ',EL_B)
            return {'Krack_A' : Krack(EL_A,IL_A), 'Krack_B' : Krack(EL_B,IL_B)}
        
    def graphToDot(self,graph=None):
        if graph == None:
            print ('Missing graph specification.')
            return
        dot = 'graph {\ngraph[rankdir="LR", outputorder="edgesfirst"]\nnode[fontname="Arial", fontsize=120, shape=circle, style=filled, fixedsize=shape];\n'
        for u,v,att in graph.edges(data=True):
            x = [u,v]
            x.sort(key=locale.strxfrm)
            u = x[0]
            v = x[1]
            dot += u+' -- '+v+' [penwidth='+str(att.get('weight'))
            dot += ', id='+'"'+u+"--"+v+'"'
            if att.get('weight') > 1:
                dot += ', color=Red]\n'
            else:
                dot += ']\n'
        for u,att in graph.nodes(data=True):
            dot += u+' [width=' + str(1+3*math.sqrt(att.get('occ'))) + ', label=' + str(att.get('i-name')) + ', class=' + str(att.get('i-class')) + ']\n'
        dot += '}'
        fn = f"{self.exp_name}.dot"
        p = Path(self.working_dir)
        outfile = p / fn
        with codecs.open(outfile, 'w', encoding = 'utf8') as file:
            file.write(dot)
        return
    
    def graphToGEXF(self,graph=None): 
        if graph == None:
            print ('Missing graph specification.')
            return
        ns = {"gr": "http://www.gexf.net/1.2draft"}
        root = ET.Element('gr:gexf', attrib={"xmlns:gr":"http://www.gexf.net/1.2", "xmlns:viz":"http://www.gexf.net/1.2/viz", \
        "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance", "xsi:schemaLocation":"http://www.gexf.net/1.2 https://gexf.net/1.2/gexf.xsd", \
        "version":"1.2"})
        meta = ET.SubElement(root,"gr:meta",attrib={"lastmodifieddate":"2023-09-15"})
        creator = ET.SubElement(meta, "gr:creator")
        creator.text = "Norbert Luttenberger"
        description = ET.SubElement(meta, "gr:description")
        description.text = "fruschtique Ingredient Graph in gexf notation"
        g_graph = ET.SubElement(root,"gr:graph",attrib={"defaultedgetype":"undirected"})
        attributes = ET.SubElement(g_graph, "gr:attributes", attrib={"class":"node"})
        attribute_0 = ET.SubElement(attributes, "gr:attribute", attrib={"id":"0","title":"occ","type":"float"})
        attribute_1 = ET.SubElement(attributes, "gr:attribute", attrib={"id":"1","title":"i-class","type":"string"})        
        nodes = ET.SubElement(g_graph, "gr:nodes") 
        for n,attr in graph.nodes(data=True):
            node = ET.SubElement(nodes, "gr:node", attrib={"id":n, "label":self.catIngredients.get(n).get("i-name")})
            att_values = ET.SubElement(node,"gr:attvalues")
            att_value  = ET.SubElement(att_values,"gr:attvalue", attrib={"for":"0","value":str(attr.get("occ"))})
            att_value  = ET.SubElement(att_values,"gr:attvalue", attrib={"for":"1","value":str(attr.get("i-class"))})
        edges = ET.SubElement(g_graph, "gr:edges")
        for n1,n2,attr in graph.edges(data=True):
            edge = ET.SubElement(edges, "gr:edge", attrib={"id":attr.get("id"), "source":n1, "target":n2, "weight":str(attr.get("weight"))})
        tree = ET.ElementTree(root)
        ET.indent(tree)
        fn = f"{self.exp_name}.gexf"
        p = Path(self.working_dir)
        outfile = p / fn
        tree.write(outfile, encoding='UTF-8', xml_declaration='<?xml version="1.0" encoding="UTF-8"?>')
        return
    
    def graphToCSV(self,graph=None):
        if graph == None:
            print ('Missing graph specification.')
            return
        p = Path(self.working_dir)
        # nodes
        fn = f"{self.exp_name} nodes.csv"
        outfile = p / fn
        with codecs.open(outfile, 'w', encoding = 'utf8') as file:
            file.write('n,i-name,i-class,occ,sub\n')
            for (n,attr) in graph.nodes(data=True):
                file.write(f"{n},{attr.get('i-name')},{attr.get('i-class')},{attr.get('occ')},{attr.get('sub')}\n")
        # edges
        fn = f"{self.exp_name} edges.csv"
        outfile = p / fn
        if self.collType == 'single':
            with codecs.open(outfile, 'w', encoding = 'utf8') as file:
                file.write('id,n1,n2,weight,sub\n')
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},{attr.get('sub')}\n") \
                    for n1,n2,attr in (graph.edges(data=True))]
            return
        else:
            A_nodes  = self.nodeSets(graph,self.subCollLtrs[0])
            #print (len(A_nodes))
            B_nodes  = self.nodeSets(graph,self.subCollLtrs[1])
            #print (len(B_nodes))
            AB_nodes = self.nodeSets(graph,[self.subCollLtrs[0],self.subCollLtrs[1]])
            #print ('len AB', len(AB_nodes))
            with codecs.open(outfile, 'w', encoding = 'utf8') as file:
                file.write('id,n1,n2,weight,sub\n')
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},A\n") \
                    for n1,n2,attr in (graph.edges(data=True)) \
                    if (n1 in A_nodes) and (n2 in A_nodes)]
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},B\n") \
                    for n1,n2,attr in (graph.edges(data=True)) \
                    if (n1 in B_nodes) and (n2 in B_nodes)]
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},AB\n") \
                    for n1,n2,attr in (graph.edges(data=True)) \
                    if (n1 in AB_nodes) and (n2 in AB_nodes)]
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},AAB\n") \
                    for n1,n2,attr in (graph.edges(data=True)) \
                    if ((n1 in A_nodes) and (n2 in AB_nodes)) or ((n1 in AB_nodes) and (n2 in A_nodes))]
                [file.write(f"{attr.get('id')},{n1},{n2},{attr.get('weight')},BAB\n") \
                    for n1,n2,attr in (graph.edges(data=True)) \
                    if ((n1 in B_nodes) and (n2 in AB_nodes)) or ((n1 in AB_nodes) and (n2 in B_nodes))]
            return
    
    def SVGMakerInit(self,graph=None):
        """Initialize the SVG Maker of the fruschtique Culinary Collection Class.
        Steps as follows:
        1 -- Create dot file for collection from graph.
        2 -- Call sfdp subprocess and create svg file for collection. 
        3 -- Create pandas representation for graph nodes and edges.
        """
        # 1 -- dot file
        infile  = f"{os.path.join(self.working_dir,self.exp_name)}.dot"
        if not(os.path.isfile(infile)):
            self.graphToDot(graph)
        # 2 -- svg file
        outfile = f"{os.path.join(self.working_dir,self.exp_name)} poor graph.svg"
        if not(os.path.isfile(outfile)):
            subprocess.run (['sfdp', infile, '-o', outfile, '-Goverlap=prism', '-Tsvg'])
        # 3 -- pandas representation
        # columns for nodes:
        #   id               ingredient/node id
        #   sub              subcollection indicator (A, B, AB, or None)
        #   occ              ingredient occurrence in collection
        #   class            ingrendient class
        #   cx_fd            x coordinate for node center, fd stands for force-directed layout
        #   cy_fd            y coordinate for node center, fd stands for force-directed layout
        #   rx_fd            x radius, fd stands for force-directed layout
        #   ry_fd            y radius, fd stands for force-directed layout
        # columns for edges:
        #   id               edge id, coded by <start-id>--<end-id>, where start-id alphabetically < end-id
        #   sub
        #   start_id         id of start node
        #   end_id           id of end node
        #   weight
        #   start_x_fd       x coordinate for start point, fd stands for force-directed layout
        #   start_y_fd       y coordinate for start point, fd stands for force-directed layout
        #   end_x_fd         x coordinate for end point, fd stands for force-directed layout
        #   end_y_fd         y coordinate for end point, fd stands for force-directed layout
        #   start_x_node     x coordinate for start at node center
        #   start_y_node     y coordinate for start at node center
        #   end_x_node       x coordinate for end at node center
        #   end_y_node       y coordinate for end at node center
        # read graphics file just created
        with open(outfile, 'r', encoding='utf-8') as s:
            ss = ET.parse(s)
        svg_in = ss.getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        self.transform = svg_in.find('svg:g[@id="graph0"]',ns).get('transform')
        self.viewbox   = svg_in.get('viewBox')
        # nodes
        t0 = process_time()
        node_coords = {node.find("svg:title", ns).text: (node.find("svg:ellipse", ns).attrib['cx'], \
                                                         node.find("svg:ellipse", ns).attrib['cy'], \
                                                         node.find("svg:ellipse", ns).attrib['rx'], \
                                                         node.find("svg:ellipse", ns).attrib['ry']  \
                                                        ) for node in svg_in.findall(".//svg:g[@class='node']", ns)}
        text_coords = {node.find("svg:title", ns).text: (node.find("svg:text", ns).attrib['x'], \
                                                         node.find("svg:text", ns).attrib['y']  \
                                                        ) for node in svg_in.findall(".//svg:g[@class='node']", ns)}
        self.nds = pd.DataFrame({ 
                        'sub'  : [att.get('sub') for i,att in graph.nodes(data=True)], \
                        'occ'  : [self.occ_dict.get(k) for k in graph.nodes()], \
                        'name' : [att.get('i-name') for i,att in graph.nodes(data=True)], \
                        'class': [self.cat.get('ingredients').get(k).get('i-class') for k in graph.nodes()], \
                        'cx_fd': [node_coords.get(k)[0] for k in graph.nodes()], \
                        'cy_fd': [node_coords.get(k)[1] for k in graph.nodes()], \
                        'rx_fd': [node_coords.get(k)[2] for k in graph.nodes()], \
                        'ry_fd': [node_coords.get(k)[3] for k in graph.nodes()], \
                        'txt_x': [text_coords.get(k)[0] for k in graph.nodes()], \
                        'txt_y': [text_coords.get(k)[1] for k in graph.nodes()]  \
                        }, \
                        index = graph.nodes() \
                        )
        t1 = process_time()
        print ('runtime for generating svg nodes in pandas dataframe: ', t1-t0)
        # compute initial font size
        self.fontsize = math.ceil(float(max(self.nds['rx_fd']))/10)
        #print ('font size: ', self.fontsize)
        # edges
        t0 = process_time()
        #for u,v,attr in graph.edges(data=True):
        #    #if svg_in.find(f".//svg:g[@id='{attr.get('id')}']/svg:path", ns).attrib['d'] == None:
        #    print (attr.get('id'))
        path_coords = [svg_in.find(f".//svg:g[@id='{attr.get('id')}']/svg:path", ns).attrib['d'] for u,v,attr in graph.edges(data=True)]
        self.eds = pd.DataFrame({
            'start_id'    : [u for u,v,attr in graph.edges(data=True)], \
            'end_id'      : [v for u,v,attr in graph.edges(data=True)], \
            'sub'         : [attr.get('sub')    for u,v,attr in graph.edges(data=True)], \
            'weight'      : [attr.get('weight') for u,v,attr in graph.edges(data=True)], \
            'start_x_fd'  : [coords.split(',')[0][1:]           for coords in path_coords], \
            'start_y_fd'  : [coords.split(',')[1].split('C')[0] for coords in path_coords], \
            'end_x_fd'    : [coords.split(' ')[2].split(',')[0] for coords in path_coords], \
            'end_y_fd'    : [coords.split(' ')[2].split(',')[1] for coords in path_coords], \
            'start_x_node': [node_coords[u][0]                  for u,v,attr in graph.edges(data=True)], \
            'start_y_node': [node_coords[u][1]                  for u,v,attr in graph.edges(data=True)], \
            'end_x_node'  : [node_coords[v][0]                  for u,v,attr in graph.edges(data=True)], \
            'end_y_node'  : [node_coords[v][1]                  for u,v,attr in graph.edges(data=True)]  \
        }, index = [attr.get('id') for u,v,attr in graph.edges(data=True)])
        t1 = process_time()
        print ('runtime for generating svg edges in pandas dataframe: ', t1-t0)
        return
    
    def previewHTML(self,scale=1.0):
        # read poor graph.svg
        infile = f"{os.path.join(self.working_dir,self.exp_name)} poor graph.svg"
        with open(infile, 'r', encoding='utf-8') as f:
            svg_in = ET.parse(f)
            root_in = svg_in.getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        # compute font size and transform parameter        
        font_size = self.fontsize * scale
        transform = root_in.find('svg:g[@id="graph0"]',ns).get('transform')
        # create html head section
        preview = ET.Element('html')
        head  = ET.SubElement(preview, 'head')
        # node styling css
        style = ET.SubElement(head, 'style')
        style.text = \
        ' .i-alc   {fill: #7087ED; stroke: #7087ED; background-color: #7087ED}' +\
        ' .i-carb  {fill: #C8A98B; stroke: #C8A98B; background-color: #C8A98B}' +\
        ' .i-condi {fill: #D58680; stroke: #D58680; background-color: #D58680}' +\
        ' .i-egg   {fill: #70A287; stroke: #70A287; background-color: #70A287}' +\
        ' .i-etc   {fill: #9AA6BF; stroke: #9AA6BF; background-color: #9AA6BF}' +\
        ' .i-fat   {fill: #81CDD8; stroke: #81CDD8; background-color: #81CDD8}' +\
        ' .i-fish  {fill: #ffdab9; stroke: #ffdab9; background-color: #ffdab9}' +\
        ' .i-fruit {fill: #7FDD46; stroke: #7FDD46; background-color: #7FDD46}' +\
        ' .i-herb  {fill: #95A84E; stroke: #95A84E; background-color: #95A84E}' +\
        ' .i-meat  {fill: #EE5874; stroke: #EE5874; background-color: #EE5874}' +\
        ' .i-milk  {fill: #6EA2DC; stroke: #6EA2DC; background-color: #6EA2DC}' +\
        ' .i-nuts  {fill: #D09E44; stroke: #D09E44; background-color: #D09E44}' +\
        ' .i-onion {fill: #60C667; stroke: #60C667; background-color: #60C667}' +\
        ' .i-spice {fill: #FF7F50; stroke: #FF7F50; background-color: #FF7F50}' +\
        ' .i-sweet {fill: #CDE1A6; stroke: #CDE1A6; background-color: #CDE1A6}' +\
        ' .i-veg   {fill: #65DDB7; stroke: #65DDB7; background-color: #65DDB7}'
        # js functions for buttons
        script = ET.SubElement(head, 'script')
        script.text = \
        'function show_A()    {' +\
        'let g0 = document.getElementById("graph0");' +\
        'let g1 = g0.cloneNode(false);' +\
        'g0.remove();' +\
        'const n = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'n.setAttribute("href","#A_nodes");' +\
        'g1.appendChild (n);' +\
        'let svg = document.getElementsByTagName("svg")[0];' +\
        'svg.appendChild(g1);' +\
        '};' +\
        'function show_B()    {' +\
        'let g0 = document.getElementById("graph0");' +\
        'let g1 = g0.cloneNode(false);' +\
        'g0.remove();' +\
        'const n = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'n.setAttribute("href","#B_nodes");' +\
        'g1.appendChild (n);' +\
        'let svg = document.getElementsByTagName("svg")[0];' +\
        'svg.appendChild(g1);' +\
        '};' +\
        'function show_AB()   {' +\
        'let g0 = document.getElementById("graph0");' +\
        'let g1 = g0.cloneNode(false);' +\
        'g0.remove();' +\
        'const n = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'n.setAttribute("href","#AB_nodes");' +\
        'g1.appendChild (n);' +\
        'let svg = document.getElementsByTagName("svg")[0];' +\
        'svg.appendChild(g1);' +\
        '};' +\
        'function show_full() {' +\
        'let g0 = document.getElementById("graph0");' +\
        'let g1 = g0.cloneNode(false);' +\
        'g0.remove();' +\
        'const nA = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'nA.setAttribute("href","#A_nodes");' +\
        'g1.appendChild (nA);' +\
        'const nB = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'nB.setAttribute("href","#B_nodes");' +\
        'g1.appendChild (nB);' +\
        'const nAB = document.createElementNS("http://www.w3.org/2000/svg","use");' +\
        'nAB.setAttribute("href","#AB_nodes");' +\
        'g1.appendChild (nAB);' +\
        'let svg = document.getElementsByTagName("svg")[0];' +\
        'svg.appendChild(g1);' +\
        '};' 
        # create button area in HTML body
        body  = ET.SubElement(preview, 'body')
        div_attr   = {'style':'width:auto;height:120px;'}
        div_form   = ET.SubElement(body,'div', attrib=div_attr)
        buttonA_attr = {'id':'btn_graph_A', 'type':'button','onclick':'show_A()', 'style':f"cursor:pointer;font-size:24px; margin:24px; padding:12px"}
        buttonA      = ET.SubElement(div_form, 'button', attrib=buttonA_attr)
        buttonA.text = 'subgraph A'
        buttonB_attr = {'id':'btn_graph_B', 'type':'button','onclick':'show_B()', 'style':f"cursor:pointer;font-size:24px; margin:24px; padding:12px"}
        buttonB      = ET.SubElement(div_form, 'button', attrib=buttonB_attr)
        buttonB.text = 'subgraph B'
        buttonAB_attr = {'id':'btn_graph_AB', 'type':'button','onclick':'show_AB()', 'style':f"cursor:pointer;font-size:24px; margin:24px; padding:12px"}
        buttonAB      = ET.SubElement(div_form, 'button', attrib=buttonAB_attr)
        buttonAB.text = 'subgraph A ∩ B'
        buttonfull_attr = {'id':'btn_graph_full', 'type':'button','onclick':'show_full()', 'style':f"cursor:pointer;font-size:24px; margin:24px; padding:12px"}
        buttonAB      = ET.SubElement(div_form, 'button', attrib=buttonfull_attr)
        buttonAB.text = 'full graph'
        # create SVG div
        div   = ET.SubElement(body,'div')
        svg_out_attr = {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'version':'1.1', 'viewBox':root_in.get('viewBox')}
        svg_out = ET.SubElement(div, 'svg', attrib=svg_out_attr)
        # create SVG defs for graph nodes
        defs = ET.SubElement(svg_out,'defs')
        nodes_A = ET.SubElement(defs, 'g', id='A_nodes')
        nodes_B = ET.SubElement(defs, 'g', id='B_nodes')
        nodes_AB = ET.SubElement(defs, 'g', id='AB_nodes')
        for n in self.nds.index:
            sub = self.nds.at[n,'sub']
            if   sub ==  'A' : def_el = nodes_A
            elif sub ==  'B' : def_el = nodes_B
            elif sub == 'AB' : def_el = nodes_AB
            else: def_el = None
            node_attr   = {'class':'node', 'id':n, 'data-sub':sub, 'style':'cursor: pointer;'}
            node        = ET.SubElement(def_el, 'g', attrib=node_attr)
            title       = ET.SubElement(node, 'title')
            title.text  = f"#occ: {self.nds.at[n,'occ']}"
            ellip_class = f"i-{self.nds.at[n,'class']}"            
            ellip_attr  = {'class':ellip_class, 'cx':self.nds.at[n,'cx_fd'], 'cy':self.nds.at[n,'cy_fd'], 'rx':self.nds.at[n,'rx_fd'], 'ry':self.nds.at[n,'ry_fd']}
            ET.SubElement(node, 'ellipse', attrib=ellip_attr)
            text_attr   = {'x':self.nds.at[n,'txt_x'], 'y':self.nds.at[n,'txt_y'], 'style':f"text-anchor: middle; font-family: Arial Narrow; font-size: {font_size}px;"}
            text        = ET.SubElement(node, 'text', attrib=text_attr)
            text.text   = self.nds.at[n,'name'] 
        # create SVG main graph
        graph0_attr = {'transform':transform, 'id':'graph0'}
        graph0 = ET.SubElement(svg_out,'g', attrib=graph0_attr)
        use_attr = {'href':'#A_nodes'}
        ET.SubElement(graph0,'use', use_attr)
        use_attr = {'href':'#B_nodes'}
        ET.SubElement(graph0,'use', use_attr)
        use_attr = {'href':'#AB_nodes'}
        ET.SubElement(graph0,'use', use_attr)
        # write HTML to file
        tree = ET.ElementTree(preview)
        ET.indent(tree)
        outfile = f"{os.path.join(self.working_dir,self.exp_name)} preview.html"
        tree.write(outfile)
        return
    
    def makeSVG(self,graph=None,rcpName=None,occ_growing=None,wgt_growing=None,ix=None,scale=1.0):
        """
        make SVG for partial graph, use occ_growing and wgt_growing
        """
        #ns = {'fr': 'http://fruschtique.de/ns/recipe', 'fe': 'http://fruschtique.de/ns/fe', 'fc': 'http://fruschtique.de/ns/igt-catalog'}
        # svg header
        w  = self.viewbox.split()[2]
        h  = self.viewbox.split()[3]
        svg_out_attr = {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'version':'1.1', 'viewbox':self.viewbox, \
                        'preserveAspectRatio':'xMidYMid meet', 'zoomAndPan':'magnify', 'contentScriptType':'text/ecmascript', 'contentStyleType':'text/css', 'width':w, 'height':h}
        svg_out = ET.Element('svg', attrib=svg_out_attr)
        style = ET.SubElement(svg_out, 'style')
        style.text = \
            ' .i-alc   {fill: #7087ED; stroke: #7087ED; background-color: #7087ED}' +\
            ' .i-carb  {fill: #C8A98B; stroke: #C8A98B; background-color: #C8A98B}' +\
            ' .i-condi {fill: #D58680; stroke: #D58680; background-color: #D58680}' +\
            ' .i-egg   {fill: #70A287; stroke: #70A287; background-color: #70A287}' +\
            ' .i-etc   {fill: #9AA6BF; stroke: #9AA6BF; background-color: #9AA6BF}' +\
            ' .i-fat   {fill: #81CDD8; stroke: #81CDD8; background-color: #81CDD8}' +\
            ' .i-fish  {fill: #ffdab9; stroke: #ffdab9; background-color: #ffdab9}' +\
            ' .i-fruit {fill: #7FDD46; stroke: #7FDD46; background-color: #7FDD46}' +\
            ' .i-herb  {fill: #95A84E; stroke: #95A84E; background-color: #95A84E}' +\
            ' .i-meat  {fill: #EE5874; stroke: #EE5874; background-color: #EE5874}' +\
            ' .i-milk  {fill: #6EA2DC; stroke: #6EA2DC; background-color: #6EA2DC}' +\
            ' .i-nuts  {fill: #D09E44; stroke: #D09E44; background-color: #D09E44}' +\
            ' .i-onion {fill: #60C667; stroke: #60C667; background-color: #60C667}' +\
            ' .i-spice {fill: #FF7F50; stroke: #FF7F50; background-color: #FF7F50}' +\
            ' .i-sweet {fill: #CDE1A6; stroke: #CDE1A6; background-color: #CDE1A6}' +\
            ' .i-veg   {fill: #65DDB7; stroke: #65DDB7; background-color: #65DDB7}'
        # svg graph
        g0_node_attr = {'id':'graph0', 'transform':self.transform}
        g0_node = ET.SubElement(svg_out,'g',attrib=g0_node_attr)    
        rcp_g_attr = {'id':f"rr-{ix}"}
        rcp_g      = ET.SubElement(g0_node,'g',attrib=rcp_g_attr)
        name_field = ET.SubElement(rcp_g,'g')
        nf_back_attr = {'x':str(200.0), 'y':str(400.0 - float(h)), 'width':str(float(w)/3), 'height':str(float(h)/16), 'fill':'white', 'stroke':'white', 'stroke-width':'1', 'fill-opacity':'1', 'stroke-opacity':'1'}
        nf_back      = ET.SubElement(name_field, 'rect', nf_back_attr) 
        nf_text_attr = {'x':str(240.0), 'y':str(600.0 - float(h)), 'style':f"text-anchor: start; font-family: Arial Narrow; font-size: {1.5 * self.fontsize * scale}px;"}
        nf_text      = ET.SubElement(name_field, 'text', nf_text_attr)
        nf_text.text = f"{ix:02d} {rcpName}"
        #print (nf_text.text)
        # recipe graph edges
        for u,v,att in graph.edges(data=True):
            ed_id       = att.get('id')
            edge_attr   = {'class':'edge', 'id':ed_id, 'style':'cursor: pointer;'}
            edge        = ET.SubElement(rcp_g, 'g', attrib=edge_attr)
            start_x     = self.eds.at[ed_id,'start_x_node']
            start_y     = self.eds.at[ed_id,'start_y_node']
            end_x       = self.eds.at[ed_id,'end_x_node']
            end_y       = self.eds.at[ed_id,'end_y_node']
            pt_coor     = f"M{start_x},{start_y}L{end_x},{end_y}"
            xx = wgt_growing.get(ed_id)
            if xx == 1:
                path_attr   = {'fill':'none', 'stroke': 'black', 'd':pt_coor}
            elif xx == 2: 
                path_attr   = {'fill':'none', 'stroke': 'black', 'stroke-width':'2', 'd':pt_coor}
            elif xx > 2: 
                path_attr   = {'fill':'none', 'stroke': 'red', 'stroke-width':'2', 'd':pt_coor}
            else: 
                path_attr   = {'fill':'none', 'stroke': 'black', 'd':pt_coor}
            path        = ET.SubElement(edge,'path',path_attr)
        # recipe graph nodes
        font_size = self.fontsize * scale
        for n in graph.nodes():
            node_attr   = {'class':'node', 'id':n, 'data-sub':self.nds.at[n,'sub'], 'style':'cursor: pointer;'}
            node        = ET.SubElement(rcp_g, 'g', attrib=node_attr)
            title       = ET.SubElement(node, 'title')
            title.text  = f"#occ: {occ_growing.get(n)}"
            ellip_class = f"i-{self.nds.at[n,'class']}" 
            x           = 36*(1 + 3*math.sqrt(occ_growing.get(n)))
            rx          = str(round(x*2, 0)/2)
            ry          = rx              
            ellip_attr  = {'class':ellip_class, 'cx':self.nds.at[n,'cx_fd'], 'cy':self.nds.at[n,'cy_fd'], 'rx':rx, 'ry':ry}
            ET.SubElement(node, 'ellipse', attrib=ellip_attr)
            text_attr   = {'x':self.nds.at[n,'txt_x'], 'y':self.nds.at[n,'txt_y'], 'style':f"text-anchor: middle; font-family: Arial Narrow; font-size: {self.fontsize * scale}px;"}
            text        = ET.SubElement(node, 'text', attrib=text_attr)
            text.text   = self.nds.at[n,'name'] 
        # return svg
        return svg_out
    
    def createSVGSequence(self,rcpNames=None,targetDir=None,scale=1.0):
        """
        generate svg per recipe graph in order as given by rcpNames list
        collect resulting svg files in directory
        node coordinates to be taken from ingredient graph svg
        edge coordinates to be taken from start and end node coordinates
        provide occ_growing and weight_growing to SVGMaker
        """
        # init
        K  = nx.Graph()                                  # empty recipe graph (complete graph)
        ix = 1                                           # sequence number
        font_size = self.fontsize * scale
        print ('Fontsize: ', font_size)
        occ_growing = {idx:0 for idx in self.nds.index}  # init occ_growing
        wgt_growing = {idx:0 for idx in self.eds.index}  

        p = Path(self.working_dir)
        ddd = p / self.working_dir / self.exp_name / targetDir 
        ddd.mkdir(parents=True, exist_ok=True)     
        # loop over recipes in collection for creating recipe graphs
        for rcpName in rcpNames:                         # collect ingredients for recipe graph
            occ_list = []
            rcp_igt_set = set()
            xx = rcpName.get('ingredients')
            for ingredient in xx:
                rcp_igt_set.add(ingredient)
            occ_list.extend(list(rcp_igt_set))
            K = nx.complete_graph(rcp_igt_set)           # build recipe graph
            for k in rcp_igt_set:
                occ_growing[k] += 1              
            # add attributes to edges of G
                # edge id
            e_attr = {}
            for e in list(K.edges(data=True)):
                x = [e[0],e[1]]
                x.sort(key=locale.strxfrm)
                id = str(x[0]) + '--' + str(x[1])
                xx = (e[0],e[1])
                e_attr[xx] = {'id':id}
            nx.set_edge_attributes(K, e_attr)
            for k in list(nx.get_edge_attributes(K,'id').values()):
                wgt_growing[k] += 1
            # save to file
            
            build = self.makeSVG(K,rcpName.get('recipeName'),occ_growing,wgt_growing,ix,scale)
            tree = ET.ElementTree(build)
            ET.indent(tree)
            fn = f"{ix:03d} {rcpName.get('recipeName')}.svg"
            file_path = ddd / fn
            tree.write(file_path)
            ix += 1
        return

    def sortByContrib2IG(self, rcpNames=None):
        """
        sort recipes by contribution of distinct ingredients to full graph, descending
        """
        # function for sorting subset of Pandas dataframe
        def sort_sub(df, i1, i2, by_col):
            a = df.iloc[i1:i2].copy()
            a.sort_values(by=by_col, inplace=True, ascending=False, ignore_index=True)
            df.iloc[i1:i2] = a
            return df
        
        # collect ingredients lists
        igt_sets = []
        for rcp in rcpNames:    
            igt_set = set(rcp.get('ingredients'))
            igt_sets.append(igt_set)
        count = [len(igt_set) for igt_set in igt_sets]
        # create Pandas dataframe for recipes and their ingredients
        collection_df = pd.DataFrame({'number':range(1,len(rcpNames)+1), 'rcp_names': rcpNames, 'rcp_ingredients': igt_sets, 'count_igt': count})
        # first: recipe with max number of ingredients
        collection_df.sort_values(by='count_igt', inplace=True, ascending=False, ignore_index=True)
        # init dataframe before sorting
        collection_df['union'] = [set() for i in range(len(rcpNames))]
        collection_df['union_len'] = 0
        collection_df.at[0,'union'] = collection_df.at[0,'rcp_ingredients']
        collection_df.at[0,'union_len'] = len(collection_df.at[0,'union'])
        # sort dataframe by union length
        for ix in range(1,len(rcpNames)):   
            for ix2 in range (ix,len(rcpNames)):
                coll = collection_df.at[ix2,'rcp_ingredients'].union(collection_df.at[ix-1,'union'])
                collection_df.at[ix2,'union']     = coll
                collection_df.at[ix2,'union_len'] = len(coll)
            sort_sub(collection_df,ix,len(rcpNames),'union_len')
            print (ix, collection_df.at[ix-1,'union_len'], collection_df.at[ix-1,'rcp_names'].get('recipeName'))
        return list(collection_df['rcp_names'])
    
    def graphToSVG (self, scale=1.0):
        """ 
        Create svg file for graph
        """
        def add_SVG_edge(id,sub,start_id,end_id,weight,start_x,start_y,end_x,end_y):
            edge_attr   = {'class':'edge', 'id':id}
            edge        = ET.SubElement(g0_node, 'g', attrib=edge_attr)
            title       = ET.SubElement(edge,'title')
            title.text  = f"{start_id}--{end_id}"
            pt_coor     = f"M{start_x},{start_y}L{end_x},{end_y}"
            if weight == 1:
                path_attr   = {'fill':'none', 'stroke': 'black', 'd':pt_coor}
            elif weight == 2: 
                path_attr   = {'fill':'none', 'stroke': 'black', 'stroke-width':'2', 'd':pt_coor}
            elif weight > 2: 
                path_attr   = {'fill':'none', 'stroke': 'red', 'stroke-width':'2', 'd':pt_coor}
            else: 
                path_attr   = {'fill':'none', 'stroke': 'black', 'd':pt_coor}
            path        = ET.SubElement(edge,'path',path_attr)
            
        def add_SVG_node(id,sub,occ,name,i_class,cx_fd,cy_fd,rx_fd,ry_fd,txt_x,txt_y):
            node_attr   = {'class':'node', 'id':id, 'data-sub':sub, 'style':'cursor: pointer;'}
            node        = ET.SubElement(g0_node, 'g', attrib=node_attr)
            title       = ET.SubElement(node, 'title')
            title.text  = f"#occ: {occ}"
            ellip_class = f"i-{i_class}"            
            ellip_attr  = {'class':ellip_class, 'cx':cx_fd, 'cy':cy_fd, 'rx':rx_fd, 'ry':ry_fd}
            ET.SubElement(node, 'ellipse', attrib=ellip_attr)
            text_attr   = {'x':txt_x, 'y':txt_y, 'style':f"text-anchor: middle; font-family: Arial Narrow; font-size: {font_size}px;"}
            text        = ET.SubElement(node, 'text', attrib=text_attr)
            text.text   = name
            
        font_size = self.fontsize * scale
        # svg header
        w  = self.viewbox.split()[2]
        h  = self.viewbox.split()[3]
        svg_out_attr = {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'version':'1.1', 'viewbox':self.viewbox, \
                        'preserveAspectRatio':'xMidYMid meet', 'zoomAndPan':'magnify', 'contentScriptType':'text/ecmascript', 'contentStyleType':'text/css', 'width':w, 'height':h}
        svg_out = ET.Element('svg', attrib=svg_out_attr)
        style = ET.SubElement(svg_out, 'style')
        style.text = \
            ' .i-alc   {fill: #7087ED; stroke: #7087ED; background-color: #7087ED}' +\
            ' .i-carb  {fill: #C8A98B; stroke: #C8A98B; background-color: #C8A98B}' +\
            ' .i-condi {fill: #D58680; stroke: #D58680; background-color: #D58680}' +\
            ' .i-egg   {fill: #70A287; stroke: #70A287; background-color: #70A287}' +\
            ' .i-etc   {fill: #9AA6BF; stroke: #9AA6BF; background-color: #9AA6BF}' +\
            ' .i-fat   {fill: #81CDD8; stroke: #81CDD8; background-color: #81CDD8}' +\
            ' .i-fish  {fill: #ffdab9; stroke: #ffdab9; background-color: #ffdab9}' +\
            ' .i-fruit {fill: #7FDD46; stroke: #7FDD46; background-color: #7FDD46}' +\
            ' .i-herb  {fill: #95A84E; stroke: #95A84E; background-color: #95A84E}' +\
            ' .i-meat  {fill: #EE5874; stroke: #EE5874; background-color: #EE5874}' +\
            ' .i-milk  {fill: #6EA2DC; stroke: #6EA2DC; background-color: #6EA2DC}' +\
            ' .i-nuts  {fill: #D09E44; stroke: #D09E44; background-color: #D09E44}' +\
            ' .i-onion {fill: #60C667; stroke: #60C667; background-color: #60C667}' +\
            ' .i-spice {fill: #FF7F50; stroke: #FF7F50; background-color: #FF7F50}' +\
            ' .i-sweet {fill: #CDE1A6; stroke: #CDE1A6; background-color: #CDE1A6}' +\
            ' .i-veg   {fill: #65DDB7; stroke: #65DDB7; background-color: #65DDB7}' 
            
        # svg graph
        g0_node_attr = {'id':'graph0', 'transform':self.transform}
        g0_node = ET.SubElement(svg_out,'g',attrib=g0_node_attr) 
        # traversing the pandas dataframe for edges
        #   id               edge id, coded by <start-id>--<end-id>, where start-id alphabetically < end-id
        #   sub
        #   start_id         id of start node
        #   end_id           id of end node
        #   weight
        #   start_x_fd       x coordinate for start point, fd stands for force-directed layout
        #   start_y_fd       y coordinate for start point, fd stands for force-directed layout
        #   end_x_fd         x coordinate for end point, fd stands for force-directed layout
        #   end_y_fd         y coordinate for end point, fd stands for force-directed layout
        #   start_x_node     x coordinate for start at node center
        #   start_y_node     y coordinate for start at node center
        #   end_x_node       x coordinate for end at node center
        #   end_y_node       y coordinate for end at node center
        edges_frame = self.eds
        [add_SVG_edge(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]) for row \
                in zip(edges_frame.index, edges_frame['sub'], edges_frame['start_id'], edges_frame['end_id'], edges_frame['weight'], \
                edges_frame['start_x_fd'], edges_frame['start_y_fd'], edges_frame['end_x_fd'], edges_frame['end_y_fd'])]
        # traversing the pandas dataframe for nodes
        nodes_frame = self.nds
        [add_SVG_node(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]) for row \
                in zip(nodes_frame.index, nodes_frame['sub'], nodes_frame['occ'], nodes_frame['name'], nodes_frame['class'], \
                nodes_frame['cx_fd'], nodes_frame['cy_fd'], nodes_frame['rx_fd'], nodes_frame['ry_fd'], nodes_frame['txt_x'], nodes_frame['txt_y'] )]
        # write created svg to file
        tree = ET.ElementTree(svg_out)
        ET.indent(tree)
        outfile = f"{os.path.join(self.working_dir,self.exp_name)}.svg"
        tree.write(outfile)              
        return nodes_frame

    def nodesByOcc(self, incl_lower=None, excl_upper=None, fn=None, cls=None, scale=1.0):
        """ 
        Create svg file with nodes meeting occurrence constraint
        """
        def add_SVG_node(id,sub,occ,name,i_class,cx_fd,cy_fd,rx_fd,ry_fd,txt_x,txt_y):
            node_attr   = {'class':'node', 'id':id, 'data-sub':sub, 'style':'cursor: pointer;'}
            node        = ET.SubElement(g0_node, 'g', attrib=node_attr)
            title       = ET.SubElement(node, 'title')
            title.text  = f"#occ: {occ}"
            if cls != None:
                ellip_class = cls
            else:
                ellip_class = f"i-{i_class}"            
            ellip_attr  = {'class':ellip_class, 'cx':cx_fd, 'cy':cy_fd, 'rx':rx_fd, 'ry':ry_fd}
            ET.SubElement(node, 'ellipse', attrib=ellip_attr)
            text_attr   = {'x':txt_x, 'y':txt_y, 'style':f"text-anchor: middle; font-family: Arial Narrow; font-size: {font_size}px;"}
            text        = ET.SubElement(node, 'text', attrib=text_attr)
            text.text   = name
        
        font_size = self.fontsize * scale
        # svg header
        w  = self.viewbox.split()[2]
        h  = self.viewbox.split()[3]
        svg_out_attr = {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'version':'1.1', 'viewbox':self.viewbox, \
                        'preserveAspectRatio':'xMidYMid meet', 'zoomAndPan':'magnify', 'contentScriptType':'text/ecmascript', 'contentStyleType':'text/css', 'width':w, 'height':h}
        svg_out = ET.Element('svg', attrib=svg_out_attr)
        style = ET.SubElement(svg_out, 'style')
        style.text = \
            ' .i-alc   {fill: #7087ED; stroke: #7087ED; background-color: #7087ED}' +\
            ' .i-carb  {fill: #C8A98B; stroke: #C8A98B; background-color: #C8A98B}' +\
            ' .i-condi {fill: #D58680; stroke: #D58680; background-color: #D58680}' +\
            ' .i-egg   {fill: #70A287; stroke: #70A287; background-color: #70A287}' +\
            ' .i-etc   {fill: #9AA6BF; stroke: #9AA6BF; background-color: #9AA6BF}' +\
            ' .i-fat   {fill: #81CDD8; stroke: #81CDD8; background-color: #81CDD8}' +\
            ' .i-fish  {fill: #ffdab9; stroke: #ffdab9; background-color: #ffdab9}' +\
            ' .i-fruit {fill: #7FDD46; stroke: #7FDD46; background-color: #7FDD46}' +\
            ' .i-herb  {fill: #95A84E; stroke: #95A84E; background-color: #95A84E}' +\
            ' .i-meat  {fill: #EE5874; stroke: #EE5874; background-color: #EE5874}' +\
            ' .i-milk  {fill: #6EA2DC; stroke: #6EA2DC; background-color: #6EA2DC}' +\
            ' .i-nuts  {fill: #D09E44; stroke: #D09E44; background-color: #D09E44}' +\
            ' .i-onion {fill: #60C667; stroke: #60C667; background-color: #60C667}' +\
            ' .i-spice {fill: #FF7F50; stroke: #FF7F50; background-color: #FF7F50}' +\
            ' .i-sweet {fill: #CDE1A6; stroke: #CDE1A6; background-color: #CDE1A6}' +\
            ' .i-veg   {fill: #65DDB7; stroke: #65DDB7; background-color: #65DDB7}' +\
            ' .occ_1   {fill: #E96F49; stroke: #E96F49; background-color: #E96F49}' +\
            ' .occ_2   {fill: #BEDF1B; stroke: #BEDF1B; background-color: #BEDF1B}' +\
            ' .occ_3   {fill: #1BDF32; stroke: #1BDF32; background-color: #1BDF32}' +\
            ' .occ_4   {fill: #1BD6DF; stroke: #1BD6DF; background-color: #1BD6DF}' +\
            ' .occ_5   {fill: #7D7DEF; stroke: #7D7DEF; background-color: #7D7DEF}' 
        # svg graph
        g0_node_attr = {'id':'graph0', 'transform':self.transform}
        g0_node = ET.SubElement(svg_out,'g',attrib=g0_node_attr) 
        # create pandas dataframe with nodes meeting the given occurrence constraint
        nodes_frame = self.nds.loc[(self.nds['occ'] >= incl_lower) & (self.nds['occ'] < excl_upper)]
        # loop comprehension for traversing the pandas dataframe
        [add_SVG_node(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]) for row \
                in zip(nodes_frame.index, nodes_frame['sub'], nodes_frame['occ'], nodes_frame['name'], nodes_frame['class'], \
                nodes_frame['cx_fd'], nodes_frame['cy_fd'], nodes_frame['rx_fd'], nodes_frame['ry_fd'], nodes_frame['txt_x'], nodes_frame['txt_y'] )]
        # write created svg to file
        tree = ET.ElementTree(svg_out)
        ET.indent(tree)
        file = f"{self.exp_name} {fn}.svg"
        p = Path(self.working_dir)
        outfile = p / file
        tree.write(outfile)              
        return
    
    def graphToSVGgrey (self, scale=1.0):
        """ 
        Create svg file for graph
        """
            
        def add_SVG_node(id,sub,occ,name,i_class,cx_fd,cy_fd,rx_fd,ry_fd,txt_x,txt_y):
            node_attr   = {'class':'node', 'id':id, 'data-sub':sub, 'style':'cursor: pointer;'}
            node        = ET.SubElement(g0_node, 'g', attrib=node_attr)
            title       = ET.SubElement(node, 'title')
            title.text  = f"#occ: {occ}"
            ellip_class = f"i-{i_class}"            
            ellip_attr  = {'class':'i-grey', 'cx':cx_fd, 'cy':cy_fd, 'rx':rx_fd, 'ry':ry_fd}
            ET.SubElement(node, 'ellipse', attrib=ellip_attr)
            #text_attr   = {'x':txt_x, 'y':txt_y, 'style':f"text-anchor: middle; font-family: Arial Narrow; font-size: {font_size}px;"}
            #text        = ET.SubElement(node, 'text', attrib=text_attr)
            #text.text   = name
            
        font_size = self.fontsize * scale
        # svg header
        w  = self.viewbox.split()[2]
        h  = self.viewbox.split()[3]
        svg_out_attr = {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'version':'1.1', 'viewbox':self.viewbox, \
                        'preserveAspectRatio':'xMidYMid meet', 'zoomAndPan':'magnify', 'contentScriptType':'text/ecmascript', 'contentStyleType':'text/css', 'width':w, 'height':h}
        svg_out = ET.Element('svg', attrib=svg_out_attr)
        style = ET.SubElement(svg_out, 'style')
        style.text = \
            ' .i-alc   {fill: #7087ED; stroke: #7087ED; background-color: #7087ED}' +\
            ' .i-carb  {fill: #C8A98B; stroke: #C8A98B; background-color: #C8A98B}' +\
            ' .i-condi {fill: #D58680; stroke: #D58680; background-color: #D58680}' +\
            ' .i-egg   {fill: #70A287; stroke: #70A287; background-color: #70A287}' +\
            ' .i-etc   {fill: #9AA6BF; stroke: #9AA6BF; background-color: #9AA6BF}' +\
            ' .i-fat   {fill: #81CDD8; stroke: #81CDD8; background-color: #81CDD8}' +\
            ' .i-fish  {fill: #ffdab9; stroke: #ffdab9; background-color: #ffdab9}' +\
            ' .i-fruit {fill: #7FDD46; stroke: #7FDD46; background-color: #7FDD46}' +\
            ' .i-herb  {fill: #95A84E; stroke: #95A84E; background-color: #95A84E}' +\
            ' .i-meat  {fill: #EE5874; stroke: #EE5874; background-color: #EE5874}' +\
            ' .i-milk  {fill: #6EA2DC; stroke: #6EA2DC; background-color: #6EA2DC}' +\
            ' .i-nuts  {fill: #D09E44; stroke: #D09E44; background-color: #D09E44}' +\
            ' .i-onion {fill: #60C667; stroke: #60C667; background-color: #60C667}' +\
            ' .i-spice {fill: #FF7F50; stroke: #FF7F50; background-color: #FF7F50}' +\
            ' .i-sweet {fill: #CDE1A6; stroke: #CDE1A6; background-color: #CDE1A6}' +\
            ' .i-veg   {fill: #65DDB7; stroke: #65DDB7; background-color: #65DDB7}' +\
            ' .i-grey  {fill: #E1E1E1; stroke: #E1E1E1; background-color: #E1E1E1}'
            
        # svg graph
        g0_node_attr = {'id':'graph0', 'transform':self.transform}
        g0_node = ET.SubElement(svg_out,'g',attrib=g0_node_attr) 
        
        # traversing the pandas dataframe for nodes
        nodes_frame = self.nds
        [add_SVG_node(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]) for row \
                in zip(nodes_frame.index, nodes_frame['sub'], nodes_frame['occ'], nodes_frame['name'], nodes_frame['class'], \
                nodes_frame['cx_fd'], nodes_frame['cy_fd'], nodes_frame['rx_fd'], nodes_frame['ry_fd'], nodes_frame['txt_x'], nodes_frame['txt_y'] )]
        # write created svg to file
        tree = ET.ElementTree(svg_out)
        ET.indent(tree)
        outfile = f"{os.path.join(self.working_dir,self.exp_name)} grey.svg"
        tree.write(outfile)              
        return nodes_frame    

    def checkColl(self, key_ref):
        """
        some plausibility checks
        1 key ingredient occurence
        """
        # key ingredient occurence
        for fn_rcp in self.in_files:
            with open(fn_rcp, 'r', encoding='utf-8') as f:
                rcp_in = ET.parse(f)
                rcp_root = rcp_in.getroot()
                rcp_name = rcp_root.find('fr:recipeName', self.ns).text
                key_elements = []
                key_elements = rcp_root.findall(f".//ns0:igdtName[@ref='{key_ref}']",self.ns)
                if len(key_elements) == 0:
                    print (f"0    key ingredients for {rcp_name}")  
                elif len(key_elements) >= 2:
                    print (f"=> 2 key ingredients for {rcp_name}")


#### Helper functions

index = dict()
noRefIgts = []
    
# find longest matching ID for given ingredient name
def getIgtID (given, index):
    match = 0
    xxid = None
    for k,v in index.items():
        if k in given.lower():
            if len(k) > match:
                match = len(k)
                xxid = v
    return xxid

# write ingredient ID into recipe
def write2XML(rcp,ns,igt,id):
    el = rcp.findall(f'.//fr:igdtName[.="{igt}"]', ns)
    for x in el:
        x.set('ref',id)
        print
    return el

# read ingredients catalogue and create ingredients index
def createIgdtIndex (igdtCat):
    global index, noRefIgts
    with open(igdtCat, encoding='utf-8') as file:
        cat            = json.load(file)
        catIngredients = cat.get('ingredients')
        #catClasses     = cat.get('classes')
        noRefIgts      = cat.get('noRefIgts')
        index = dict()
        for igt in catIngredients.items():
            x = dict()
            k = igt[0]
            x = {k:k}
            index.update(x)
            y = dict()
            for syn in igt[1].get('synonyms'):
                y = {syn:k}
                index.update(y)
        return

# create refs, write them into recipe, and return results list
def writeRefs2rcp (loc,rcpName,ns):
    global index, noRefIgts
    fp = os.path.join(loc,rcpName)
    print (fp)
    with open(fp, 'r', encoding='utf-8') as f:
        rcp_in = ET.parse(f)
        rcp_root = rcp_in.getroot()
    allGiven = [entry.text.replace('"','') for entry in rcp_root.findall('.//fr:igdtName', ns)]
    suc = 0
    noSuc = []
    for ig in allGiven:
        match = getIgtID(ig, index)
        if match == None:
            noSuc.append(ig)
        else:
            suc += 1
            write2XML(rcp_root,ns,ig,match) 
    for xx in noSuc:
        for x in noRefIgts:
            if x in xx:
                suc += 1
    tree = ET.ElementTree(rcp_root)
    ET.indent(tree)
    tree.write(fp)
    return {'total':len(allGiven), 'success':suc, 'fail':noSuc, 'recipe name':rcpName}

#### fruschtiqueCCapi functions for creating references to ingredients catalogue

def createRefs4Recipe(loc=None,rcpName=None,igdtCat=None):
    global index, noRefIgts
    createIgdtIndex(igdtCat)
    ns = {'fr': 'http://fruschtique.de/ns/recipe'}
    return 

def createRefs4Coll(loc=None,igdtCat=None,recurse=None):
    # loop over recipes in loc directory
    # call to createRefs4Recipe per recipe
    # write modified recipes back to loc directory
    global index, noRefIgts
    createIgdtIndex(igdtCat)
    ns = {'fr': 'http://fruschtique.de/ns/recipe'}
    results = []
    if recurse == 'yes':
        for path, dirs, files in os.walk(loc):
            for rcp in files:
                if not(rcp[0:1].isnumeric()):
                    loc = Path(path)
                    #print (loc / rcp)
                    result = writeRefs2rcp (loc,rcp,ns)
                    results.append (result)
    else:
        for rcp in os.listdir(loc):
            result = writeRefs2rcp (loc,rcp,ns)
            results.append (result)
    return results

#### fruschtiqueCCapi scraper functions 

def scrapeCK (loc=None, url=None, extended_name=None, synList=None):

    # when reading from file:
    #with open(url, 'r') as f:
    #    root = BeautifulSoup(f, 'html.parser')

    # when reading from web
    response = requests.get(url)
    if response.status_code == 200: 
        root = BeautifulSoup(response.text, 'html.parser')
    else:
        return -1
    
    name = extended_name 
    instruct = root.select("small+div.ds-box")[0].get_text(separator = '\n',strip=True)
    # find ingredient tables
    hidden = root.find('div', {'amp-access':'rolesMap.ROLE_ENTITLEMENT_PLUS_RECIPES'})
    if hidden == None:
        igdt_tables = root.select('.ingredients')
    else:
        igdt_tables = root.select('div[amp-access="rolesMap.ROLE_ENTITLEMENT_PLUS_RECIPES"] > .ingredients')

    igt_list_text = ''
    for idx in range(0,len(igdt_tables)):
        igt_list_text += igdt_tables[idx].get_text()
    #print (f"Found {len(igdt_tables)} ingredient tables.")
    for syn in synList:
        if (syn in name.lower()) or (syn in igt_list_text.lower()) or (syn in instruct.lower()):
            break
        else:
            return 0
    _id  = f'ck-{uuid.uuid4()}'
    
    fr = 'http://fruschtique.de/ns/recipe'
    ET.register_namespace('fr', fr)
    xsi = 'http://www.w3.org/2001/XMLSchema-instance'
    recipe = ET.Element('fr:recipe', attrib={'xmlns:fr' : fr, 'xmlns:xsi': xsi, 'xsi:schemaLocation': fr + ' file:///c:/Users/nlutt/Documents/Websites/tools/recipe.xsd', 'rcpID': _id})
    meta = ET.SubElement(recipe, 'fr:meta')
    ET.SubElement(meta, 'fr:book').text = ''
    ET.SubElement(meta, 'fr:chapter').text = ''
    ET.SubElement(recipe, 'fr:recipeName').text = extended_name
    ET.SubElement(recipe, 'fr:recipeKeywords')
    ET.SubElement(recipe, 'fr:recipeIntro')
    recipe_ingredients = ET.SubElement(recipe, 'fr:recipeIngredients')
    igdt_list = ET.SubElement(recipe_ingredients, 'fr:igdtList')
    ET.SubElement(igdt_list, 'fr:igdtListName')
    for idx in range(0, len(igdt_tables)):
        #print (f" table {idx}")
        igt_list_rows = igdt_tables[idx].select('tbody tr')
        for i in range(0, len(igt_list_rows)):
            #print (f" row {i}")
            igdt_list_line = ET.SubElement(igdt_list, 'fr:igdtListLine')
            x = igt_list_rows[i].select('td')[0].get_text().replace('"','')
            xx = " ".join(x.split())
            ET.SubElement(igdt_list_line, 'fr:igdtQuantity').text = xx
            y = igt_list_rows[i].select('td')[1].get_text().replace('"','')
            yy = " ".join(y.split())
            #print (yy)
            ET.SubElement(igdt_list_line, 'fr:igdtName', attrib={'ref':''}).text = yy

    instructions = ET.SubElement(recipe, 'fr:recipeInstructions')
    instruction = ET.SubElement (instructions,'fr:instruction')
    ET.SubElement(instruction,'fr:instrStepName')
    ET.SubElement(instruction,'fr:instrStepText').text = instruct
    ET.SubElement(recipe, 'fr:recipeSideDish')
    ET.SubElement(recipe, 'fr:recipeOrigin')
    ET.SubElement(recipe, 'fr:recipeSeeAlso')
    ET.SubElement(recipe, 'fr:recipeLicense')
    xml_rcp = ET.ElementTree(recipe)
    return xml_rcp

def parse_search_result_page(url=None):
    response = requests.get(url)
    body = response.text
    xx = response.status_code
    #print (xx)
    if xx != 200:
        return -1
    root = BeautifulSoup(body, 'html.parser')
    rcpList = []
    nameList = []
    for el in root.select('.recipe-list>.ds-recipe-card'):
        rcp_name = el.get('data-vars-recipe-title').replace('"','').replace('/','').replace('  ',' ').replace(' - ','-')
        #print (rcp_name)
        x_url = el.find('a').get('href')
        rcp_url = x_url.split('#')[0]
        #print (rcp_url)
        if rcp_name is not None:
            rcpList.append((rcp_name,rcp_url))
            nameList.append (rcp_name)
    return rcpList, nameList

def scrapeCKbyKey(loc=None, culinaryKey=None, igdtCat=None):
    """
    """
    # create complete recipe list
    totalRcpList = []
    ctrList = []
    i1 = 0
    while True:
        url = f'https://www.chefkoch.de/rs/s{i1}/{culinaryKey}/Rezepte.html'
        xx = parse_search_result_page(url)
        if xx != -1:
            totalRcpList.extend(xx[0])
            ctrList.extend(xx[1])
            i1 += 1
        else:
            break
    print ('CK search results: ', len(totalRcpList))  

    ctr = dict(Counter(ctrList))
    #print (ctr)

    # provide list of synonyms for culinary key
    with open('C:/Users/nlutt/myPyPro/second/data/igt_cat.json', encoding='utf-8') as file:
        cat            = json.load(file)
        catIngredients = cat.get('ingredients')
    _id = ''
    for k,v in catIngredients.items():
        #print (k)
        if v.get('i-name') == culinaryKey:
            _id = k
            break
    if _id == '':
        print (f"{culinaryKey} not in ingredients catalogue!")
        return
            
    synList = [catIngredients.get(_id).get('i-name').lower()]
    for syn in catIngredients.get(_id).get('synonyms'):
        synList.append(syn)
    #print (synList)
    # scrape CK recipes and write to XML files
    i = 0
    for rcp in totalRcpList:
        rcpName = rcp[0].replace('"','').replace('/','').replace('  ',' ').replace(' - ','-')
        url = rcp[1]
        name_counter = ctr.get(rcpName)
        if name_counter > 1:
            extension = str(name_counter).zfill(3)
            extended_fn = f"{rcpName} {extension}.xml"
            extended_rcpName = f"{rcpName} {extension}"
            ctr.update({rcpName:name_counter - 1})
        else:
            extended_fn = f"{rcpName}.xml" 
            extended_rcpName = rcpName
        xml_rcp = scrapeCK (loc,url,extended_rcpName,synList)
        if xml_rcp == 0:
            print (rcpName)
        elif xml_rcp == -1: 
            print ('Done!')
            break
        else: 
            i += 1
            print (i)  
            file_path = f"{os.path.join(loc,extended_fn)}"
            xml_rcp.write(file_path, xml_declaration=True, encoding='utf-8', method='xml') 
    print ('Done!')
    return

#### fruschtiqueCCapi functions for sample spaces

def makeSampleSpace(sourceDir=None, graphlabDir=None, sampleSpaceName=None, cb=None, meta=None):
    """
    1 Create folder for new sample space
    2 Create XML-coded catalog of recipes in sourcedir
    3 create XML-coded descriptor for collection 
    """
    # new sample space
    p = Path(graphlabDir)
    newSpace = p / 'sampleSpaces' / sampleSpaceName  
    newSpace.mkdir(parents=True, exist_ok=True) 
    newGraphsDir = newSpace / 'graphs'
    newGraphsDir.mkdir(parents=True, exist_ok=True)   
    # catalogue of files in collection
    sourceFiles = [os.path.join(sourceDir,f) for f in os.listdir(sourceDir) if os.path.isfile(os.path.join(sourceDir, f))]
    collection = ET.Element('collection')
    for f in sourceFiles:
        x = urllib.parse.urljoin('file:', pathname2url(f))
        doc = ET.SubElement(collection,'doc',attrib={'href':x})
    cata = ET.ElementTree(collection)
    ET.indent(cata)
    cata.write(os.path.join(newSpace,'catalogue.xml'), xml_declaration=True, encoding='utf-8', method='xml')
    # create descriptor
    fe = 'http://fruschtique.de/ns/fe'
    ET.register_namespace('fe', fe)
    xsi = 'http://www.w3.org/2001/XMLSchema-instance' 
    experiment = ET.Element('fe:experiment', attrib={'xmlns:fe' : fe, 'xmlns:xsi': xsi, 'xsi:schemaLocation': fe + ' file:///c:/users/nlutt/documents/websites/graphlab/tools/experiment.xsd'})
    fullTitle = ET.SubElement(experiment,'fe:fullTitle')
    fullTitle.text = f"{sampleSpaceName}"
    cookbook = ET.SubElement(experiment,'fe:cookbook')
    cookbook.text = cb
    experimentPath = ET.SubElement(experiment,'fe:experimentPath')
    experimentPath.text = f'sampleSpaces/{sampleSpaceName}/'
    winExperimentPath = ET.SubElement(experiment,'fe:win-experimentPath')
    winExperimentPath.text = f"{os.path.join('sampleSpaces',sampleSpaceName)}\\"
    experimentName = ET.SubElement(experiment,'fe:experimentName')
    experimentName.text = f"{sampleSpaceName}"
    ET.SubElement(experiment,'fe:experimentDescription')
    useIngredientReplacements = ET.SubElement(experiment,'fe:useIngredientReplacements')
    useIngredientReplacements.text = 'no'
    descriptor = ET.ElementTree(experiment)
    ET.indent(descriptor)
    descriptor.write(os.path.join(graphlabDir,f'currentDescriptor {sampleSpaceName}.xml'), xml_declaration=True, encoding='utf-8', method='xml')
    return None
