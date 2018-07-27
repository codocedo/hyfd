import logging

logger = logging.getLogger(__name__)

class FDNode(object):
    def __init__(self, att=-1, n_atts=0):
        self.att = att
        # self.idx = [True]*n_atts
        self.link = {}
        self.parent = None
        self.rhs=[False]*n_atts
    
    def get_children(self):
        for i in sorted(self.link.keys()):
            yield self.link[i]

    def invalidate(self, invalid_rhss):
        for i in invalid_rhss:
            self.rhs[i] = False

    def __repr__(self):
        return str("<FDNode>{}=>{}".format(self.get_lhs(), str(self.get_rhss())))

    def get_rhss(self):
        return [i for i, j in enumerate(self.rhs) if j]

    def get_lhs(self):
        base = set([self.att])
        parent = self.parent
        while parent is not None:
            if parent.att>=0:
                base.add(parent.att)
            parent = parent.parent
        return base

    def flip(self):
        for i in range(len(self.rhs)):
            self.rhs[i] = not self.rhs[i]

    def add_child(self, child):
        # self.idx[child.att] = False
        self.link[child.att] = child
        child.parent = self


class FDTree(object):
    def __init__(self, n_atts=0):
        self.n_atts = n_atts
        self.root = FDNode(n_atts=self.n_atts)

    def level_and_recurse(self, current_node, sought_depth, depth=0):
        if sought_depth==depth:
            yield current_node
        else:
            for att in sorted(current_node.link.keys()):
                for i in self.level_and_recurse(current_node.link[att], sought_depth, depth+1):
                    yield i

    def get_level(self, sought_depth):
        for i in self.level_and_recurse(self.root, sought_depth):
            yield i

    def print_and_recurse(self, current_node, depth=1):
        # print ("\t"*depth, current_node.att)
        # print ("\t"*depth, current_node.link.keys())
        # print ("\t"*depth, current_node.rhs)
        for i in sorted(current_node.link.keys()):
            self.print_and_recurse(current_node.link[i], depth+1)

    def print_tree(self):
        self.print_and_recurse(self.root)
    
    def find_fd(self, lhs, rhs):
        current_node = self.root
        s_lhs = sorted(lhs, reverse=True)
        while bool(s_lhs):
            next_att = s_lhs.pop()
            if current_node.link.get(next_att, False):
                current_node = current_node.link[next_att]
            else:
                return False
        return current_node.rhs[rhs]

    def add(self, lhs, rhss):
        """
        rhss contains a list of attributes
        """
        # logger.debug("ADD FD: {}=>{}".format(lhs, rhss))
        # print ()
        new_node = None
        current_node = self.root
        s_lhs = sorted(lhs,reverse=True)
        while bool(s_lhs):
            next_att = s_lhs.pop()
            add = True
            if current_node.link.get(next_att, False):
                current_node = current_node.link[next_att]
            else:
                new_node = FDNode(att=next_att, n_atts=self.n_atts)
                current_node.add_child(new_node)
                current_node = new_node
        for rhs in rhss:
            current_node.rhs[rhs] = True
        return new_node

    # def add_and_get_if_new(self, lhs, rhss):
    #     """
    #     rhss contains a list of attributes
    #     """
    #     current_node = self.root
    #     s_lhs = sorted(lhs,reverse=True)
    #     new_node = None
    #     while bool(s_lhs):
    #         next_att = s_lhs.pop()
    #         if current_node.link.get(next_att, False):
    #             current_node = current_node.link[next_att]
    #         else:
    #             new_node = FDNode(att=next_att, n_atts=self.n_atts)
    #             current_node.add_child(new_node)
    #             current_node = new_node
    #     for rhs in rhss:
    #         current_node.rhs[rhs] = True
    #     return new_node
        

    def read_and_recurse(self, current_node, base):
        for i, rhs in enumerate(current_node.rhs):
            if rhs:
                yield (base, i)
        for att in sorted(current_node.link.keys()):
            next_node = current_node.link[att]
            for i in self.read_and_recurse(next_node, base.union([att])):
                yield i
            

    def read_fds(self):
        # print ("READING")
        current_node = self.root
        base = set([])
        for i in self.read_and_recurse(current_node, base):
            yield i

    def check_and_recurse(self, current_node, base, lhs, rhs):
        # print ('\t CHECK_AND_RECURSE:', current_node.att, base, lhs, rhs)
        if base.issubset(lhs) and current_node.rhs[rhs]:
            yield (base, rhs)
        for att in sorted(current_node.link.keys()):
            if att in lhs:
                next_node = current_node.link[att]
                for i in self.check_and_recurse(next_node, base.union([att]), lhs, rhs):
                    yield i
            elif att > max(lhs):
                break
        
    def fd_has_generals(self, lhs, rhs):
        """
        rhs contains a single attribute
        """
        # print ("FD_HAS_GENERALS:", "{}=>{}".format(lhs, rhs))
        base = set([])
        result = False
        for old_lhs, old_rhs in self.check_and_recurse(self.root, base, lhs, rhs):
            result = True
            break
        # print ("FD_HAS_GENERALS:", result, [i for i in self.read_fds()])
        # print(result)
        return result

    def get_fd_and_generals(self, lhs, rhs):
        # print (self.fds)
        # print ("FD_GET_GENERALS:", lhs, rhs)
        base = set([])
        for old_lhs, old_rhs in self.check_and_recurse(self.root, base, lhs, rhs):
            # print ("FD_GET_GENERALS:",  "{}=>{}".format(lhs, rhs), "{}=>{}".format(old_lhs, old_rhs))
            # print ('RETURN', old_lhs, old_rhs)
            yield old_lhs

    def remove(self, lhs, rhs):
        # print ("REMOVE:", lhs, rhs)
        # print ([i for i in self.read_fds()])
        current_node = self.root
        s_lhs = sorted(lhs,reverse=True)
        while bool(s_lhs):
            next_att = s_lhs.pop()
            if current_node.link.get(next_att, False):
                current_node = current_node.link[next_att]
            else:
                raise KeyError
        
        current_node.rhs[rhs] = False
        # print ([i for i in self.read_fds()])

# class FDTree(object):
#     def __init__(self, n_atts):
#         self.fds = {}
#     def add(self, lhs, rhs):
#         for x in rhs:
#             self.fds.setdefault(x, []).append(set(lhs))
#     def fd_has_generals(self, lhs, rhs):
#         if rhs not in self.fds:
#             return False
#         for o_lhs in self.fds.get(rhs, []):
#             if o_lhs.issubset(lhs):
#                 return True
#         return False
#     def get_fd_and_generals(self, lhs, rhs):
#         # print (self.fds)
#         for o_lhs in self.fds.get(rhs, []):
#             if o_lhs.issubset(lhs):
#                 yield o_lhs
#     def read_fds(self):
#         return self.fds.items()
#     def remove(self, lhs, rhs):
#         lhss = self.fds.get(rhs, [])
#         if lhs in lhss:
#             # print (lhss)
#             del lhss[lhss.index(lhs)]
#             # print (lhss)
#             return True
#         else:
#             return False
