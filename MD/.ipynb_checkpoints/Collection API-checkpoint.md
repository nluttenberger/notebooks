## Collection API

#### Init

- read XML-coded descriptor file for collection
- read json file for ingredients catalog
- generate json file holding collection data  
  params: `graphLab:path` (graphLab location), `descrip_fn:filename` (XML-coded descriptor for graph experiment),  
  `igdtCat_path:path`(path to ingredients catalogue), `igdtCat_fn:filename` (ingredients catalogue filename)    
  output:  json-encoded file with subcollection and recipe lists, located 

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
   
- `nodeSets()`: node sets (subcollection(s) pure, intersection);  
   params: `graph`,`letter:string` `[, letter:string]`  
   returns: `nodes:list` with node attributes 
   
- `edgeSets()`: edge sets (pure, mixed, intersection);  
   params: `graph`,`letter:string [,letter:string]`  
   returns: `edges:dict`  
   
- `Krack()`: Krackhardt's index (global, ingredient-wise)  
   params: `letter:string, letter:string`   
   
- `toDot()`: output in dot format  
   params: `graph:graph`, `path:path`, `filename:filename` (dot file)  
   
- `toGephi()`: output in Gephi format  
   params: `graph:graph`, `path:path`, `filename:filename` (Gephi file) 
   
- `toCSV()`: output in csv format  
   params: `graph:graph`, `path:path`, `filename:filename` (CSV file)    
   
- `previewSVG()`: embed SVG-formated graph in HTML wrapper  
   params: `graph:graph`, `path:path` (common path), `fnSVGin:filename` (initial SVG file), `fnHTMLout:filename`(output HTML file) 

#### JSON file format

- collection title
- collections : { subcollection letter : { subcollection name, author, list of recipe names } }
- recipes : { recipe name : list of references to ingredients catalogue }
