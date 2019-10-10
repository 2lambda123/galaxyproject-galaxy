/** deep equal of two dictionaries */
function matches(d, d2) {
    for (var k in d2) {
        if (Object.prototype.hasOwnProperty.call(d2, k)) {
            if (!Object.prototype.hasOwnProperty.call(d, k) || d[k] !== d2[k]) {
                return false;
            }
        }
    }
    return true;
}

/** map key/values in obj
 *      if propsOrFn is an object, return only those k/v that match the object
 *      if propsOrFn is function, call the fn and returned the mapped values from it
 */
function iterate(obj, propsOrFn) {
    var fn = typeof propsOrFn === "function" ? propsOrFn : undefined;
    var props = typeof propsOrFn === "object" ? propsOrFn : undefined;
    var returned = [];
    var index = 0;
    for (var key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            var value = obj[key];
            if (fn) {
                returned.push(fn.call(value, value, key, index));
            } else if (props) {
                //TODO: break out to sep?
                if (typeof value === "object" && matches(value, props)) {
                    returned.push(value);
                }
            } else {
                returned.push(value);
            }
            index += 1;
        }
    }
    return returned;
}

// ============================================================================
/** A graph edge containing the name/id of both source and target and optional data
 */
function Edge(source, target, data) {
    this.source = source !== undefined ? source : null;
    this.target = target !== undefined ? target : null;
    this.data = data || null;
    //if( typeof data === 'object' ){
    //    extend( self, data );
    //}
    return this;
}
/** String representation */
Edge.prototype.toString = function() {
    return `${this.source}->${this.target}`;
};

/** Return a plain object representing this edge */
Edge.prototype.toJSON = function() {
    //TODO: this is safe in most browsers (fns will be stripped) - alter tests to incorporate this in order to pass data
    //return this;
    var json = {
        source: this.source,
        target: this.target
    };
    if (this.data) {
        json.data = this.data;
    }
    return json;
};

// ============================================================================
/** A graph vertex with a (unique) name/id and optional data.
 *      A vertex contains a list of Edges (whose sources are this vertex) and maintains the degree.
 */
function Vertex(name, data) {
    this.name = name !== undefined ? name : "(unnamed)";
    this.data = data || null;
    this.edges = {};
    this.degree = 0;
    return this;
}

/** String representation */
Vertex.prototype.toString = function() {
    return `Vertex(${this.name})`;
};

//TODO: better name w no collision for either this.eachEdge or this.edges
/** Iterate over each edge from this vertex */
Vertex.prototype.eachEdge = function(propsOrFn) {
    return iterate(this.edges, propsOrFn);
};

/** Return a plain object representing this vertex */
Vertex.prototype.toJSON = function() {
    //return this;
    return {
        name: this.name,
        data: this.data
    };
};

// ============================================================================
/** Base (abstract) class for Graph search algorithms.
 *      Pass in the graph to search
 *      and an optional dictionary containing the 3 vertex/edge processing fns listed below.
 */
var GraphSearch = function(graph, processFns) {
    this.graph = graph;

    this.processFns = processFns || {
        vertexEarly: function(vertex, search) {
            //console.debug( 'processing vertex:', vertex.name, vertex );
        },
        edge: function(from, edge, search) {
            //console.debug( this, 'edge:', from, edge, search );
        },
        vertexLate: function(vertex, search) {
            //console.debug( this, 'vertexLate:', vertex, search );
        }
    };

    this._cache = {};
    return this;
};

/** Search interface where start is the vertex (or the name/id of the vertex) to begin the search at
 *      This public interface caches searches and returns the cached version if it's already been done.
 */
GraphSearch.prototype.search = function _search(start) {
    if (start in this._cache) {
        return this._cache[start];
    }
    if (!(start instanceof Vertex)) {
        start = this.graph.vertices[start];
    }
    return (this._cache[start.name] = this._search(start));
};

/** Actual search (private) function (abstract here) */
GraphSearch.prototype._search = function __search(start, search) {
    search = search || {
        discovered: {},
        //parents : {},
        edges: []
    };
    return search;
};

/** Searches graph from start and returns a search tree of the results */
GraphSearch.prototype.searchTree = function _searchTree(start) {
    return this._searchTree(this.search(start));
};

/** Helper fn that returns a graph (a search tree) based on the search object passed in (does not actually search) */
GraphSearch.prototype._searchTree = function __searchTree(search) {
    return new Graph(true, {
        edges: search.edges,
        vertices: Object.keys(search.discovered).map(key => this.graph.vertices[key].toJSON())
    });
};

// ============================================================================
/** Breadth first search algo.
 */
var BreadthFirstSearch = function(graph, processFns) {
    GraphSearch.call(this, graph, processFns);
    return this;
};
BreadthFirstSearch.prototype = new GraphSearch();
BreadthFirstSearch.prototype.constructor = BreadthFirstSearch;

/** (Private) implementation of BFS */
BreadthFirstSearch.prototype._search = function __search(start, search) {
    search = search || {
        discovered: {},
        //parents : {},
        edges: []
    };

    var self = this;
    var queue = [];

    function discoverAdjacent(adj, edge) {
        var source = this;
        if (self.processFns.edge) {
            self.processFns.edge.call(self, source, edge, search);
        }
        if (!search.discovered[adj.name]) {
            //console.debug( '\t\t\t', adj.name, 'is undiscovered:', search.discovered[ adj.name ] );
            search.discovered[adj.name] = true;
            //search.parents[ adj.name ] = source;
            search.edges.push({ source: source.name, target: adj.name });
            //console.debug( '\t\t\t queuing undiscovered: ', adj );
            queue.push(adj);
        }
    }

    //console.debug( 'BFS starting. start:', start );
    search.discovered[start.name] = true;
    queue.push(start);
    while (queue.length) {
        var vertex = queue.shift();
        //console.debug( '\t Queue is shifting. Current:', vertex, 'queue:', queue );
        if (self.processFns.vertexEarly) {
            self.processFns.vertexEarly.call(self, vertex, search);
        }
        self.graph.eachAdjacent(vertex, discoverAdjacent);
        if (self.processFns.vertexLate) {
            self.processFns.vertexLate.call(self, vertex, search);
        }
    }
    //console.debug( 'search.edges:', JSON.stringify( search.edges ) );
    return search;
};

// ============================================================================
/** Depth first search algorithm.
 */
var DepthFirstSearch = function(graph, processFns) {
    GraphSearch.call(this, graph, processFns);
    return this;
};
DepthFirstSearch.prototype = new GraphSearch();
DepthFirstSearch.prototype.constructor = DepthFirstSearch;

/** (Private) implementation of DFS */
DepthFirstSearch.prototype._search = function(start, search) {
    //console.debug( 'depthFirstSearch:', start );
    search = search || {
        discovered: {},
        //parents    : {},
        edges: [],
        entryTimes: {},
        exitTimes: {}
    };
    var self = this;
    var time = 0;

    // discover verts adjacent to the source (this):
    //  processing each edge, saving the edge to the tree, and caching the reverse path with parents
    function discoverAdjacentVertices(adjacent, edge) {
        //console.debug( '\t\t adjacent:', adjacent, 'edge:', edge );
        var sourceVertex = this;
        if (self.processFns.edge) {
            self.processFns.edge.call(self, sourceVertex, edge, search);
        }
        if (!search.discovered[adjacent.name]) {
            //search.parents[ adjacent.name ] = sourceVertex;
            search.edges.push({
                source: sourceVertex.name,
                target: adjacent.name
            });
            recurse(adjacent);
        }
    }

    // use function stack for DFS stack process verts, times, and discover adjacent verts (recursing into them)
    function recurse(vertex) {
        //console.debug( '\t recursing into: ', vertex );
        search.discovered[vertex.name] = true;
        if (self.processFns.vertexEarly) {
            self.processFns.vertexEarly.call(self, vertex, search);
        }
        search.entryTimes[vertex.name] = time++;

        self.graph.eachAdjacent(vertex, discoverAdjacentVertices);

        if (self.processFns.vertexLate) {
            self.processFns.vertexLate.call(self, vertex, search);
        }
        search.exitTimes[vertex.name] = time++;
    }
    // begin recursion with the desired start
    recurse(start);

    return search;
};

// ============================================================================
/** A directed/non-directed graph object.
 */
function Graph(directed, data, options) {
    //TODO: move directed to options
    this.directed = directed || false;
    return this.init(options).read(data);
}
window.Graph = Graph;

/** Set up options and instance variables */
Graph.prototype.init = function(options) {
    options = options || {};

    this.allowReflexiveEdges = options.allowReflexiveEdges || false;

    this.vertices = {};
    this.numEdges = 0;
    return this;
};

/** Read data from the plain object data - both in d3 form (nodes and links) or vertices and edges */
Graph.prototype.read = function(data) {
    if (!data) {
        return this;
    }
    if (Object.prototype.hasOwnProperty.call(data, "nodes")) {
        return this.readNodesAndLinks(data);
    }
    if (Object.prototype.hasOwnProperty.call(data, "vertices")) {
        return this.readVerticesAndEdges(data);
    }
    return this;
};

//TODO: the next two could be combined
/** Create the graph using a list of nodes and a list of edges (where source and target are indeces into nodes) */
Graph.prototype.readNodesAndLinks = function(data) {
    if (!(data && Object.prototype.hasOwnProperty.call(data, "nodes"))) {
        return this;
    }
    //console.debug( 'readNodesAndLinks:', data );
    //console.debug( 'data:\n' + JSON.stringify( data, null, '  ' ) );
    data.nodes.forEach(node => {
        this.createVertex(node.name, node.data);
    });
    //console.debug( JSON.stringify( self.vertices, null, '  ' ) );

    (data.links || []).forEach((edge, i) => {
        var sourceName = data.nodes[edge.source].name;
        var targetName = data.nodes[edge.target].name;
        this.createEdge(sourceName, targetName, this.directed);
    });
    //console.debug( JSON.stringify( self.toNodesAndLinks(), null, '  ' ) );
    return this;
};

/** Create the graph using a list of nodes and a list of edges (where source and target are names of nodes) */
Graph.prototype.readVerticesAndEdges = function(data) {
    if (!(data && Object.prototype.hasOwnProperty.call(data, "vertices"))) {
        return this;
    }
    //console.debug( 'readVerticesAndEdges:', data );
    //console.debug( 'data:\n' + JSON.stringify( data, null, '  ' ) );
    data.vertices.forEach(node => {
        this.createVertex(node.name, node.data);
    });
    //console.debug( JSON.stringify( this.vertices, null, '  ' ) );

    (data.edges || []).forEach((edge, i) => {
        this.createEdge(edge.source, edge.target, this.directed);
    });
    //console.debug( JSON.stringify( this.toNodesAndLinks(), null, '  ' ) );
    return this;
};

/** Return the vertex with name, creating it if necessary */
Graph.prototype.createVertex = function(name, data) {
    //console.debug( 'createVertex:', name, data );
    if (this.vertices[name]) {
        return this.vertices[name];
    }
    return (this.vertices[name] = new Vertex(name, data));
};

/** Create an edge in vertex named sourceName to targetName (optionally adding data to it)
 *      If directed is false, create a second edge from targetName to sourceName.
 */
Graph.prototype.createEdge = function(sourceName, targetName, directed, data) {
    //note: allows multiple 'equivalent' edges (to/from same source/target)
    //console.debug( 'createEdge:', source, target, directed );
    var isReflexive = sourceName === targetName;
    if (!this.allowReflexiveEdges && isReflexive) {
        return null;
    }

    var sourceVertex = this.vertices[sourceName];
    var targetVertex = this.vertices[targetName];
    //note: silently ignores edges from/to unknown vertices
    if (!(sourceVertex && targetVertex)) {
        return null;
    }

    var edge = new Edge(sourceName, targetName, data);
    sourceVertex.edges[targetName] = edge;
    sourceVertex.degree += 1;
    this.numEdges += 1;

    //TODO:! don't like having duplicate edges for non-directed graphs
    // mirror edges (reversing source and target) in non-directed graphs
    //  but only if not reflexive
    if (!isReflexive && !directed) {
        // flip directed to prevent recursion loop
        this.createEdge(targetName, sourceName, true);
    }

    return edge;
};

/** Walk over all the edges of the graph using the vertex.eachEdge iterator */
Graph.prototype.edges = function(propsOrFn) {
    return Array.prototype.concat.apply([], this.eachVertex(vertex => vertex.eachEdge(propsOrFn)));
};

/** Iterate over all the vertices in the graph */
Graph.prototype.eachVertex = function(propsOrFn) {
    return iterate(this.vertices, propsOrFn);
};

/** Return a list of the vertices adjacent to vertex */
Graph.prototype.adjacent = function(vertex) {
    return iterate(vertex.edges, edge => this.vertices[edge.target]);
};

/** Call fn on each vertex adjacent to vertex */
Graph.prototype.eachAdjacent = function(vertex, fn) {
    return iterate(vertex.edges, edge => {
        var adj = this.vertices[edge.target];
        return fn.call(vertex, adj, edge);
    });
};

/** Print the graph to the console (debugging) */
Graph.prototype.print = function() {
    console.log(`Graph has ${Object.keys(this.vertices).length} vertices`);
    this.eachVertex(vertex => {
        console.log(vertex.toString());
        vertex.eachEdge(edge => {
            console.log(`\t ${edge}`);
        });
    });
    return this;
};

/** Return a DOT format string of this graph */
Graph.prototype.toDOT = function() {
    var strings = [];
    strings.push("graph bler {");
    this.edges(edge => {
        strings.push(`\t${edge.from} -- ${edge.to};`);
    });
    strings.push("}");
    return strings.join("\n");
};

/** Return vertices and edges of this graph in d3 node/link format */
Graph.prototype.toNodesAndLinks = function() {
    var indeces = {};
    return {
        nodes: this.eachVertex((vertex, key, i) => {
            indeces[vertex.name] = i;
            return vertex.toJSON();
        }),
        links: this.edges(edge => {
            var json = edge.toJSON();
            json.source = indeces[edge.source];
            json.target = indeces[edge.target];
            return json;
        })
    };
};

/** Return vertices and edges of this graph where edges use the name/id as source and target */
Graph.prototype.toVerticesAndEdges = function() {
    return {
        vertices: this.eachVertex((vertex, key) => vertex.toJSON()),
        edges: this.edges(edge => edge.toJSON())
    };
};

/** Search this graph using BFS */
Graph.prototype.breadthFirstSearch = function(start, processFns) {
    return new BreadthFirstSearch(this).search(start);
};

/** Return a searchtree of this graph using BFS */
Graph.prototype.breadthFirstSearchTree = function(start, processFns) {
    return new BreadthFirstSearch(this).searchTree(start);
};

/** Search this graph using DFS */
Graph.prototype.depthFirstSearch = function(start, processFns) {
    return new DepthFirstSearch(this).search(start);
};

/** Return a searchtree of this graph using DFS */
Graph.prototype.depthFirstSearchTree = function(start, processFns) {
    return new DepthFirstSearch(this).searchTree(start);
};

//Graph.prototype.shortestPath = function( start, end ){
//};
//
//Graph.prototype.articulationVertices = function(){
//};
//
//Graph.prototype.isAcyclic = function(){
//};
//
//Graph.prototype.isBipartite = function(){
//};

/** Return an array of weakly connected (no edges between) sub-graphs in this graph */
Graph.prototype.weakComponents = function() {
    //TODO: alternately, instead of returning graph-like objects:
    //  - could simply decorate the vertices (vertex.component = componentIndex), or clone the graph and do that

    var searchGraph = this;
    var undiscovered;
    var components = [];

    function getComponent(undiscoveredVertex) {
        //TODO: better interface on dfs (search v. searchTree)
        var search = new DepthFirstSearch(searchGraph)._search(undiscoveredVertex);

        // remove curr discovered from undiscovered
        undiscovered = undiscovered.filter(name => !(name in search.discovered));

        return {
            vertices: Object.keys(search.discovered).map(vertexName => this.vertices[vertexName].toJSON()),
            edges: search.edges.map(edge => {
                // restore any reversed edges
                var hasBeenReversed = this.vertices[edge.target].edges[edge.source] !== undefined;
                if (this.directed && hasBeenReversed) {
                    var swap = edge.source;
                    edge.source = edge.target;
                    edge.target = swap;
                }
                return edge;
            })
        };
    }

    if (this.directed) {
        // if directed - convert to undirected for search
        searchGraph = new Graph(false, this.toNodesAndLinks());
    }
    undiscovered = Object.keys(searchGraph.vertices);
    //console.debug( '(initial) undiscovered:', undiscovered );
    while (undiscovered.length) {
        var undiscoveredVertex = searchGraph.vertices[undiscovered.shift()];
        components.push(getComponent(undiscoveredVertex));
        //console.debug( 'undiscovered now:', undiscovered );
    }

    //console.debug( 'components:\n', JSON.stringify( components, null, '  ' ) );
    return components;
};

/** Return a single graph containing the weakly connected components in this graph */
Graph.prototype.weakComponentGraph = function() {
    //note: although this can often look like the original graph - edges can be lost
    var components = this.weakComponents();
    return new Graph(this.directed, {
        vertices: components.reduce((reduction, curr) => reduction.concat(curr.vertices), []),
        edges: components.reduce((reduction, curr) => reduction.concat(curr.edges), [])
    });
};

/** Return an array of graphs of the weakly connected components in this graph */
Graph.prototype.weakComponentGraphArray = function() {
    //note: although this can often look like the original graph - edges can be lost
    var graph = this;
    return this.weakComponents().map(component => new Graph(graph.directed, component));
};

// ============================================================================
/** Create a random graph with numVerts vertices and numEdges edges (for testing)
 */
function randGraph(directed, numVerts, numEdges) {
    //console.debug( 'randGraph', directed, numVerts, numEdges );
    var data = { nodes: [], links: [] };
    function randRange(range) {
        return Math.floor(Math.random() * range);
    }
    for (var i = 0; i < numVerts; i++) {
        data.nodes.push({ name: i });
    }
    for (i = 0; i < numEdges; i++) {
        data.links.push({
            source: randRange(numVerts),
            target: randRange(numVerts)
        });
    }
    //console.debug( JSON.stringify( data, null, '  ' ) );
    return new Graph(directed, data);
}

// ============================================================================
export default {
    Vertex: Vertex,
    Edge: Edge,
    BreadthFirstSearch: BreadthFirstSearch,
    DepthFirstSearch: DepthFirstSearch,
    Graph: Graph,
    randGraph: randGraph
};
