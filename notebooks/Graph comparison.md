## Comparing Davidis and Ottolenghi collections for vegetable recipes

#### get ingredients lists for ...

- A recipes
- B recipes
- build common recipes lists
- build common ingredients lists

#### compute projection

- A = adjacency matrix for bipartite graph  
      ingredients -> recipes
- G = adjacency matrix for ingredient graph
- G = A x A<sup>T</sup>

#### compute node and edge attributes 

- nodes: name, class, occurence, subgraph
- edges: id, weight, subgraph

#### compute node and edge sets   

- A nodes-pure, B nodes-pure, A∩B nodes
- A edges-pure, A edges-mixed,  
  A∩B edges,  
  B edges-pure, B edges-mixed
- "pure" means: contained in A\A∩B, resp. B\A∩B

#### comparison

- extract edges veg--spice
- extract edges veg--herb