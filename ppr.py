# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright 2009 Abraham Flaxman

# based on NetworkX PageRank module (networkx/algorithms/pagerank.py):
#    Copyright (C) 2004-2008 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    Distributed under the terms of the GNU Lesser General Public License
#    http://www.gnu.org/copyleft/lesser.html

import networkx
from networkx import NetworkXError

def ppr(G, v, alpha=0.85, max_iter=1000, tol=1.0e-8, nstart=None):
    """Return the Personal PageRank of the nodes in the graph.

    Personal PageRank computes the largest eigenvector of the stochastic
    adjacency matrix of G with reset vector v.  
    

    Parameters
    -----------
    G : graph
      A networkx graph

    v : dictionary
      A reset vector

    alpha : float, optional
      Parameter for PageRank, default=0.85
       
    max_iter : integer, optional
      Maximum number of iterations in power method.

    tol : float, optional
      Error tolerance used to check convergence in power method iteration.

    nstart : dictionary, optional
      Starting value of PageRank iteration for each node. 

    Returns
    -------
    nodes : dictionary
       Dictionary of nodes with value as PageRank 


    Examples
    --------
    >>> G=nx.path_graph(4)
    >>> pr=nx.pagerank(G,{0:.5, 1:.5},alpha=0.9)
    """

    #if type(G) == networkx.MultiGraph or type(G) == networkx.MultiDiGraph():
    #    raise Exception("pagerank() not defined for graphs with multiedges.")

    # create a copy in (right) stochastic form        
    W=stochastic_graph(G)

    # normalize the reset vector
    reset = dict.fromkeys(W, 0.0)
    sum_v = sum(v.values())
    for n in v:
        assert G.has_node(n), 'node "%s" not found' % str(n)
        reset[n] = v[n]/sum_v
    
    # choose fixed starting vector if not given
    if nstart is None:
        x=dict.fromkeys(W,0.0)
        for n in reset:
            x[n] = 1.
    else:
        x=nstart
    # normalize starting vector to 1                
    s=sum(x.values())
    assert s != 0., 'starting vector must be non-zero'
    for k in x: x[k]/=s

    nnodes=W.number_of_nodes()
    # "dangling" nodes, no links out from them
    dangle=[n for n in W if sum(W[n].values())==0.0]
    # pagerank power iteration: make up to max_iter iterations        
    for i in range(max_iter):
        xlast=x
        x=dict.fromkeys(xlast.keys(),0)
        danglesum=alpha/nnodes*sum(xlast[n] for n in dangle)
        teleportsum=(1.0-alpha)*sum(xlast.values())
        for n in x:
            # this matrix multiply looks odd because it is
            # doing a left multiply x^T=xlast^T*W
            for nbr in W[n]:
                x[nbr]+=alpha*xlast[n]*W[n][nbr]
            x[n]+=danglesum+teleportsum*reset[n]
        # normalize vector to 1                
        s=1.0/sum(x.values())
        for n in x: x[n]*=s
        # check convergence, l1 norm            
        err=sum([abs(x[n]-xlast[n]) for n in x])
        if err < tol:
            return x

    print("WARNING:   " + "pagerank: power iteration failed to converge in %d iterations."%(i+1))
    return x


def stochastic_graph(G,copy=True):
    """Return a right-stochastic representation of G.

    A right-stochastic graph is a weighted graph in which all of
    the node (out) neighbors edge weights sum to 1.
    
    Parameters
    -----------
    G : graph
      A networkx graph, must have valid edge weights

    copy : bool, optional
      If True make a copy of the graph, otherwise modify original graph

    """        
    if not G.weighted:
        raise NetworkXError("Input to stochastic_graph() must be a weighted graph.")

    if copy:
        if G.directed:
            W=networkx.DiGraph(G)
        else:
            W=networkx.Graph(G) 
    else:
        W=G # reference original graph, no copy

    for n in W:
        deg=float(sum(W[n].values()))
        for p in W[n]: 
            W[n][p]/=deg
            # also adjust pred entry for consistency 
            # though it is not used in pagerank algorithm
            if G.directed:
                W.pred[p][n]/=deg
    return W
