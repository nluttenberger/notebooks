# The *fruschtique*&copy; API

## General Information
The *fruschtique*&copy; API supports the programmer to create ingredient graphs from culinary collections of cueML&copy;-encoded recipes. It has functions for
- scraping recipes (selected by a searchstring) from the chefkoch.de website and converting them to cueML format
- extracting several structural information from a culinary collection
- creating an ingredient graph from a colinary collection
- preparing a SVG-based preview of an ingredient graph
- storing the graph in different formats, among them CSV, GEXF, and DOT 
- comparing two subcollections that have been compiled into a single culinary collection  

The *fruschtique*&copy; CC API relies on a JSON-encoded ingredients catalogue providing a normalized name and related synonymes for ingredient names found in recipes. The ingredients catalogue also assigns to each ingredients one of 16 different ingredient classes.  

Find the cueML&copy; XSD Schema and the actual ingredients catalogue in this repository. Find a sample cueML&copy;-encoded recipe in this repo, too.  

For a description what actually is meant by the term "culinary collection", see [this doc]().  

Sample ingredient graphs can be seen [here](https://graphlab.fruschtique.de).  

The *fruschtique*&copy; CC API is part of the *fruschtique*&copy; suite of Python- and XSLT-based tools, data formats, data repositories, and websites.

## Getting started
Start programming your *fruschtique*&copy; CC API-based application by installing the *fruschtique*&copy; CC API as follows:  

`pip install fruschtique`  

and importing it into your Python code:  

`import fruschtique as fr`

## Reading this doc
- The descriptions of the *fruschtique*&copy; CC API functions are grouped by keywords indicating their purpose.  
- `[exp name]` stands for the current experiment name. It is given in the descriptor file.
#####  &nbsp;

## The `CulinaryCollection` class and its methods
The CulinaryCollection class provides a number of methods to the programmer that let him/her construct ingredient graphs from culinary collections, and analyse these graphs.
#####  &nbsp;
---
### Init method
---
#### `CulinaryCollection(graphLab=None, descriptor=None, igdtCat=None, working=None)`  
- *description:*  
Reads the cueML/XML-encoded descriptor for the collection/experiment from the local disc, reads cueML/json-encoded ingredients catalog, creates json-encoded file `coll_data.json` in the working directory holding the collection data   
- *params:*  
`graphLab:dirpath` (absolute path to graphLab top-level directory)  
`descriptor:filename` (XML-encoded descriptor for graph experiment)  
`igdtCat:fullpath` (absolute path to JSON-encoded ingredients catalogue file)   
`working:dirpath` (absolute path to notebook's working directory; often the 'data' directory)  
- *returns:*  
nothing
- *side-effects:*  
produces json-encoded file `coll_data.json` in the given working directory with subcollection and recipe lists  
- *errors*  
    - missing ref
    - null ref
- *print:*  
collection name, #subcollections, recipe author names, #recipes total, #recipes subcollection-wise, #distinct ingredients in collection, #ingredients in ingredients catalogue  
- *example:*   
`myColl = fr:CulinaryCollection('c:\users\xuser\graphLab\', 'descriptor.xml', 'c:\users\xuser\graphLab\igdt_cat.json', 'c:\users\xuser\pyProjects\graphs\data\')`  
&nbsp;  
`print(myColl)`
#####  &nbsp;  

---
### Collection-related methods
---

#### `checkColl(keyIngredientRef)`  
- *description:*  
Checks collection for some plausibility assertions (further to be added).  
See parameter descriptions.
- *params:*  
`keyIngredientRef:string` (The collection's key ingredient should have an occurrence value of 100%)
- *returns:*  
None
- *side-effects:*  
None 
- *print:*  
n/a  
- *example:*  
`myColl.checkColl('grünkohl')`
#####  &nbsp; 


#### `listSubcolls()`
- *description:*  
  General information on subcollections contained in collection  
- *params:*  
no params  
- *returns:*  
`list` of `dict`, keys: `letter`, `name`, `author`, `rcpCount`, `igtCount`
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`info = myColl.listSubcolls()`
#####  &nbsp;


#### `listRecipes(subColl=None)`  
- *description:*  
return list of recipes total or subcollection-wise  
- *params:*  
`subcoll_letter:string` (optional; default: return complete list)    
- *returns:*  
`list` of `dict`, keys: `recipeName`, `ingredients`
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`myArcpList = myColl.listRecipesList('A')`
#####  &nbsp;


#### `listIngredients(subcoll=None)`  
- *description:*  
distinct ingredients used in collection: total, subcollection-wise
- *params:*  
`[subcoll_letter:string]` (optional; default: complete list)
- *returns:*  
`list(references to ingredients catalogue)`
- *side-effects:*  
none
- *print:*  
n/a
- *example:*  
`ingredients_list_for_B = myColl.listIngredients('B')`  
#####  &nbsp;


#### `listIngredientsCatalog(i-class or [keys for ingredient entries in catalogue], default=None)`  
- *description:*  
returns complete catalogue, list of ingredient references for given i-class, or full catalogue entries for list of references, default=None  
- *params:*  
one of `references_to_ingrediensts_catalogue:list`,  `i-class:string`; if `None` : return complete ingredients catalogue 
- *returns:*  
list(ingredients catalogue entries)  
- *side-effects:*  
none  
- *print:*  
n/a
- *examples:*  
`myList = myColl.listIngredientsCatalog(['ei','brot'])`  
`myList = myColl.listIngredientsCatalog('veg')`  
#####  &nbsp; 


#### `cosine_sim()`  
- *description:*  
   determines cosine similarity between subcollections in total and between ingredient vectors class-wise  
- *params:*  
   none  
- *returns:*  
   None, if current collection has no subcollections, else dict with entries for 'total' and ingredient classes
- *side-effects:*  
   none  
- *print:*  
   n/a  
- *example:*  
   `myColl.cosine_sim()`
#####  &nbsp; 


#### `entropy()`  
- *description:*  
determine entropy of subcollections  
- *params:*  
none  
- *returns:*  
if collection has no subcollections: `entropy:float` for collection, else  
`dict` with keys `entropy_A, entropy_B`  
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`myColl.entropy()`
#####  &nbsp; 


---
### Graph-related methods
---


#### `toGraph(subcoll=None or subcolllist=None)`  
- *description:*  
converts (sub)collection(s) to ingredient graph  
- *params:*  
`subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)
- *returns:*  
Networkx Graph with node attributes `i-name`, `i-class`, `occ`, `sub`, and edge attributes `id`, `weight`, `sub`
- *side-effects:*  
none
- *print:*  
summary information on resulting graph and its nodes and edges
- *example:*  
`G = myColl.toGraph(['A', 'B'])`
#####  &nbsp; 

     
#### `nodeSets(graph=None, subcoll=None or subcolllist=None)`     
- *description:*  
computes node sets: pure node set for single subcollection or intersection set for two subcollections 
- *params:*  
`graph:graph` (Networkx graph), `subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)  
- *returns:*  
`list` of nodes with node attributes    
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`nodesets = myColl.nodeSets(G, ['A', 'B'])`   
#####  &nbsp; 

     
#### `edgeSets(graph=None, subcoll=None or subcolllist=None)`   
- *description:*  
compute edge sets: subcollection-pure, subcollection-to-intersection, intersection-pure  
- *params:*  
`graph` (Networkx graph), `subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)
- *returns:*  
`dict` with keys `A_edges, AAB_edges, B_edges, BAB_edges, AB_edges` 
- *side-effects:*  
none
- *print:*  
n/a
- *example:*
`edgesets = myColl.edgeSets(G, 'A')`   
#####  &nbsp; 

     
#### `Krack(graph=None, subcoll=None or reflist=None)`  
- *description:*  
Computes Krackhardt's Index (KI) subcollection- or ingredient-wise with KI = (EL-IL)/(EL+IL) with EL = external links and IL = internal links.
The subcollection-wise application of `Krack()` is applicable only if the collection has two subcollections. 
As defined here, `Krack()` measures the interconnection between a collection's "pure node set" and the intersection node set.  
  - internal links: relations in the "pure edges set", i.e. relations that connect ingredient nodes in the collection's "pure node set"  
  - external links: relations in the "mixed edges set"  
- *params:*  
`graph` (Networkx graph), `subcoll:string` (single letter denoting a subcollection) or `reflist:list` (list of references to ingredients catalogue)  
- *returns:*  
`dict` with keys  
- *side-effects:*  
none  
- *print:*  
n/a  
- *examples:*  
`index_subcoll = myColl.Krack(G, 'A')`  
`index_some = myColl.Krack(G, ['butter', 'ei'])`  
#####  &nbsp; 


---  
### Graph export methods
---


#### `graphToDot(graph=None)`  
- *description:*  
create dot-file for graph creation by graphviz 
- *params:*  
`graph` (Networkx graph)   
- *returns:*  
nothing  
- *side-effects:*  
DOT file is written to working directory   
- *print:*  
n/a  
- *example:*  
`myColl.toDot(G)`
#####  &nbsp; 

   
#### `graphToGEXF(graph=None)`  
- *description:*  
output in gexf format to be used by Gephi
- *params:*  
`graph` (Networkx graph)    
- *returns:*  
nothing  
- *side-effects:*  
GEXF file is written to working directory    
- *print:*  
n/a  
- *example:*  
`myColl.toGEXF(G,'myGEXFgraph')`
#####  &nbsp; 

     
#### `graphToCSV(graph=None)`    
- *description:*  
creates two CSV-encoded files, one for nodes and one for edges   
- *params:*  
`graph` (Networkx graph)    
- *returns:*  
nothing  
- *side-effects:*  
Two CSV files are written to working directory, one for nodes, the other for edges  
- *print:*  
n/a  
- *example:*  
`myColl.toCSV(G)`
#####  &nbsp; 


---  
### SVG-related methods
---

#### `SVGMakerInit(graph=None)`  
- *description:*  
Initializes the SVG Maker component of the Culinary Collection object and provides data for following SVG-related function calls. This function must be called before all other SVG-related functions.
- *params:*  
`graph:graph` (Networkx graph)  
- *returns:*  
None
- *side-effects:*  
Creates file `[exp_name] poor graph.svg` in working directory 
- *print:*  
n/a  
- *example:*  
`myColl.SVGMakerInit()`
#####  &nbsp; 


#### `graphToSVG(scale=1.0)`  
- *description:*  
Creates SVG file for graph.
- *params:*   
`scale:float` (scaling factor for font size in SVG graph)
- *returns:*  
bla
- *side-effects:*  
Creates file `[exp_name].svg` in working directory 
- *print:*  
n/a  
- *example:*  
`myColl.graphToSVG(1.1)`
#####  &nbsp; 


#### `previewHTML(scale=1.0)`     
- *description:*  
Embeds SVG graph in HTML/CSS/JS wrapper.  
In case the collection has subcollections, HTML buttons are created to select either subcollection nodes, or their intersection, or the full graph node set.
- *params:*    
`scale:float` (scaling factor for font size in SVG graph)  
- *returns:*  
nothing  
- *side-effects:*  
Creates file `[exp_name] preview.html` in working directory  
- *print:*  
n/a  
- *example:*  
`myColl.previewHTML(G,1.1)`
#####  &nbsp; 


#### `createSVGSequence(rcpList=None,targetDir=None,scale=1.0)`  
- *description:*  
Creates a single SVG file per recipe in the recipe list. Coordinates for nodes and edges are taken from the complete SVG ingredient graph. 
- *params:*  
`rcpList:list` (list of recipe names)
`targetDir: dir path` (sub directory of the working dir, where to store the created SVG graphs)
`scale:float` (scaling factor for font size in SVG graphs)
- *returns:*  
None
- *side-effects:*  
Creates subdirectory in the working dir 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 


#### `sortByContrib2IG()`  
- *description:*  
bla
- *params:*  
bla
- *returns:*  
`sequence:list` (ordered list of recipe names)
- *side-effects:*  
bla 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 

---  
## Functions for scraping recipes and normalizing their ingredient names


#### `scrapeCKbyKey(culinaryKey=None, targetDir=None)`  
- *description:*  
Scrapes search results for culinary key from the Chefkoch website (chefkoch.de), converts them cueML-encoding and stores them in directory
- *params:*  
`culinaryKey:string` (input for Chefkoch search entry field)  
`targetDir:dirpath` (location for storing scraped recipes)
- *returns:*  
nothing
- *side-effects:*  
creates directory given by `culinaryKey` in location given by `dirpath` and stores scraped recipes in this directory; recipe files carry recipe names as filenames; recipe files are encoded in cueML; not contained: references to ingredients catalogue
- *print:*  
n/a  
- *example:*  
`fr:scrapeCKbyKey('schwarzwurzel', 'c:/users/xlutt/Documents/newColl/schwarzwurzelColl')`
#####  &nbsp; 


#### `createRefs4Recipe(loc=None, recipeName=None, igdtCat=None)`  
- *description:*  
creates ingrendients catalogue references for all ingredients in the given recipes 
- *params:*  
`loc:dirpath` (absolute path to recipe file directory)  
`recipeName:string` (name of recipe)  
`igdtCat:fullpath` (absolute path to JSON-encoded ingredients catalogue file)
- *returns:*  
`dict` with `'total':int, 'success':int, 'fail':list, 'recipeName':string`
- *side-effects:*  
stores updated cueML-encoded recipe file in the `loc` directory 
- *print:*  
n/a  
- *example:*  
`result = fr:createRefs4Recipe('C:/Users/xuser/Documents/newColl/recipes_xml/', 'Mung Dal mit Spinat.xml')`
#####  &nbsp;


#### `createRefs4Coll(loc=None, igdtCat=None)`  
- *description:*  
creates ingrendients catalogue references for all ingredients in the recipes of a collection
- *params:*  
`loc:dirpath` (location of collection)  
`igdtCat:fullpath` (absolute path to JSON-encoded ingredients catalogue file)
- *returns:*  
`dict` with `'total':int, 'success':int, 'fail':list, 'recipeName':string` 
- *side-effects:*  
stores updated cueML-encoded recipe files in the `loc` directory 
- *print:*  
n/a  
- *example:*  
`result = fr:createRefs4Collection('C:/Users/xuser/Documents/newColl/recipes_xml/')`
#####  &nbsp; 


#### `makeSampleSpace(sourceDir=None, graphlabDir=None, sampleSpaceName=None, meta=None)`  
- *description:*  
creates a fruschtique sample space from scraped recipes in the fruschtique graphlab directory 
- *params:*  
`sourceDir:dirpath` (absolute path to source directory holding scraped recipes in fruschtique XML format)  
`graphlabDir:dirpath` (absolute path to local fruschtique graphlab)  
`sampleSpaceName:string` (sample space name)  
`meta:filepath` (path to JSON-encoded file with meta information describing the collection to be created)
- *returns:*  
nothing
- *side-effects:*  
create fruschtique directory tree in target directory
create files: fruschtique descriptor file, fruschtique catalog file 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 

---  
## File formats


#### `coll_data`
- *description:*  
JSON-encoded file describing the collection
- *format:*  
`collection: {title, collections: {subcoll: {subcollName, author, [recipe names]}}, recipes: {recipeName: name, ingredients: [references to ingredients catalogue]}}`
#####  &nbsp; 


#### `ingredients catalogue`
- *description:*  
the ingredients catalogue in JSON format
- *format:*  
#####  &nbsp; 


#### `sample recipe file`
--- 
### MD template for functions
---


#### `function()`  
- *description:*  
bla
- *params:*  
bla
- *returns:*  
bla
- *side-effects:*  
bla 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 


---
```
graphlab
├───.idea
├───chatGPT
├───deprecated
├───dist
│   ├───2022-H1
│   ├───2022-Q1
│   ├───2022-Q2
│   ├───ckMangold
│   ├───ckMaronensuppe
│   ├───ckPensionsfrucht
│   ├───compareDev
│   ├───compareHD-YO
│   ├───css
│   ├───Flavour
│   ├───fruschtique
│   ├───g_demo4Theory
│   ├───HD-Fleisch
│   ├───HD-Gemüse
│   ├───HD-Suppen
│   ├───img
│   │   ├───blog
│   │   ├───icons
│   │   ├───logos
│   │   └───theory
│   ├───js
│   │   ├───.idea
│   │   └───vendor
│   ├───Kochbuch50
│   ├───Kochbuch60
│   ├───pdf
│   ├───svg
│   └───two_of_HD-Gemüse
├───doc
│   ├───fr Ausdruck
│   └───fr docs
│       ├───img
│       ├───material
│       └───sheets
├───etc
│   ├───Fotos ZKM Barabasi
│   └───JSNetworkX API Reference-Dateien
├───experiments
│   ├───all-betweenness_lt_500
│   │   ├───graphs
│   │   └───htmlFragments
│   ├───InsalataValtelina
│   │   ├───graphs
│   │   └───htmlFragments
│   └───vorspeisen
│       ├───graphs
│       └───htmlFragments
├───filters
├───lit
│   └───Teng Lin - Substitution
├───sampleSpaces
│   ├───2022-H1
│   │   └───graphs
│   ├───2022-Q1
│   │   └───graphs
│   ├───2022-Q2
│   │   └───graphs
│   ├───all-1
│   │   ├───graphs
│   │   ├───htmlFragments
│   │   └───tteesstt
│   ├───ckMangold
│   │   └───graphs
│   ├───ckMaronensuppe
│   │   └───graphs
│   ├───ckPensionsfrucht
│   │   └───graphs
│   ├───compareDev
│   │   └───graphs
│   ├───compareHD-YO
│   │   └───graphs
│   ├───demo4Theory
│   │   └───graphs
│   ├───Flavour
│   │   └───graphs
│   ├───forFour
│   ├───fruschtique
│   │   └───graphs
│   ├───GraphConstruct
│   │   └───graphs
│   ├───HD-Fleisch
│   │   └───graphs
│   ├───HD-Gemüse
│   │   └───graphs
│   ├───HD-Suppen
│   │   └───graphs
│   ├───InsalataValtellina
│   │   └───graphs
│   ├───k50
│   │   └───graphs
│   ├───k60
│   │   └───graphs
│   └───two_of_HD-Gemüse
│       └───graphs
├───src
│   ├───css
│   ├───doc
│   ├───img
│   └───js
├───stoer-wagner
├───temp
├───theory
└───tools

```