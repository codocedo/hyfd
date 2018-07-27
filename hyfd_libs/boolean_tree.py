class BooleanTree(object):
    '''
    BooleanTree that maintains a list of boolean array lists
    The leaf can be either None, False or True.
    None, means that no element has been stored in that position.
    False and True indicates whether the element stored in that position has been read.
    Elements are stored in lists of two elements, element 0 is for False, element 1 is for True.
    self.root = [None, [[None, False], [True, None]]]
    means the lists [True, False, True] and [True, True, False] are stored.
    The first one has not been read, the second one has been read already.
    '''
    def __init__(self):
        self.root = [None, None]
        self.n_elements = 0

    def append(self, lst):
        '''
        Insert the list of booleans elements in the Tree
        '''
        current_node = self.root
        for i in lst:
            idx = 0 if not i else 1
            if current_node[idx] is not None:
                current_node = current_node[idx]
            else:
                current_node[idx] = [None, None]
                current_node = current_node[idx]
        if current_node == [None, None]:
            while bool(current_node):
                current_node.pop()
            current_node.append(False)
            self.n_elements += 1

    def recursive_read(self, current_node, prefix, single_read=False):
        '''
        Recursively read the elements in the Tree.
        If single_read is False, all elements are returned.
        If single_read is True, only elements that have not been read are returned.
        '''
        if len(current_node) == 1:
            if single_read:
                if not current_node[0]:
                    current_node[0] = True
                    yield prefix
            else:
                yield prefix
        else:
            for i in range(2):
                if current_node[i] is not None:
                    for j in self.recursive_read(current_node[i], prefix+[i==1], single_read):
                        yield j

    def read(self, single_read=False):
        '''
        Start the recursion to get all elements in the Tree.
        If single_read is False, all elements are returned.
        If single_read is True, only elements that have not been read are returned.
        '''
        for i in self.recursive_read(self.root, [], single_read):
            yield i

    def __iter__(self):
        '''
        Read elements in the Tree that have not been read before
        '''
        for i in self.read(single_read=True):
            yield i

    def __contains__(self, lst):
        current_node = self.root
        for i in lst:
            if current_node[i] is None:
                return False
            current_node = current_node[i]
        return True
    def __len__(self):
        return self.n_elements
    def __repr__(self):
        return "<BooleanTree>::{}".format(list(self.read(single_read=False)))

    


if __name__ == "__main__":
    bt = BooleanTree()
    lsts = [(True, False, True, False), (False, True, False, True), (False, True, False, True), (False, False, True, True), (True, False, True, False), (False, False, True, True), (False, False, False, True), (False, True, False, True), (False, True, False, True)]
    for lst in lsts:
        # print "{} in BooleanTree?:{}".format(lst, lst in bt)
        bt.append(lst)
        # print "{} in BooleanTree?:{}".format(lst, lst in bt)
    print "Return all elements:", list(bt.read(single_read=True))
    print "Should not return any element:", list(bt.read(single_read=True))
    bt.append((False, True, False, True))
    print "Should not return any element:", list(bt.read(single_read=True))

    new_lst1 = (True, True, False, True)
    print "{} in BooleanTree?:{}".format(new_lst1, new_lst1 in bt)
    print "Insert {} in BooleanTree".format(new_lst1)
    bt.append(new_lst1)
    print "{} in BooleanTree?:{}".format(new_lst1, new_lst1 in bt)
    bt.append((True, True, True, True))
    print "Return Two Elements:", list([i for i in bt]) # Should return only the previous two elements. Same as print list(bt.read(single_read=True)) 
    print "Return all elements:", list(bt.read(single_read=False)) # should return all elements
    
    # print sorted(set(lsts))