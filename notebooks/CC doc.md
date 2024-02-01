# The *fruschtique*&copy; API

## General Information
The *fruschtique*&copy; API supports the programmer to create ingredient graphs from culinary collections of cueML&copy;-encoded recipes. It has functions for
- scraping recipes (selected by a searchstring) from the chefkoch.de website and converting them to cueML format
- extracting several structural information from a culinary collection
- creating an ingredient graph from a colinary collection
- preparing a SVG-based preview of an ingredient graph
- storing the graph in different formats, among them CSV, GEXF, and DOT 
- comparing subcollections that have been compiled into a single culinary collection  

The *fruschtique*&copy; API relies on a JSON-encoded ingredients catalogue providing a normalized name and related synonymes for ingredient names found in recipes. The ingredients catalogue also assigns to each ingredients one of 16 different ingredient classes.  

Find the cueML&copy; XSD Schema and the actual ingredients catalogue in this repository. Find a sample cueML&copy;-encoded recipe in this repo, too.  

For a description what actually is meant by the term "culinary collection", see [this doc]().  

Sample ingredient graphs can be seen [here](https://graphlab.fruschtique.de).  

The *fruschtique*&copy; API is part of the *fruschtique*&copy; suite of Python and XSLT tools, data formats, data repositories, and websites.

## Getting started
Start programming your *fruschtique*&copy; API-based application by installing the *fruschtique*&copy; API as follows:  

`pip install fruschtique`  

and importing it into your Python code:  

`import fruschtique as fr`

## This doc
The descriptions of the *fruschtique* API functions are grouped by keywords indication their purpose.
#####  &nbsp;

## The `CulinaryCollection` class and its methods
The CulinaryCollection class provides a number of methods to the programmer that let him/her construct ingredient graphs from culinary collections, and analyse these graphs.
#####  &nbsp;

---
### Init
---
#### `CulinaryCollection(graphLab, descriptor, igdtCat, working)`  
- *description:*  
read cueML/XML-coded descriptor for collection from graphLab, read cueML/json-coded ingredients catalog, generate json-coded file holding collection data   
- *params:*  
`graphLab:dirpath` (absolute path to graphLab top-level directory)  
`descriptor:filename` (XML-encoded descriptor for graph experiment, located in graphLab top-level directory)  
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
### Collection-related
---


#### `infoSubcolls()`
- *description:*  
  General information on subcollections contained in collection  
- *params:*  
`xx` (absolute path to graphLab top-level directory)  
- *returns:*  
`dict` with keys `#subcollections, subcollection names, recipe author names, #recipes subcollection-wise, #distinct ingredients in subcollections`
- *side-effects:*  
none  
- *print:*  
collection name, #subcollections, recipe author names, #recipes total, #recipes subcollection-wise, #distinct ingredients in collection, #ingredients in ingredients catalogue  
- *example:*  
`info = myColl.infoSubcolls()`
#####  &nbsp;


### `recipesList(subColl=None)`  
- *description:*  
return list of recipes total or subcollection-wise  
- *params:*  
`subcoll_letter:string` (optional; default: return complete list)    
- *returns:*  
`list(recipe names)`
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`myArcpList = myColl.recipesList('A')`
#####  &nbsp;


### `ingredientsList(subcoll=None)`  
- *description:*  
distinct ingredients used: total, subcollection-wise
- *params:*  
`[subcoll_letter:string]` (optional; default: complete list)
- *returns:*  
`list(references to ingredients catalogue)`
- *side-effects:*  
none
- *print:*  
n/a
- *example:*  
`myBigtList = myColl.ingredientsList('B')`  
#####  &nbsp;


### `catalogList(i-class or [keys for ingredient entries in catalogue], default=None)`  
- *description:*  
returns complete catalogue, list of ingredient references for given i-class, or full catalogue entries for list of references, default=None  
- *params:*  
one of `references_to_ingrediensts_catalogue:list`,  `i-class:string`, default: None  
- *returns:*  
list(ingredients catalogue entries)  
- *side-effects:*  
none  
- *print:*  
n/a
- *examples:*  
`myList = myColl.catalogList(['ei','brot'])`  
`myList = myColl.catalogList('veg')`  
#####  &nbsp; 


### `cosine_sim()`  
- *description:*  
   determines cosine similarity between subcollections in total and ingredient vectors class-wise  
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


### `entropy()`  
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
### Graph-related
---


### `toGraph(subcoll=None or subcolllist=None)`  
- *description:*  
converts (sub)collection(s) to ingredient graph  
- *params:*  
`subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)
- *returns:*  
Networkx Graph with node attributes `i-name`, `i-class`, `occ`, `sub`, and edge attributes `id`, `weight`
- *side-effects:*  
none
- *print:*  
summary information on resulting graph nodes and edges
- *example:*  
`G = myColl.toGraph(['A', 'B'])`
#####  &nbsp; 

     
### `nodeSets(graph=None, subcoll=None or subcolllist=None)`     
- *description:*  
computes node sets: pure node set for single subcollection or intersection set for two subcollections 
- *params:*  
`graph:graph` (Networkx graph), `subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)  
- *returns:*  
list(nodes with node attributes)    
- *side-effects:*  
none  
- *print:*  
n/a  
- *example:*  
`nodesets = myColl.nodeSets(G, ['A', 'B'])`   
#####  &nbsp; 

     
### `edgeSets(graph=None, subcoll=None or subcolllist=None)`   
- *description:*  
compute edge sets: pure, mixed, intersection  
- *params:*  
`graph` (Networkx graph), `subcoll:string` or `[subcoll:string+]` (single letter denoting a subcollection or list thereof)
- *returns:*  
`dict` with keys `A_e_pure, A_e_mixed, B_e_pure, B_e_mixed, AB_e_intersect` 
- *side-effects:*  
none
- *print:*  
n/a
- *example:*
`edgesets = myColl.edgeSets(G, 'A')`   
#####  &nbsp; 

     
### `Krack(graph=None, subcoll=None or reflist=None)`  
- *description:*  
Computex Krackhardt's index (global, ingredient-wise) with KI = (EL-IL)/(EL+IL) with EL = external links and IL = internal links.  
As defined here, the Krackhardt index measures the connection between a collection's "pure node set" and the intersection node set.  
internal links: relations in the "pure edges set", i.e. relations that connect ingredient nodes in the collection's "pure node set"  
external links: relations in the "mixed edges set"  
`Krack()` is applicable only if collection has two subcollections
- *params:*  
`graph` (Networkx graph), `subcoll:string` (single letter denoting a subcollection) or `reflist:list` (list of references to ingredients catalogue)  
- *returns:*  
dict({ })  
- *side-effects:*  
none  
- *print:*  
n/a  
- *examples:*  
`index_subcoll = myColl.Krack(G, 'A')`  
`index_some = myColl.Krack(G, ['butter', 'ei'])`  
#####  &nbsp; 


---  
### Graph exports
---


### `toDot(graph=None, dirpath=None, filename=None)`  
- *description:*  
create dot-file for graph creation by graphviz
- *params:*  
`graph` (Networkx graph), `dirpath`, `filename` (for dot file)  
- *returns:*  
nothing  
- *side-effects:*  
dot file is written to given dirpath-filename   
- *print:*  
n/a  
- *example:*  
`myColl.toDot(G,'myWorkingDir','myDOTgraph')`
#####  &nbsp; 

   
### `toGEXF(graph=None, dirpath=None, filename=None)`  
- *description:*  
output in gexf format to be used by Gephi
- *params:*  
`graph` (Networkx graph), `dirpath`, `filename` (for gexf file)  
- *returns:*  
nothing  
- *side-effects:*  
gexf file is written to given dirpath-filename    
- *print:*  
n/a  
- *example:*  
`myColll.toGEXF(G,'myWorkingDir','myGEXFgraph')`
#####  &nbsp; 

     
### `toCSV(graph=None, dirpath=None, filename=None)`    
- *description:*  
creates CSV-encoded file with nodes and edges sections describing the graph  
- *params:*  
`graph` (Networkx graph), `dirpath`, `filename` (for CSV file)   
- *returns:*  
nothing  
- *side-effects:*  
CSV file is written to given dirpath-filename  
- *print:*  
n/a  
- *example:*  
`myColl.toCSV(G,'myWorkingDir','myCSVgraph')`
#####  &nbsp; 


---  
### SVG-related
---

     
### `previewSVG(graph=None, fontsize=1.0)`     
- *description:*  
embeds SVG-formated graph in HTML/CSS/JS wrapper, showing graph nodes only;  
in case the collection has subcollections, HTML buttons are created to switch on only subcollection nodes or their intersection
- *params:*  
`graph` (Networkx graph to be previewed), `scale:float` (scaling factor for font size in SVG graph, 1.0 < scale < 2.0, recommended: 1.0, default: 1.0)  
- *returns:*  
nothing  
- *side-effects:*  
`svgGraph-poor.svg`, `preview.html` and `dotdot.dot` files are written to given working directory  
- *print:*  
n/a  
- *example:*  
`previewSVG(G,1.1)`
#####  &nbsp; 


### `createSVGRecipeGraphs()`  
- *description:*  
Creates a single SVG file per recipe. Coordinates for nodes and edges are taken from the complete SVG ingredient graph. 
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
### Scraping and normalizing
---


### `scrapeCK(searchword=None, target=none)`  
- *description:*  
Scrapes search results from the Chefkoch website (chefkoch.de); this function should be used after `EmptyCollection` and before `createRefs4Collection`
- *params:*  
`searchword:string` (input for Chefkoch search entry field)  
`target:dirpath` (location for storing scraped recipes)
- *returns:*  
nothing
- *side-effects:*  
creates directory named by `searchword` in location given by `dirpath` and stores scraped recipes in this directory; recipe files carry recipe names as filenames; recipe files are encoded in cueML; not contained: references to ingredients catalogue
- *print:*  
n/a  
- *example:*  
`scrapeCK('schwarzwurzel', 'c:\users\nlutt\pyProjects\graphs\data\')`
#####  &nbsp; 


### `createRefs4Recipe(recipeName)`  
- *description:*  
creates references to the ingrendients catalogue for all ingredients listed in the recipe 
- *params:*  
`recipeName:string` (name of recipe)
- *returns:*  
`dict` with keys `'refsCreated', 'noRefIngredients'`, each having `list` values
- *side-effects:*  
stores resulting cueML-encoded recipe file in the working directory 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp;


### `createRefs4Collection(location)`  
- *description:*  
creates references to ingrendients catalogue for all ingredients listed in the recipe of a collection
- *params:*  
`location:dirpath` (location of collection)
- *returns:*  
`dict` with keys `'succRefs', 'noSuccRefs'` with list values
- *side-effects:*  
bla 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 


### `checkCollection ('dirpath')`  
- *description:*  
bla
- *params:*  
bla
- *returns:*  
`dict` with keys `'succRefs', 'noSuccRefs'` with list values
- *side-effects:*  
bla 
- *print:*  
n/a  
- *example:*  
`myColl`
#####  &nbsp; 


---  
### File formats
---


### `coll_data`
- *description:*  
JSON-encoded file describing the collection
- *format:*  
`collection: {title, collections: {subcoll: {subcollName, author, [recipe names]}}, recipes: {recipeName: name, ingredients: [references to ingredients catalogue]}}`
#####  &nbsp; 


### `ingredients catalogue`
- *description:*  
the ingredients catalogue in JSON format
- *format:*  
#####  &nbsp; 


---  
### MD template for docs
---


### `function()`  
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


