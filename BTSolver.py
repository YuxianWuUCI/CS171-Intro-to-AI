import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: true is assignment is consistent, false otherwise
    """
    def forwardChecking ( self ):
        """
            Put a trailmarker in case the new assigned variable makes the network unconsistent
            Then the program need to restore all neighbours which have value deleted before
            
            This function uses the trail of the class instead of creating a new one in function.
            The reason is that once the new variable does not make the network unconsistent so
            the forward checking would return True but there is no solution for sudoku after assigning
            this value to this variable.
            
            In this case, the program need go back to status before the variable was assigned
            and the domain of its neighbor should be restored. A local trail can not restore
            the neighbor, so we need to use the trail which the class already has.
        """
        self.trail.placeTrailMarker()           #use the trail from class
        v_assign = []
        for v in self.network.variables:
            #if the variable is assigned and modified, check its neighbors
            #use modified to check whether this assigned variable has already been forward checked in previou
            if v.isAssigned() and v.isModified():
                
                #document the variables which have been forward checked
                v_assign.append(v)
                for v_neigh in self.network.getNeighborsOfVariable(v):
                    
                    #only push the neighbour which contains the value of v
                    if v_neigh.domain.contains(v.getAssignment()):
                        self.trail.push( v_neigh )
                        #remove the same value which v is assigned
                        v_neigh.removeValueFromDomain(v.getAssignment())
                    #this means the network is inconsistent and should backtrack
                    if v_neigh.domain.isEmpty():
                        
                        #before making undo. restore all the assigned variables' "modified"
                        for v_s in v_assign:
                            v_s.setModified(True)
                        self.trail.undo()
                        return False
                v.setModified( False )
        #delete the trailmarker we made in the begining of the function
        #so that once the trail implement undo() out of this function,
        #the status won't go back to here
        self.trail.trailMarker.pop()
        return True

    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: true is assignment is consistent, false otherwise
    """
    def norvigCheck ( self ):
        self.trail.placeTrailMarker()           #use the trail from class
        v_assign = []
        v_change = set()
        for v in self.network.variables:
            #if the variable is assigned and modified, check its neighbors
            #use modified to check whether this assigned variable has already been forward checked in previou
            if v.isAssigned() and v.isModified():
                
                #document the variables which have been forward checked
                v_assign.append(v)
                
                #document the varaibles whose domain has been changed during the forward check
                v_change.add(v)
                for v_neigh in self.network.getNeighborsOfVariable(v):
                    
                    #only push the neighbour which contains the value of v
                    #otherwise if the assigned variable A is one of v's neighbors,
                    #A will be added to trail and its Modified attribute will be set to False once the trail undo
                    if v_neigh.domain.contains(v.getAssignment()):
                        self.trail.push( v_neigh )
                        v_change.add(v_neigh)
                        #remove the same value which v is assigned
                        v_neigh.removeValueFromDomain(v.getAssignment())
                    #this means the network is inconsistent and should backtrack
                    if v_neigh.domain.isEmpty():
                        for v_s in v_assign:
                            v_s.setModified(True)
                        self.trail.undo()
                        return False
                v.setModified( False )
        
        # the part above is same as forward checking
        # now implement the second rule
        
        for v_s in v_change:
            for c in self.network.getConstraints():
                #if this constraint contains the variables which have been assigned in the first half part
                #there are three constraints which have v_s
                if(c.contains(v_s)):
                    #after forward checking, neighbours of v_s may satisfy the second rule
                    for value in range(1,self.gameboard.N):
                        #count all the variables that have this value in their domain
                        va_place = [v for v in c.vars if v.domain.contains(value)]
                        if len(va_place) == 0:
                            for v in v_assign:
                                v.setModified(True)
                            self.trail.undo()
                            return False
                        elif len(va_place) == 1:
                            self.trail.push(va_place[0])
                            va_place[0].assignValue(value)

        self.trail.trailMarker.pop()
        return True

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return None

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        min=self.gameboard.N
        for v in self.network.variables:
            if v.size() < min and not v.isAssigned():
                min=v.size()
        for v in self.network.variables:
            if v.size()==min:
                return v
        return None
    """
        Part 2 TODO: Implement the Degree Heuristic

        Return: The unassigned variable with the most unassigned neighbors
    """
    def getDegree ( self ):
        max = -1 #initialize
        max_v = self.getfirstUnassignedVariable()
        for v in self.network.variables:
            counter = 0 #used to count the degree of variable
            if not v.isAssigned():
                for v_neigh in self.network.getNeighborsOfVariable(v): #count the degree
                    if not v_neigh.isAssigned():
                        counter = counter +1
                if counter > max:
                    max = counter
                    max_v = v
        if max == -1:
            return None
        return max_v

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with, first, the smallest domain
                and, second, the most unassigned neighbors
    """
    def MRVwithTieBreaker ( self ):
        # return None
        
        # initialize two pivots. minimum for MRV, maximum for Degree.
        minimum = self.gameboard.N
        maximum = -1
        result = None
        
        for v in self.network.variables:
            if not v.isAssigned():
                v_count = v.domain.size() #used to record remaining value
                if v_count < minimum:
                    minimum = v_count
                    result = v
                    maximum = -1
                elif v_count == minimum:
                    d_count = 0 #used to record degree
                    for n in self.network.getNeighborsOfVariable(v):
                        if not n.isAssigned():
                            d_count = d_count +1
                    if d_count > maximum:
                        maximum = d_count
                        result = v
    
        # all value are assigned.
        if (minimum == self.gameboard.N) and (maximum == -1):
            return None
        else:
            return result

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        d = {}
        for value in v.domain.values:
            counter = 0
            for v_neigh in self.network.getNeighborsOfVariable(v):
                if value in v_neigh.domain.values:
                    counter = counter +1
            d[value]=counter
        b = sorted(d.items(),key= lambda x:x[1])
        result = []
        for item in b:
            result.append(item[0])
        return result

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self ):
        if self.hassolution:
            return

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            for var in self.network.variables:

                # If all variables haven't been assigned
                if not var.isAssigned():
                    print ( "Error" )

            # Success
            self.hassolution = True
            return

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recurse
            if self.checkConsistency():
                self.solve()

            # If this assignment succeeded, return
            if self.hassolution:
                return

            # Otherwise backtrack
            self.trail.undo()

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "Degree":
            return self.getDegree()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
