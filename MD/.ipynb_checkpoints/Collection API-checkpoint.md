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
---    

#### Collection-related

- `infoSubcolls()`  
  *description:*
  >general information on subcollections contained in collection  
  
  *params:*  
  >none  
  
  *returns:*  
  >dict(#subcollections, subcollection names, recipe author names, #recipes subcollection-wise, #distinct ingredients in subcollections)  
  
  *side-effects:*  
  >none  
  
  *print:*  
  >n/a  
  
  *example:*  
  >`info = myColl.infoSubcolls()`
---    
- `recipesList()`  
   *description:*  
   >return list of recipes total or subcollection-wise  
   
   *params:*  
   >`subcoll_letter:string` (optional; default: complete list)    
  
   *returns:*  
   > list(recipe names)  
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`list = myColl.recipesList('A')`  
---  
- `ingredientsList()`  
   *description:*  
   >distinct ingredients used: total, subcollection-wise  
   
   *params:*  
   >`[subcoll_letter:string]` (optional; default: complete list)  
  
   *returns:*  
   >list(references to ingredients catalogue)  
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`list = myColl.ingredientsList('B')`
---  
- `catalogList()`  
   *description:*  
   >return ingredients in ingredients catalogue: complete catalogue, list, single entry  
   
   *params:*  
   >`references_to_ingrediensts_catalogue:List` or `reference_to_ingrediensts_catalogue:string` (optional, default: complete ingredients catalog)  
  
   *returns:*  
   >list(ingredients catalogue entries)  
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`list = myColl.catalogList(['ei','brot'])`  
---
- `cosine_sim()`  
   *description:*  
   >determine cosine similarity between subcollections in total and ingredient class-wise  
   
   *params:*  
   >none  
  
   *returns:*  
   >dict
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`myColl.cosine_sim()`
---  
- `entropy()`  
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
   >`myColl.entropy()`
---  
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
---     
- `nodeSets()`     
   *description:*  
   >compute node sets: pure node set for single subcollection or intersection set for two subcollections 
   
   *params:*  
   >`graph:graph` (Networkx graph), `subcoll_letter:string` or `[subcoll_letter:string,subcoll_letter:string]`  
   
   *returns:*  
   >list(nodes with node attributes)    
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`nodesets = myColl.nodeSets(G, ['A', 'B'])`   
---     
- `edgeSets()`   
   *description:*  
   >compute edge sets: pure, mixed, intersection  
   
   *params:*  
   >`graph:graph` (Networkx graph), `subcoll_letter:string` or `[subcoll_letter:string,subcoll_letter:string]`  
  
   *returns:*  
   >dict({A_e_pure, A_e_mixed, B_e_pure, B_e_mixed, AB_e_intersect})   
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`edgesets = myColl.edgeSets(G, 'A')`   
---     
- `Krack()`  
   *description:*  
   >compute Krackhardt's index (global, ingredient-wise)  
   >KI = (EL-IL)/(EL+IL) with EL = external links and IL = internal links  
   >As defined here, the Krackhardt index measures the connection between a collection's "pure node set" and the intersection node set.  
   >internal links: relations in the "pure edges set", i.e. relations that connect ingredient nodes in the collection's "pure node set"  
   >external links: relations in the "mixed edges set"  
   >`Krack()` is applicable only if collection has two subcollections
   
   *params:*  
   >`graph:graph` (Networkx graph), `subcoll_letter:string` or `references_to_ingrediensts_catalogue:List`   
     
   *returns:*  
   >dict({ })  
   
   *side-effects:*  
   >none  
  
   *print:*  
   >n/a  
  
   *examples:*  
   >`index_subcoll = myColl.Krack(G, 'A')`  
   >`index_some = myColl.Krack(G, ['butter', 'ei'])`  
---     
- `toDot()`  
   *description:*  
   >create dot-file for graph  
   
   *params:*  
   >`graph:graph`, `path:path`, `filename:filename` (dot file)  
  
   *returns:*  
   >nothing  
   
   *side-effects:*  
   >dot file is written to given path   
  
   *print:*  
   >n/a  
  
   *example:*  
   >`myColl.toDot(G,'myWorkingDir','myDOTgraph')`
---     
- `toGEXF()`  
   *description:*  
   >output in gexf format  
   
   *params:*  
   >`graph:graph`, `path:path`, `filename:filename` (gexf file)  
  
   *returns:*  
   >nothing  
   
   *side-effects:*  
   >gexf file is written to given path    
  
   *print:*  
   >n/a  
  
   *example:*  
   >`myColll.toGEXF(G,'myWorkingDir','myGEXFgraph')`
---     
- `toCSV()`    
   *description:*  
   >create CSV-coded file for graph  
   
   *params:*  
   >params: `graph:graph` (Networkx graph), `path:path`, `filename:filename` (CSV file)   
  
   *returns:*  
   >nothing  
   
   *side-effects:*  
   >CSV file is written to given path  
  
   *print:*  
   >n/a  
  
   *example:*  
   >`myColl.toCSV(G,'myWorkingDir','myCSVgraph')`
---     
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
---  
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
   >`myColl`