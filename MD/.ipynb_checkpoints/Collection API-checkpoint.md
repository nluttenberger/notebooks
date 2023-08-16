## Collection API

#### Init

- read json file for collection
- read json file for ingredients catalog

#### Collection-related

- `infoSubcolls()`: subcollection letter, name, author, #recipes   

- `recipes_list()`: list of recipes total, subcollection-wise  
   params: `[letter:string]`  
   returns: list of recipe names

- `ingredients_list()`: list of ingredients total, subcollection-wise  
   params: `[letter:string]`  
   returns: list of ingredients
   
- `catalog_list()`: list of catalog entries total, nbunch, single  
   params: nbunch or igt, if none list complete catalog
   returns: list of catalog entries


#### Graph-related

- `toGraph()`: convert (sub)collection(s) to ingredient graph  
   params: `letter:string [, letter:string]`  
   returns: Networkx Graph with node attributes `i-name`, `i-class`, `occ`, `sub`, and edge attributes `id`, `weight`
   
- `nodeSets()`: node sets (subcollection(s), pure, intersection);  
   params: `graph`,`letter:string` `[, letter:string]`  
   returns: `nodes:list` with node attributes 
   
- `edgeSets()`: edge sets (pure, mixed, intersection);  
   params: `graph`,`letter:string [,letter:string]`  
   returns: `edges:dict`  
   
- `Krack()`: Krackhardt's index (global, ingredient-wise)  
   params: `letter:string, letter:string`   
   
- `toDot()`: output in dot format  
   params: `graph:graph, filename:string`  
   
- `toGephi()`: output in Gephi format  
   params: `graph:graph, filename:string`  
   
- `toCSV()`: output in csv format  
   params: `graph:graph, filename:string`  
   
- `SVGtoHTML()`: embed SVG graphics in HTML+CSS wrapper

#### JSON file format

- title
- subcollections: { subcollection letter : name, author, recipes list }
- recipes: { recipe name: ingredients list }
