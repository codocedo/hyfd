'''
Converts a Canonical Cover to a Minimal Cover
'''

import sys
import json

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
    for ri, rule in enumerate(L):
        A, B = rule
        L[ri] = (set([]), set([]))
        #print ('{}->{}'.format(A,B))
        
        B = derive_iteration_free(L, A.union(B))
        #print ('\t->'+str(B))
        add = True
        for rule2 in L:
            if (A, B) == rule2:
                add = False
        if add:
            L[ri] = (A, B)
        else:
            remove.append(ri)
    for i in sorted(remove, reverse=True):
        del L[i]
    #L = [rule for rule in L if bool(rule[0])]
    #L = sorted(L, key=lambda s: (len(s[0]), sorted(s[1])), reverse=True)
    #L = sorted(L, key=lambda s: (sorted(s[0]), sorted(s[1])))
    remove = []
    for ri, rule in enumerate(L):
        A, B = rule
        L[ri] = (set([]), set([]))
#        print(A)
        A = derive_full(L, A)
#        print '\t->'+str(A)
        if A != B:
            L[ri] = (A, B-A)
        else:
            remove.append(ri)
    for i in sorted(remove, reverse=True):
        del L[i]
    return L

def read_rules(path):
    with open(path, 'r') as fin:
        return [(set(ant), set([con])) for ant, con in json.load(fin)]
        # return [(set(ant), set([con])) for ant, con in json.load(fin)]

if __name__ == "__main__":
    L = read_rules(sys.argv[1])
    print len(L)
    print len(minimal_cover(L))
