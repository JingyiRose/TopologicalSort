# ReconBuilder.py
# This code builds a representation of a host tree, parasite tree, and a reconfiguration
# as specified in Recon.py using the host tree, parasite tree, and reconfiguration 
# representation in the DTL.

import Recon
from Recon import TreeType #TODO this is redundant

# The input trees are dictionaries of the following form:
# There is a dummy edge at the top of each tree called 'hTop' (host tree)
# or 'pTop' (parasite tree).  The tree is a dictionary in which the 
# key is the name of the edge and the the value is of the form
# (topVertex, bottomVertex, edge1, edge2)
# where topVertex is the top vertex of the edge, bottomVertex is the bottom vertex of the edge
# and edge1 and edge2 are the two children edges or None (in the case of an edge terminating at a leaf)
# Example host tree
host_tree = { 'hTop': ('Top', 'm0', ('m0', 'm1'), ('m0', 'm2')),
 ('m0', 'm1'): ('m0', 'm1', None, None),
 ('m0', 'm2'): ('m0', 'm2', ('m2', 'm3'), ('m2', 'm4')),
 ('m2', 'm3'): ('m2', 'm3', None, None),
 ('m2', 'm4'): ('m2', 'm4', None, None)}

# Example parasite tree
parasite_tree = { 'pTop': ('Top', 'n0', ('n0', 'n1'), ('n0', 'n2')),
  ('n0', 'n1'): ('n0', 'n1', None, None),
  ('n0', 'n2'): ('n0', 'n2', ('n2', 'n3'), ('n2', 'n4')),
  ('n2', 'n3'): ('n2', 'n3', None, None),
  ('n2', 'n4'): ('n2', 'n4', None, None)}

# Example host root:  
host_root = 'm0'

# Example parasite root: 
parasite_root = 'n0'

# Example tip mapping:  
tip_mapping= {'n1': 'm4', 'n3': 'm4', 'n4': 'm4'}

# Example reconciliation:
reconciliation = { ('n0', 'm4'): [('D', ('n1', 'm4'), ('n2', 'm4'))],
('n1', 'm4'): [('C', (None, None), (None, None))],
('n2', 'm4'): [('D', ('n3', 'm4'), ('n4', 'm4'))],
('n3', 'm4'): [('C', (None, None), (None, None))],
('n4', 'm4'): [('C', (None, None), (None, None))]}

# Example frequency dictionary
# Provides frequency information for all non-contemporaneous associations
# ROSE:  YOU DON'T NEED TO WORRY ABOUT THIS
frequencies = { ('D', ('n1', 'm4'), ('n2', 'm4')): 0.5,
                ('D', ('n3', 'm4'), ('n4', 'm4')): 0.75 }

def build_formatted_tree(tree):
    """
    :param tree:  a tree dictionary
    :return: A temporal graph that contains all the temporal relations implied by
             the tree. Each key is a node tuple of the form (name, type) where name
             is a string representing the name of a parasite or host tree INTERNAL 
             node and type is either TreeType.HOST or TreeType.PARASITE which are 
             defined in Recon.py. The associated value is a list of node tuples that
             are the children of this node tuple in the tree.
    """
    tree_type = None
    if 'pTop' in tree:
        tree_type = TreeType.PARASITE
    else:
        tree_type = TreeType.HOST

    formatted_tree = {}
    for edge_name in tree:
        edge_four_tuple = tree[edge_name]
        # the temporal graph does not contain leaves as keys
        if _is_leaf_edge(edge_four_tuple):
            continue
        # the temporal graph contains internal node tuples as keys,
        # and their children nodes tuples as values
        node_name = _bottom_node(edge_four_tuple)
        left_child_name = edge_four_tuple[2][1]
        right_child_name = edge_four_tuple[3][1]
        formatted_tree[(node_name, tree_type)] = [(left_child_name, tree_type), \
                                               (right_child_name, tree_type)]
    return formatted_tree

def createParentDict(H, P):
    """
    :param host_tree:  host tree dictionary
    :param parasite_tree:  parasite tree dictionary
    :return: A dictionary that maps the name of a child node to the name of its parent 
             for both the host tree and the parasite tree.
    """
    parent_dict = {}
    for edge_name in H:
        child_node = _bottom_node(H[edge_name])
        parent_node = _top_node(H[edge_name])
        parent_dict[child_node] = parent_node
    for edge_name in P:
        child_node = _bottom_node(P[edge_name])
        parent_node = _top_node(P[edge_name])
        parent_dict[child_node] = parent_node
    return parent_dict

def uniquify(elements):
    """
    :param elements:  a list whose elements might not be unique
    :return: A list that contains only the unique elements of the input list. 
    """
    hold_dict = {}
    for element in elements:
            hold_dict[element] = 1
    return list(hold_dict.keys())

def build_temporal_graph(host_tree, parasite_tree, reconciliation):
    """
    :param host_tree:  host tree dictionary
    :param parasite_tree:  parasite tree dictionary
    :param reconciliation:  reconciliation dictionary
    :return: The temporal graph which is defined as follows:
        Each key is a node tuple of the form (name, type) where name is a string representing
        the name of a parasite or host tree INTERNAL node and type is either TreeType.HOST or 
        TreeType.PARASITE which are defined in Recon.py. 
        Note that leaves of the host and parasite trees are not considered here.
        The associated value is a list of node tuples that are the children of this node tuple
        in the temporal graph.
    """
    # create a dictionary that maps each host and parasite node to its parent
    parent = createParentDict(host_tree, parasite_tree)
    # create temporal graphs for the host and parasite tree
    temporal_host_tree = build_formatted_tree(host_tree)
    temporal_parasite_tree = build_formatted_tree(parasite_tree)
    # initialize the final temporal graph to the combined temporal graphs of host and parasite tree
    temporal_graph = temporal_host_tree
    temporal_graph.update(temporal_parasite_tree)
    # add temporal relations implied by each node mapping and the corresponding event
    for node_mapping in reconciliation:
        parasite, host = node_mapping
        host_parent = parent[host]
        # get the event corresponding to this node mapping
        event_tuple = reconciliation[node_mapping][0]
        event_type = event_tuple[0]
        # if event type is a loss, the parasite is not actually mapped to the host in final 
        # reconciliation, so we skip the node_mapping
        if event_type == 'L':
            continue
        # if the node_mapping is not a leaf_mapping, we add the first relation
        if event_type != 'C':
            temporal_graph[(parasite, TreeType.PARASITE)].append((host, TreeType.HOST))
        # if the node_mapping is not a mapping onto the root of host tree, we add the second relation
        if host_parent != 'Top':
            temporal_graph[(host_parent, TreeType.HOST)].append((parasite, TreeType.PARASITE))
        
        # if event is a transfer, then we add two more temporal relations
        if event_type == 'T':
            # get the mapping for the right child which is the transferred child
            right_child_mapping = event_tuple[2]
            right_child_parasite, right_child_host = right_child_mapping
            # since a transfer event is horizontal, we have these two implied relations
            temporal_graph[(parent[right_child_host], TreeType.HOST)].append((parasite, TreeType.PARASITE))
            # the second relation is only added if the right child mapping is not a leaf mapping
            if right_child_mapping not in reconciliation or reconciliation[right_child_mapping][0][0]!='C':
                temporal_graph[(right_child_parasite, TreeType.PARASITE)].append((host, TreeType.HOST))

    for node_tuple in temporal_graph:
        # we need to make sure the associated value in the dictionary does not contain repeated node tuples
        temporal_graph[node_tuple] = uniquify(temporal_graph[node_tuple])
    return temporal_graph
    

def topological_order(temporal_graph):
    """
    :param: temporal graph as described in the return type of build_temporal_graph
    :return: A dictionary in which a key is a node tuple (name, type) as described
        in build_temporal_graph and the value is a positive integer representing its topological ordering.
        The ordering numbers are consecutive values beginning at 1.
        If the graph has a cycle and the topological ordering therefore fails, this
        function returns None.
    """
    # the ordering of nodes starts at 1
    next_order = 1
    unvisited_nodes = list(temporal_graph.keys())
    # the visitng_nodes is used to detect cycles. If the visiting_nodes add an element that is already
    # in the list, then we have found a cycle
    visiting_nodes = []
    ordering_dict = {}
    while unvisited_nodes != []:
        start_node = unvisited_nodes.pop()
        hasCycle, next_order = topological_order_helper(temporal_graph, next_order, start_node, unvisited_nodes,\
                                visiting_nodes, ordering_dict)
        # If the graph has a cycle, there is no valid topological ordering
        if hasCycle: return None
    # we need to reverse the ordering of the nodes
    reverse_ordering(ordering_dict, next_order)
    return ordering_dict 
            
def topological_order_helper(temporal_graph, start_order, start_node, unvisited_nodes, visiting_nodes, ordering_dict):
    """
    :param: temporal graph as described in the return type of build_temporal_graph
    :param: start_order is the order we start to label the nodes with
    :param: start_node is the starting node to explore the temporal_graph
    :param: unvisited_nodes are nodes in temporal graph that have not been visited
    :param: visiting_nodes are nodes that are on the same path and are currently being explored
    :param: ordering_dict is the dictionary that contains labeled node tuples and their ordering as described
            in topological_order
    :return: a Boolean value that denotes whether the part of temporal graph reachable from start_node
             contains a cycle
    :return: the start order to be used by the remaing nodes of temporal graph that have not been labeled
    """
    next_order = start_order
    # if the current node is a leaf, we do not label it and we are done
    if start_node not in temporal_graph:
        return False, next_order
    else:
        # if a node has a path to itself, we have found a cycle
        if start_node in visiting_nodes:
            return True, next_order
        visiting_nodes.append(start_node)
        child_nodes = temporal_graph[start_node]
        for child_node in child_nodes:
            # if the child_node is already labeled, we skip it
            if child_node in ordering_dict:
                continue
            if child_node in unvisited_nodes:
                unvisited_nodes.remove(child_node)
            hasCycle, next_order = topological_order_helper(temporal_graph, next_order, 
                                    child_node, unvisited_nodes, visiting_nodes, ordering_dict)
            # if we find a cycle, we stop the process
            if hasCycle: return True, next_order
        # if children are all labeled, we can label the start_node
        visiting_nodes.remove(start_node)
        ordering_dict[start_node] = next_order
        return False, next_order+1

def reverse_ordering(ordering_dict, next_order):
    """
    :param: ordering_dict as described in topological_order. The current ordering of the nodes need to be reversed.
    :param: next_order is next order that has not been used. It is 1 larger than the max order in ordering_dict
    :return: None
    """
    for node_tuple in ordering_dict:
        current_order = ordering_dict[node_tuple]
        updated_order = next_order - current_order
        ordering_dict[node_tuple] = updated_order
    return 



# _get_names_of_internal_nodes(host_tree) will return [m0, m2]
#  _get_names_of_internal_nodes(parasite_tree) will return [n0, n2]

def _get_names_of_internal_nodes(tree):
    """
    :param: A host or parasite tree
    :return: A list of the names (strings) of the internal nodes in that tree
    """
    node_names = list()
    for edge_name in tree:
        edge_four_tuple = tree[edge_name]
        if not _is_leaf_edge(edge_four_tuple):
            node_names.append(_bottom_node(edge_four_tuple))
    return node_names

def _top_node(edge_four_tuple):
    """
    :param: 4-tuple of the form (top_vertex_name, bottom_vertex_name, child_edge1, child_edge2)
    :return: top_vertex_name
    """
    return edge_four_tuple[0]

def _bottom_node(edge_four_tuple):
    """
    :param: 4-tuple of the form (top_vertex_name, bottom_vertex_name, child_edge1, child_edge2)
    :return: bottom_vertex_name
    """
    return edge_four_tuple[1]

def _is_leaf_edge(edge_four_tuple):
    """
    :param: 4-tuple of the form (top_vertex_name, bottom_vertex_name, child_edge1, child_edge2)
    :return: True if child_edge1 = child_edge2 = None.
        This signifies that this edge terminates at a leaf. 
    """
    return edge_four_tuple[3] == None

          

# T = build_temporal_graph(host_tree, parasite_tree, reconciliation)
# ordering_dict = topological_order(T)
# print (ordering_dict)

