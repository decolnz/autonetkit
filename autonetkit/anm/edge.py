import logging
from functools import total_ordering

import autonetkit
import autonetkit.log as log
from autonetkit.anm.interface import NmPort
from autonetkit.anm.node import NmNode
from autonetkit.log import CustomAdapter

from autonetkit.anm.ank_element import AnkElement

@total_ordering
class NmEdge(AnkElement):

    """API to access link in network"""

    def __init__(self, anm, overlay_id, src_id, dst_id, ekey=0):

        self.anm = anm
        self.overlay_id = overlay_id
        self.src_id = src_id
        self.dst_id = dst_id
        self.ekey = ekey  # for multigraphs
        #logger = logging.getLogger("ANK")
        #logstring = "Interface: %s" % str(self)
        #logger = CustomAdapter(logger, {'item': logstring})
        logger = log
        self.log = logger
        self.init_logging("edge")


    def __key(self):
        """Note: key doesn't include overlay_id to allow fast cross-layer comparisons"""

        # based on http://stackoverflow.com/q/2909106

        return (self.src_id, self.dst_id)

    def __hash__(self):
        """Return a hash of a key"""
        return hash(self.__key())

    def is_multigraph(self):
        """Returns graph that is multigraph"""
        return self._graph.is_multigraph()

    def is_parallel(self):
        """If there is more than one edge between the src, dst of this edge"""
        # TODO: check this for digraph, multiidigraph
        return self._overlay().number_of_edges(self.src, self.dst) > 1

    def __eq__(self, other):
        if self.is_multigraph():
            try:
                if other.is_multigraph():
                    return (self.src_id, self.dst_id, self.ekey) == (other.src_id,
                                                                     other.dst_id, other.ekey)
                else:
                    # multi, single
                    return (self.src_id, self.dst_id) == (other.src_id,
                                                          other.dst_id)

            except AttributeError:
                if len(other) == 2:
                    # (src, dst)
                    return (self.src_id, self.dst_id) == other
                elif len(other) == 3:
                    # (src, dst, key)
                    return (self.src_id, self.dst_id, self.ekey) == other

        try:
            # self is single, other is single or multi -> only compare (src,
            # dst)
            return (self.src_id, self.dst_id) == (other.src_id, other.dst_id)
        except AttributeError:
            # compare to strings
            return (self.src_id, self.dst_id) == other

    def __repr__(self):
        """String of node"""
        if self.is_multigraph():
            return '(%s, %s, %s)' % (self.src,
                                         self.dst, self.ekey)

        return '(%s, %s)' % (self.src, self.dst)

    def __getitem__(self, key):
        """"""
        from autonetkit.anm.graph import NmGraph
        overlay = NmGraph(self.anm, key)
        return overlay.edge(self)

    def _overlay(self):
        """Return overlay and overlayid"""
        from autonetkit.anm import NmGraph
        return NmGraph(self.anm, self.overlay_id)

    def __lt__(self, other):
        """Comparison operator"""
        if self.is_multigraph() and other.is_multigraph():
            return (self.src.node_id, self.dst.node_id, self.ekey) \
                < (other.src.node_id, other.dst.node_id, other.ekey)

        return (self.src.node_id, self.dst.node_id) \
            < (other.src.node_id, other.dst.node_id)

    # Internal properties
    def __nonzero__(self):
        """Allows for checking if edge exists"""
        if self.is_multigraph():
            return self._graph.has_edge(self.src_id, self.dst_id, key=self.ekey)
        return self._graph.has_edge(self.src_id, self.dst_id)

    @property
    def raw_interfaces(self):
        """Direct access to the interfaces dictionary, used by ANK modules"""
        return self.get('_ports')

    @raw_interfaces.setter
    def raw_interfaces(self, value):
        self.set('_ports', value)

    @property
    def _graph(self):
        """Return graph the edge belongs to"""

        return self.anm.overlay_nx_graphs[self.overlay_id]

    @property
    def _data(self):
        """Return data the edge belongs to"""
        if self.is_multigraph():
            return self._graph[self.src_id][self.dst_id][self.ekey]

        return self._graph[self.src_id][self.dst_id]

    # Nodes

    @property
    def src(self):
        """Source node of edge"""

        return NmNode(self.anm, self.overlay_id, self.src_id)

    @property
    def dst(self):
        """Destination node of edge"""

        return NmNode(self.anm, self.overlay_id, self.dst_id)

    # Interfaces

    def apply_to_interfaces(self, attribute):
        """"Applying and setting various attributes to interfaces"""

        val = self.get(attribute)
        self.src_int.set(attribute, val)
        self.dst_int.set(attribute, val)

    @property
    def src_int(self):
        """Interface bound to source node of edge"""

        src_int_id = self.get('_ports')[self.src_id]
        return NmPort(self.anm, self.overlay_id,
                      self.src_id, src_int_id)

    @property
    def dst_int(self):
        """Interface bound to destination node of edge"""

        dst_int_id = self.get('_ports')[self.dst_id]
        return NmPort(self.anm, self.overlay_id,
                      self.dst_id, dst_int_id)

    def bind_interface(self, node, interface):
        """Bind this edge to specified index"""

        self._ports[node.id] = interface

    def interfaces(self):
        """Returning interfaces"""

        # TODO: warn if interface doesn't exist on node

        return [NmPort(self.anm, self.overlay_id,
                       node_id, interface_id) for (node_id,
                                                   interface_id) in self.get('_ports').items()]

    #

    def dump(self):
        """Returns dump data
        """
        return str(self._graph[self.src_id][self.dst_id])

    def get(self, key):
        """For consistency, edge.get(key) is neater than getattr(edge, key)
        """
        if hasattr(self,key):
            return getattr(self, key)

        return self._data.get(key)

    def set(self, key, val):
        """For consistency, edge.set(key, value) is neater than
        setattr(edge, key, value)
        """

        if key == 'raw_interfaces':
            self.raw_interfaces = val

        self._data[key] = val
