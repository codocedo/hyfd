'''
Converts a Canonical Cover to a Minimal Cover
'''

import sys
import json
from itertools import chain

from collections import defaultdict

def l_close(L, new_closure):
    '''
    Lin Closure
    '''
    
    fd_index = defaultdict(list)
    counts = {}

    for ri, (A,B) in enumerate(L):
        counts[ri] = len(A)
        for m in A:
            fd_index[m].append(ri)

    update = list(new_closure)
    
    while update:
        m = update.pop()
        for i in fd_index[m]:
            imp = L[i]
            counts[i] -= 1
            if counts[i] == 0:
                add = imp[1] - new_closure
                new_closure |= imp[1]
                update.extend(add)
    return new_closure

def derive_iteration_free(L, X):
    for A, B in L:
        if A.issubset(X):
            X.update(B)
    return X


def derive_full(L, X):
    old_x = None
    while X != old_x:
        old_x = set([i for i in X])
        for A, B in L:
            if A.issubset(X):
                X.update(B)
    return X

def minimal_cover(L):
    remove = []

    for ri in range(len(L)):
        L[ri][1].update(L[ri][0])
    remove = []
    for ri, (A,B) in enumerate(L):
        # fds.del_fd(A,B)
        L[ri] = (set([]), set([]))
#        print(A)
        # A = derive_full(L, A)
        # print A,
        l_close(L, A)
#        print '\t->'+str(A)
        
        if not B.issubset(A):
            L[ri] = (A, B-A)
            # fds.add_fd(A, B-A)
        else:
            remove.append(ri)
    for ri in reversed(remove):
        del L[ri]
    return L

def read_rules(path):
    with open(path, 'r') as fin:
        # return [(set(ant), set(con)) for ant, con in json.load(fin)]
        return [(set(ant), set(con)) for ant, con in json.load(fin)]

if __name__ == "__main__":
    L = read_rules(sys.argv[1])
    # for i,j  in enumerate(L):
    #     print i+1, j
    mincov = minimal_cover(L)
    
    fout_path = sys.argv[1].replace('.json', '.mincov.json')
    print ("Canonical Cover Size: {} FDs".format(len(L)))
    print ("Minimal Cover Size: {} FDs".format(len(mincov)))
    mincov = [(sorted(A), sorted(B)) for A,B in mincov]
    with open(fout_path, 'w') as fout:
        json.dump(list(mincov), fout)
        print("FDs written in:{}".format(fout_path))
