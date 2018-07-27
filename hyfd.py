"""
HyFd as described in Papenbrock et al - A Hybrid Approach to Functional Dependency Discovery (2016)

"""
from __future__ import print_function

import sys
import logging
from hyfd_libs.fd_tree import FDTree
from hyfd_libs.pli import PLI
from hyfd_libs.efficiency import Efficiency
from hyfd_libs.boolean_tree import BooleanTree

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"

logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

INVALID_FDS_THRESHOLD = 0.01



def read_csv(path, separator=','):
    """
    READ CSV
    """
    mat = [list(map(str, line.replace('\n','').split(separator))) for line in open(path, 'r').readlines()]
    return mat

def build_pli(lst):
    hashes = {}
    #print list(enumerate(lst))
    for i, j in enumerate(lst):
        hashes.setdefault(j, set([])).add(i)
    return sorted([sorted(i) for i in hashes.values() if len(i) > 1], key = lambda k: len(k), reverse=True)

def transpose(lst, n_rows):
    return [[row[j] for row in lst] for j in range(n_rows)]


class HyFd(object):
    def __init__(self, path):
        self.natts = 0
        self.nrecs = 0
        self.records = read_csv(sys.argv[1])
        self.att_order_map = []
        self.non_fds = None
        self.fds = None
        self.current_level = None
        self.current_level_number = None
        self.plis = None
        self.pli_records = None
        self.comparison_suggestions = []
        self.efficiency_queue = []
        self.efficiency_threshold = 0.4
        self.go_on = True

        self.execute()
        
        print ({i:j.att for i, j in enumerate(self.plis)})
        self.print_records()
        print ("\nRESULTS")
        for ri, (lhs, rhs) in enumerate(self.fds.read_fds()):
            # print (lhs, rhs)
            print (ri+1, [self.plis[i].att for i in lhs], '=>', self.plis[rhs].att)


    def execute(self):
        self.preproc()
        while self.go_on:
        # for i in range(2):
            self.sampling()
            self.induction()
            self.validation()
            # self.go_on = False


    def print_records(self):
        for ri, record in enumerate(self.pli_records):
            print ("\t"+str(ri)+':'+'|'.join(str(i) if i >= 0 else 'X' for i in record))
        
    def preproc(self):#, records):
        """
        PREPROC as described in algorithm 1 in [1]
        """
        self.nrecs = len(self.records)
        self.natts = len(self.records[0])
        PLI._nrecs = self.nrecs

        # INVERT TABLE RECORDS
        self.plis = [PLI(pi, build_pli(i)) for pi, i in enumerate(transpose(self.records, self.natts))]
        
        self.plis.sort(key=lambda x: x.number_of_parts, reverse=True)
        
        self.pli_records = []
        for pli in self.plis:
            col = [-1] * self.nrecs
            for cluster_id, cluster in enumerate(pli):
                for row in cluster:
                    col[row] = cluster_id
            self.pli_records.append(col)
        self.pli_records = transpose(self.pli_records, self.nrecs)


    def sampling(self):
        logger.debug("SAMPLING WITH EFF_QUEUE:{}".format(self.efficiency_queue))
        # efficiency_queue = []

        if not bool(self.efficiency_queue):
            # self.non_fds = set([])
            self.non_fds = BooleanTree()
            for x, pli in enumerate(self.plis):
                ileft = x-1
                iright = x+1 if x+1 < self.natts else 0
                for cluster_id in range(len(pli)):
                    pli[cluster_id].sort( key=lambda k: self.pli_records[k][ileft] if self.pli_records[k][ileft] >= 0 else self.pli_records[k][iright] )

            for x in range(self.natts):
                efficiency = Efficiency(att=x, pli=self.plis[x])
                run_window(efficiency, self.plis[x], self.pli_records, self.non_fds)
                self.efficiency_queue.append(efficiency)
        else:
            self.efficiency_threshold /= 2
            
            for sug in self.comparison_suggestions:
                self.non_fds.append(match(self.pli_records[sug[0]], self.pli_records[sug[1]]))
        
        while True:
            logger.debug("\tEFFICIENCY QUEUE:{}".format(self.efficiency_queue))
            self.efficiency_queue.sort(key=lambda k: k.eval(), reverse=True)
            best_eff = self.efficiency_queue[0]
            
            if best_eff.eval() < self.efficiency_threshold:
                logger.debug("Out by low efficiency")
                break
            best_eff.window += 1
            run_window(best_eff, self.plis[best_eff.att], self.pli_records, self.non_fds)
            
            if best_eff.done:
                del self.efficiency_queue[0]
            if not bool(self.efficiency_queue):
                logger.debug("Out by no candidates")
                self.go_on = False
                break
    
    def induction(self):
        logger.debug("INDUCTION")
        logger.debug("\tNON_FDS:{}:".format(self.non_fds))
        
        if self.fds is None:
            self.fds = FDTree(n_atts=self.natts)
            self.fds.add([], list(range(self.natts)))

        for lhs in self.non_fds:
            for rhs in [j for j, v in enumerate(lhs) if not v]:
                nodes = list(self.specialize(self.fds, [j for j, v in enumerate(lhs) if v], rhs))
        self.non_fd_pointer = len(self.non_fds)
        return self.fds

    def specialize(self, fds, lhs, rhs):
        '''
        SPECIALIZES THE FDTREE WITH AN INVALID FD lhs => rhs
        YIELDS THE NODES CREATED IN THE FDTREE
        '''
        logger.debug('SPECIALIZE: {}=>{}'.format(lhs, rhs))
        invalid_lhss = list(fds.get_fd_and_generals(lhs, rhs))
        for invalid_lhs in invalid_lhss:
            self.fds.remove(invalid_lhs, rhs)
            for x in range(self.natts):
                if x in invalid_lhs or rhs == x:
                    continue
                new_lhs = invalid_lhs.union([x])
                if new_lhs.issubset(set(lhs)):
                    continue
                if self.fds.fd_has_generals(new_lhs, rhs):
                    continue
                yield self.fds.add(new_lhs, [rhs])

    def refines(self, lhs, rhss):
        '''
        REFINES THE FD BY CHECKING IF THE LHS => RHS FOR EACH RHS IN RHSS
        The implementation of this function is not described in [1], but a 
        description of its functioning is provided.

        This is an interpretation of its description.

        @returns ALL RHS IN RHSS SUCH THAT LHS => RHS IS VALID, IF NONE ARE VALID THEN RETURNS []
        '''
        logger.debug('REFINE FD {}=>{}'.format(lhs, rhss))

        # for ri, record in enumerate(self.pli_records):
        #     logger.debug(str(ri)+':'+'|'.join(str(i) if i >= 0 else 'X' for i in record))
        if not bool(rhss):
            return []
        '''
        mask maintains the indices of RHSS that are still valid
        the function returns when mask is empty.
        '''
        mask = list(range(len(rhss))) 

        s_lhs = sorted(lhs)
        
        clusters = self.plis[s_lhs[0]]
        # logger.debug(clusters)
        # logger.debug([[(i, tuple([self.pli_records[i][x] for x in s_lhs+rhss])) for i in cluster] for cluster in self.plis[s_lhs[0]]])
        signatures = (( (i, [self.pli_records[i][x] for x in s_lhs+rhss]) for i in cluster) for cluster in clusters)
        
        mapping = {}
        for cluster_encoding in signatures:
            
            cluster_encoding = list(cluster_encoding)
            # print ('\t\t\t CLUSTER_ENCODING', list(cluster_encoding))
            # logger.debug("CLUSTER_ENCODING:{}".format(cluster_encoding))
            for ti, row_map in cluster_encoding:
                '''
                row_map has the signature created for the LHS and the RHSS for each attribute
                ti is the row number.
                For example, given a,b=>c we can have:
                ti, row_map = (0, [1,1,0]) 
                meaning that for row 0, columns a,b have values 1,1 and column c has value 0.
                row_map is decoded in two signatures, s1 and s2.
                signature s1 is mapped to signature s2.
                if the map of s1 exists and is not s2, then we have that at least one element in the RHSS
                should be removed from mask.
                '''
                # logger.debug("\t ti:{}|row_map:{}".format(ti, row_map))
                s1, s2 = tuple(row_map[:len(s_lhs)]), tuple(row_map[len(s_lhs):])
                '''
                If -1 is in the signature s1, then it is a singleton and should not be checked.
                '''
                if -1 in s1:
                    continue
                
                if not mapping.get(s1, False): # THE SIGNATURE S1 IS NOT MAPPED, DO IT
                    mapping[s1] = {
                        'ti':[ti],
                        's':s2
                    }
                else: # THERE IS A MAPPING FOR SIGNATURE S1
                    s3 = mapping[s1]['s'] # GET IT
                    # AND CHECK IT AGAINST S2
                    diff = [i for i in mask if s2[i] == -1 or s2[i] != s3[i]]
                    '''
                    Consider the FD a=>b,c,d and that s1 is already mapped to -1 2 1
                    and s2 is 1 2 -1. 
                    We can see that for tuple ti, the values of columns b and d do not
                    coincide to the previous mapping and they should be removed from mask.
                    '''
                    if bool(diff):
                        
                        for tj in mapping[s1]['ti']:
                            # print ("++++", ti, tj)
                            self.comparison_suggestions.append((tj, ti))
                        for i in diff:
                            mask.remove(i)
                    else:
                        mapping[s1]['ti'].append(ti)

                if not bool(mask):
                    break

            if not bool(mask):
                    break

        result = [rhss[i] for i in mask]

        return result
    
    def validation(self):
        logger.debug("VALIDATION")
        logger.debug(list(self.fds.read_fds()))
        # Data: fds, plis, plis_records
        # Result: fds, comparison_suggestions
        # print ("**", "VALIDATION", "**"*10)
        
        if self.current_level is None:
            self.current_level_number = 0
        
        self.current_level = list(self.fds.get_level(self.current_level_number))
        

        comparison_suggestions = []
        while bool(self.current_level):
            # print ("\tCURRENT_LEVEL_NUMBER: ", self.current_level_number)
            # print ("\tCURRENT_LEVEL: ", self.current_level)
            # VALIDATE ALL FDS ON CURRENT LEVEL
            invalid_fds = []
            num_valid_fds = 0
            for node in self.current_level:
                lhs = node.get_lhs()
                rhss = node.get_rhss()
                
                valid_rhss = self.refines(lhs, rhss)#, plis, pliRecords, comparisonSuggestions);
                # print ("\tTesting FD: ", lhs, rhss)
                num_valid_fds += len(valid_rhss)
                invalid_rhss = [i for i in rhss if i not in valid_rhss]
                logger.debug("\tInvalid attributes in RHS:{}".format( invalid_rhss))
                # node.invalidate(invalid_rhss)
                for invalid_rhs in invalid_rhss:
                    invalid_fds.append( (lhs, invalid_rhs) )
                # print (list(self.fds.read_fds()))

            # ADD ALL CHILDREN TO THE NEXT LEVEL
            next_level = []

            for node in self.current_level:
                for child in node.get_children():
                    next_level.append(child)

            # SPECIALIZE ALL INVALID FDs
            # print ("\tSPECIALIZING INVALIDS: ", invalid_fds, "||", list(self.fds.read_fds()))
            for invalid_fd in invalid_fds:
                lhs, rhs = invalid_fd
                for node in self.specialize(self.fds, lhs, rhs):
                    if node is not None:
                        next_level.append(node)
                

            self.current_level = next_level
            self.current_level_number += 1
            # JUDGE EFFICIENCY OF VALIDATION PROCESS
            if len(invalid_fds) > INVALID_FDS_THRESHOLD * num_valid_fds:
                # print ("EXITING WITH N_INVALID_FDS:{} > {}, N_VALID_FDS:{}".format(len(invalid_fds), INVALID_FDS_THRESHOLD * num_valid_fds, num_valid_fds))
                # print ("FINAL FDS", list(self.fds.read_fds()))
                return self.fds, comparison_suggestions
        # print ("FINAL FDS", list(self.fds.read_fds()))
        return self.fds, set([])
            # break
        



def run_window(efficiency, pli, pli_records, non_fds):
    logger.debug("\tRUN:{} window::{}".format(pli,efficiency.window ))
    # print ("\tRUN:", pli, 'window::',efficiency.window )
    prev_num_non_fds = len(non_fds)
    for cluster in pli:
        # print ('\t\t:: CLUSTER:',cluster, '|', range(len(cluster)-efficiency.window+1))
        for i in range(len(cluster)-efficiency.window+1):
            logger.debug('\t\t Comparing tuples {} - {}'.format(cluster[i],cluster[i+efficiency.window-1]))
            # # print ('\t\t\t->',)
            pivot = pli_records[cluster[i]]
            partner = pli_records[cluster[i+efficiency.window-1]]
            compare = match(pivot, partner)
            logger.debug('\t\t\tResult:{} || New?:{}'.format( compare, compare not in non_fds))
            if not all(compare):
                non_fds.append(compare)
            efficiency.increase_comps()
    efficiency.results += len(non_fds) - prev_num_non_fds

def match(row1, row2):
    return tuple([i==j and i>-1 for i, j in zip(row1, row2)])


if __name__ == "__main__":
    HyFd(sys.argv[1])



'''
EXTRACTED FROM VALIDATION
                # for x in range(self.natts):
                #     if x in lhs or rhs == x or self.fds.fd_has_generals(lhs, x) or self.fds.find_fd([x], rhs):
                #         continue
                #     new_lhs = lhs.union([x])
                #     if new_lhs.issubset(set(lhs)):
                #         # print ('r')
                #         continue
                #     if self.fds.fd_has_generals(new_lhs, rhs):
                #         # print ('x', list(self.fds.get_fd_and_generals(new_lhs, rhs)))
                #         continue
                #     child = self.fds.add(new_lhs, [rhs])
                #     if child is not None:
                #         next_level.append(child)
'''