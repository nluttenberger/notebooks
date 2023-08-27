## Recipe Collection API

#### Init

- `RecipeCollection()`  
  *description:*  
    >read cueML/XML-coded descriptor for collection from graphLab, read cueML/json-coded ingredients catalog, generate json-coded file holding collection data  
    
  *params:*  
    >`graphLab:path` (absolute path to graphLab top-level directory)  
    >`descrip_fn:filename` (XML-coded descriptor for graph experiment, located in graphLab top-level directory)  
    >`igdtCat_path:path` (full absolute path to ingredients catalogue)   
    >`working_dir` (notebook's working directory; usually the 'data' directory)  
    
  *returns:*  
    >nothing
    
  *side-effects:*  
    >produces json-coded file `coll_data.json` with subcollection and recipe lists in the given working directory  
    
  *print:*  
    >collection name, #subcollections, recipe author names, #recipes total, #recipes subcollection-wise, #distinct ingredients in collection, #ingredients in ingredients catalogue  
    
  *example:*
    >`myColl = RecipeCollection(gL_path, myDesc, myIgtCat, myWorkingDir)`  
    >`print(myColl)`
  

#### Collection-related

- `infoSubcolls()`  
  *description:*
  >general information on subcollections contained in collection  
  
  *params:*  
  >none  
  
  *returns:*  
  >#subcollections, subcollection names, recipe author names, #recipes subcollection-wise, #distinct ingredients in subcollections  
  
  *side-effects:*  
  >none  
  
  *print:*  
  >n/a  
  
  *example:*  
  >`infoSubcolls()`
  
- `recipes_list()`  
   description: list of recipes total, subcollection-wise  
   params: `[letter:string]` (subcollection) (optional)  
   returns: list of recipe names

- `ingredients_list()`  
   description: distinct ingredients used: total, subcollection-wise  
   params: `[letter:string]` (subcollection) (optional)  
   returns: list of distinct ingredients
   
- `catalog_list()`  
   description: ingredients in ingredients catalog: complete catalogue, nbunch, single entry  
   params: `nbunch` or `ingredient` (optional, default: complete ingredients catalog)  
   returns: list of ingredients catalogue entries


#### Graph-related

- `toGraph()`  
   *description:*  
   >convert (sub)collection(s) to ingredient graph    
   
   *params:*  
   > `subcoll_letter:string` or `[subcoll_letter:string, subcoll_letter:string]`    
   
   *returns:*  
   >Networkx Graph with node attributes `i-name`, `i-class`, `occ`, `sub`, and edge attributes `id`, `weight`  
   
   *side-effects:*  
   >none  
   
   *print:*  
   >n/a  
   
   *example:*  
  >`G = myColl.toGraph(['A', 'B'])`
   
- `nodeSets()`     
   *description:*  
   >compute node sets: pure set(s) for subcollection(s) and intersection set (when two subcollections are given) 
   
   *params:*  
   >`graph:graph` (Networkx graph), `subcoll_letter:string` or `[subcoll_letter:string,subcoll_letter:string]`  
   
   *returns:*  
   >`nodes:list` with node attributes    
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`nodesets = myColl.nodeSets(G, ['A', 'B'])`   
   
- `edgeSets()`  
   description: compute edge sets: pure, mixed, intersection  
   params: `graph`,`letter:string [,letter:string]`  
   returns: `edges:dict`  
   
- `Krack()`  
   description: compute Krackhardt's index (global, ingredient-wise)  
   params: `letter:string, letter:string`   
   
- `toDot()`  
   description: output in dot format  
   params: `graph:graph`, `path:path`, `filename:filename` (dot file)  
   
- `toGephi()`  
   description: output in Gephi format  
   params: `graph:graph`, `path:path`, `filename:filename` (Gephi file) 
   
- `toCSV()`  
   description: output in csv format  
   params: `graph:graph`, `path:path`, `filename:filename` (CSV file)    
   
- `previewSVG()`     
   *description:*  
   >embed SVG-formated graph in HTML/CSS/JS wrapper, showing graph nodes only  
   
   *params:*  
   >`graph:graph` (Networkx graph to be previewed), `scale:float` (scaling factor for font size in SVG graph, 1.0 < scale < 2.0, recommended: 1.0, default: 1.0)  
   
   *returns:*  
   >nothing  
   
   *side-effects:*  
   >`svgGraph-poor.svg`, `preview.html` and `dotdot.dot` files are written to given working directory  
   
   *print:*  
   >n/a  
   
   *example:*  
   >`previewSVG(G,1.1)`

#### `coll_data` file format (json)

>collection: {title, collections: {subcollection letter: {subcollectionName, author, [recipe names]}}, recipes: {recipeName: name, ingredients: [references to ingredients catalogue]}}  

  
   *description:*  
   >  
   
   *params:*  
   >  
  
   *returns:*  
   >  
   
   *side-effects:*  
   >  
  
   *print:*  
   >n/a  
  
   *example:*  
   >``