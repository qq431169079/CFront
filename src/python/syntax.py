#
# This file generates the C++ parser for a given grammar
#
# For simplicity purposes our parser is a top-down, predictive one
# that handles LL(1) grammar
#

from common import *

#####################################################################
# class Symbol
#####################################################################

class Symbol:
    # This is the name of the "eps" symbol
    EMPTY_SYMBOL_NAME = "T_"
    # This is the symbol name indicating the end of input stream
    END_SYMBOL_NAME = "T_EOF"

    # We must initialize this later because terminal object has
    # not yet been defined
    EMPTY_SYMBOL = None
    END_SYMBOL = None

    """
    This class represents a grammar symbol that is either a terminal
    or non-terminal

    Each symbol has a name, which is the syntax notation we use in the
    grammar definition. For terminal symbols we always assume that the
    name is a macro defined in another CPP file, which is also used
    by the lex to produce the token stream; For terminals their names
    are only used internally by this generator and parser code
    """
    def __init__(self, name):
        """
        Initialize the symbol and its name
        """
        # This is either a terminal macro name or non-terminal name
        self.name = name

        return

    def __hash__(self):
        """
        Hashes the object into a hash code. Note that we compute the
        hash using the name, so each name should be unique no matter
        whether it is terminal or non-terminal

        This is defined for making terminals and non-terminals hashable,
        such that we could use them in a hash or set structure

        :return: hash code
        """
        return hash(self.name)

    def __eq__(self, other):
        """
        Check whether two objects are the same

        :param other: The other object to compare against
        :return: bool
        """
        return self.name == other.name

    def __ne__(self, other):
        """
        Check whether two objects are not the same

        :param other: The other object to compare against
        :return: bool
        """
        return self.name != other.name

    def __lt__(self, other):
        """
        Check whether the current symbol has a name that is
        smaller in alphabetical order

        :param other: The other object
        :return: bool
        """
        return self.name < other.name

    def is_symbol(self):
        """
        Checks whether the item is either a terminal or a
        non-terminal

        :return: bool
        """
        return self.is_terminal() is True or \
               self.is_non_terminal() is True

    def is_terminal(self):
        """
        Whether the node is a terminal object. This function should not
        be overloaded by the derived class, because it checks the class
        type here directly

        :return: bool
        """
        return isinstance(self, Terminal)

    def is_non_terminal(self):
        """
        Whether the node is a non-terminal symbol. This is the counterpart
        of is_terminal()

        :return: bool
        """
        return isinstance(self, NonTerminal)

    def is_empty(self):
        """
        Whether the symbol node is empty terminal, i.e. "eps" in classical
        representations. "eps" is nothing more than a terminal of a special
        name "T_", which could either be shared or a newly created one.

        :return: bool
        """
        # Note that empty node must also be terminal node
        return self.is_terminal() and \
               self.name == Symbol.EMPTY_SYMBOL_NAME

    @staticmethod
    def get_empty_symbol():
        """
        Returns an empty symbol, which is a reference to the shared
        object stored within the class object. Please do not modify
        the result returned by this function as it will affect all
        objects

        Instead of calling this function users could also create their
        own instance of empty symbol using the name "T_". There is no
        difference between creating a new instance and using the shared
        instance (the latter saves memory, though)

        :return: Terminal
        """
        if Symbol.EMPTY_SYMBOL is None:
            Symbol.EMPTY_SYMBOL = \
                Terminal(Symbol.EMPTY_SYMBOL_NAME)

        return Symbol.EMPTY_SYMBOL

    @staticmethod
    def get_end_symbol():
        """
        This function returns a reference to the constant END SYMBOL
        which is the "$" symbol in many classical text books

        :return: Terminal
        """
        if Symbol.END_SYMBOL is None:
            Symbol.END_SYMBOL = \
                Terminal(Symbol.END_SYMBOL_NAME)

        return Symbol.END_SYMBOL

#####################################################################
# class Terminal
#####################################################################

class Terminal(Symbol):
    """
    This class represents a terminal symbol object
    """
    def __init__(self, name):
        """
        Initialize the terminal object

        :param name: The name of the macro that defines the terminal
        """
        Symbol.__init__(self, name)

        return

    def __repr__(self):
        """
        Returns a string representation of the object that could
        be used as its identifier

        :return: str
        """
        return "[T %s]" % (self.name, )

    def __str__(self):
        """
        Returns a string representation

        :return: str
        """
        return self.__repr__()

#####################################################################
# class NonTerminal
#####################################################################

class NonTerminal(Symbol):
    """
    This class represents a non-terminal object in a grammar definition
    """
    def __init__(self, name):
        """
        Initialize non-terminal specific data members

        :param name: The name of the non-terminal
        """
        Symbol.__init__(self, name)

        # This is a set of production objects that this symbol
        # appears on the right hand side
        # This is for non-terminals, because we want to track
        # which non-terminal is in which production
        self.rhs_set = set()

        # This is the set of productions that this symbol appears
        # as the left hand side
        self.lhs_set = set()

        # These two are FIRST() and FOLLOW() described in
        # predictive parsers
        # They will be computed using recursion + memorization
        self.first_set = set()
        self.follow_set = set()

        # This is the set of all possible symbols if we expand the
        # non-terminal
        # We use this set to determine whether there are hidden
        # left recursions, i.e.
        #
        #  S -> V1 V2 V3
        #  V1 -> V4 V5
        #  V4 -> S V6
        self.first_rhs_set = None

        # This is used to generate name for a new node
        self.new_name_index = 1

        # This is used to compute the FIRST and FOLLOW
        # Since we always do these two recursively and iteratively
        # for each iteration we mark the result to True after
        # results are computed, and clear the flag to enable recomputing
        # between different iterations
        self.result_available = False

        return

    def get_first_length(self):
        """
        This function returns the length of the FIRST set. If it is
        None then return 0

        :return: int
        """
        if self.first_set is None:
            return 0

        return len(self.first_set)

    def get_follow_length(self):
        """
        Same as get-first_length() except that it works on FOLLOW set

        :return: int
        """
        if self.follow_set is None:
            return 0

        return len(self.follow_set)

    def clear_result_available(self):
        """
        This function clears the result available flag

        :return: None
        """
        self.result_available = False

        return

    def compute_first(self, path_list):
        """
        This function computes the FIRST set for the non-terminal

        We use a recursive algorithm to compute the first set. This
        process is similar to the one we use to compute the first
        RHS set, but in this case since we care about not only
        the formation but also semantic meaning of production rules,
        we also need to consider the EMPTY SYMBOL

        :return: None
        """
        # If we have already processed this node then return
        if self.result_available is True:
            return
        else:
            self.result_available = True

        if self in path_list:
            return

        path_list.append(self)

        # For all productions A -> B1 B2 .. Bi
        # FIRST(A) is defined as FIRST(B1) union FIRST(Bj)
        # where B1 - Bj - 1 could derive terminal and
        # Bj could not
        for p in self.lhs_set:
            for symbol in p.rhs_list:
                # For terminals just add it and process
                # the next production
                if symbol.is_terminal() is True:
                    # Empty symbol is also added here if it
                    # is derived
                    self.first_set.add(symbol)

                    # Also add it into the production
                    p.first_set.add(symbol)

                    break

                # Recursively compute the FIRST set
                # Since we have processed the symbol == self case here we
                # could call this without checking
                symbol.compute_first(path_list)
                self.first_set = \
                    self.first_set.union(symbol.first_set)

                # This could contain empty symbol
                p.first_set = \
                    p.first_set.union(symbol.first_set)

                # If the empty symbol could not be derived then
                # we do not check the following non-terminals
                if Symbol.get_empty_symbol() not in symbol.first_set:
                    break
            else:
                # This is executed if all symbols are non-terminal
                # and they could all derive empty string
                p.first_set.add(Symbol.get_empty_symbol())
                self.first_set.add(Symbol.get_empty_symbol())

        path_list.pop()

        return

    def compute_follow(self, path_list):
        """
        This functions computes the FOLLOW set. Note that the FOLLOW set
        is also computed recursively, and therefore we use memorization
        to compute it

        Note that this should be run for multiple rounds for correctness
        until no symbol could be added

        :return: None
        """
        # If we are seeking for this node's FOLLOW set and then recursively
        # reached the same node then there must by cyclic grammar:
        #   A -> a B
        #   B -> b C
        #   C -> c A
        # In this case if we compute FOLLOW(A) then we will compute FOLLOW(C)
        # and FOLLOW(B) which comes back to FOLLOW(A)
        #
        # However this structure is very common in left recursion removal:
        #   A -> A a | b
        #   ---
        #   A  -> b A'
        #   A' -> eps | a A'
        # When we compute FOLLOW(A') it is inevitable that this will happen

        # This is how memorization works
        if self.result_available is True:
            return
        else:
            self.result_available = True

        if self in path_list:
            return

        path_list.append(self)

        # For all productions where this terminal appears as a symbol
        for p in self.rhs_set:
            # This is a list of indices that this symbol appears
            # Current we only allow it to have exactly 1 element
            # Because a non-terminal is not allowed to appear twice
            index_list = p.get_symbol_index(self)
            assert(len(index_list) == 1)

            index = index_list[0]

            # If the symbol appears as the last one in the production
            if index == (len(p.rhs_list) - 1):
                # This could be a self recursion but we have prevented this
                # at the beginning of this function
                p.lhs.compute_follow(path_list)

                self.follow_set = \
                    self.follow_set.union(p.lhs.follow_set)
            else:
                # Compute the FIRST set for the substring after the
                # terminal symbol
                substr_first_set = p.compute_substring_first(index + 1)

                # If the string after the non-terminal could be
                # empty then we also need to add the FOLLOW of the LHS
                if Symbol.get_empty_symbol() in substr_first_set:
                    p.lhs.compute_follow(path_list)
                    self.follow_set = \
                        self.follow_set.union(p.lhs.follow_set)

                    # Remove the empty symbol because empty could not
                    # appear in FOLLOW set
                    substr_first_set.remove(Symbol.get_empty_symbol())

                # At last, merge the FIRST() without empty symbol
                # into the current FOLLOW set
                self.follow_set = \
                    self.follow_set.union(substr_first_set)

        # Do not forget to remove this in the path set (we know
        # it does not exist before entering this function)
        path_list.pop()

        return

    def get_new_symbol(self):
        """
        This function returns a new non-terminal symbol whose
        name is derived from the name of the current one.

        The new symbol could be used in left recursion elimination
        routines and other transformation. It is of the form:
          original-name + "-" + new name index
        and the index is incremented every time we created a new
        name

        :return: NonTerminal object with a synthesized name
        """
        # Synthesize a new name
        new_name = self.name + "-" + str(self.new_name_index)
        self.new_name_index += 1

        return NonTerminal(new_name)

    def eliminate_left_recursion(self):
        """
        This function eliminates direct left recursion for the
        current non-terminal symbol. We do not deal with
        indirect ones here

        :return: None
        """
        # If there is no direct left recursion then return
        # directly
        if self.exists_direct_left_recursion() is False:
            return

        # Make a backup here because LHS set will be cleared
        # A shallow copy is sufficient here because we just use
        # LHS and RHS references
        p_set = self.lhs_set.copy()

        # This is the set of productions with left recursion
        alpha_set = set()
        # This is the set of productions without left recursion
        beta_set = set()

        pg = None
        # Clear all productions - Note here we could not iterate on
        # self.lhs because it will be changed in the iteration body
        for p in p_set:
            # This removes the production from this object
            # and also removes it from other RHS objects
            p.clear()

            # If this is a left recursion production then add
            # it to alpha set; otherwise to beta set
            if p[0] == self:
                alpha_set.add(p)
            else:
                beta_set.add(p)

            # Check they all come from the same pg instance
            if pg is None:
                pg = p.pg
            else:
                assert(id(pg) == id(p.pg))

        # It must have been cleared
        assert(len(self.lhs_set) == 0)
        assert(len(alpha_set) + len(beta_set) == len(p_set))

        # Create a new symbol and add it into the set
        new_symbol = self.get_new_symbol()
        pg.non_terminal_set.add(new_symbol)

        empty_symbol = Symbol.get_empty_symbol()
        # Also add this into pg's terminal set
        pg.terminal_set.add(empty_symbol)

        # The scheme goes as follows:
        #   For a left recursion like this:
        #     A -> A a1 | A a2 | .. A ai | b1 | b2 | .. | bj
        #   We create a new symbol A' (as above), and add
        #     A  -> b1 A' | b2 A' | ... | bj A'
        #     A' -> a1 A' | a2 A' | ... | ai A' | eps
        #     where eps is the empty symbol
        #
        # There is one exception: if bj is empty string then we
        # just ignore it and add A -> A' instead

        for beta in beta_set:
            # Special case:
            # # If it is "A -> A a1 | A a2 | eps | B1 | B2" then
            # we make it
            #   A -> A' | B1 A' | B2 A'
            #   A' -> a1 A' | a2 A' | eps
            # As long as A', B1 B2 does not have common FIRST() element
            # we are still safe
            if len(beta.rhs_list) == 1 and \
               beta.rhs_list[0] == Symbol.get_empty_symbol():
                rhs_list = []
            else:
                # Make a copy to avoid directly modifying the list
                rhs_list = beta.rhs_list[:]

            rhs_list.append(new_symbol)

            # Add production: A -> bj A'
            Production(pg, self, rhs_list)

        for alpha in alpha_set:
            # Make a slice (which is internally a shallow copy)
            rhs_list = alpha.rhs_list[1:]
            rhs_list.append(new_symbol)

            # Add production: A -> bj A'
            Production(pg, new_symbol, rhs_list)



        # Add the last A' -> eps
        Production(pg, new_symbol, [empty_symbol])

        return

    def exists_indirect_left_recursion(self):
        """
        This function checks whether there is indirect left recursion
        in the production rules, e.g.

          S -> V1 V2 V3
          V1 -> S V4

        The way we check indirect left recursions is to construct
        a set of all possible left non-terminals in all possible
        derivations of the LHS of a production. This could be done
        recursively, but we also adopt memorization to reduce the
        number of step required from exponential to linear

        :return: bool
        """
        self.build_first_rhs_set()

        # If the node itself is in the first RHS set then
        # we know there is an indirect left recursion
        return self in self.first_rhs_set

    def build_first_rhs_set(self):
        """
        Builds first RHS set as specified in the definition of the
        set. We do this recursively using memorization, i.e. the
        result is saved in self.first_rhs_set and used later

        :return: None
        """
        # If we have visited this symbol before then just return
        # Since the set object is initialized to None on construction
        # this check guarantees we do not revisit symbols
        if self.first_rhs_set is not None:
            return
        else:
            # Initialize it to empty set
            self.first_rhs_set = set()

        # For all productions with this symbol as LHS, recursively
        # add all first RHS symbol into the set of this symbol
        for p in self.lhs_set:
            # The production must have RHS side
            assert(len(p) != 0)
            s = p[0]
            if s.is_terminal() is True:
                continue

            # Recursively build the set for the first RHS
            s.build_first_rhs_set()

            # Then merge these two sets
            self.first_rhs_set = \
                self.first_rhs_set.union(s.first_rhs_set)

            # Also add the first direct RHS into the set
            self.first_rhs_set.add(s)

        return

    def exists_direct_left_recursion(self):
        """
        This function checks whether there is direct left recursion,
        i.e. for non-terminal A checks whether A -> A b exists

        This is a non-recursive process, and we just need to make sure
        that no production for this symbol could derive itself

        :return: bool
        """
        # For each production that this symbol is the LHS
        for p in self.lhs_set:
            # The production must not be an empty one
            # i.e. there must be something on the RHS
            assert(len(p) != 0)
            # Since we have defined operator== for class Symbol
            # we could directly compare two symbol
            if p[0] == self:
                return True

        return False

    def __repr__(self):
        """
        Returns a string representation of the object that could
        be used as its identifier

        :return: str
        """
        return "[NT %s]" % (self.name, )

    def __str__(self):
        """
        Returns a string representation

        :return: str
        """
        return self.__repr__()

#####################################################################
# class Production
#####################################################################

class Production:
    """
    This class represents a single production rule that has a left
    hand side non-terminal symbol and
    """
    def __init__(self, pg, lhs, rhs_list):
        """
        Initialize the production object

        :param pg: The ParserGenerator object
        :param lhs: Left hand side symbol name (string name)
        :param rhs_list: A list of right hand side symbol names
        """
        # Make sure that the lhs is a non terminal symbol
        assert(lhs.is_non_terminal() is True)

        self.pg = pg

        # This is the first set of the production which we use to
        # select rules for the same LHS
        self.first_set = set()

        # Since we defined __setattr__() to prevent setting
        # these two names, we need to set them directly into
        # the underlying dict object
        self.__dict__["lhs"] = lhs
        # We append elements into this list later
        self.__dict__["rhs_list"] = rhs_list

        # Only after this point could we add the production
        # into any set, because the production becomes
        # immutable regarding its identify (i.e. LHS and
        # RHS list)

        # Add a reference to all non-terminal RHS nodes
        for symbol in self.rhs_list:
            assert(symbol.is_symbol() is True)
            if symbol.is_non_terminal() is True:
                # We could add self in this way, because
                # the identify of the set has been fixed
                symbol.rhs_set.add(self)

        # Also add a reference of this production into the LHS
        # set of the non-terminal
        # Note that since we add it into a set, the identity
        # of the production can no longer be changed
        lhs.lhs_set.add(self)

        # Make sure the user does not input duplicated
        # productions
        if self in self.pg.production_set:
            raise KeyError("Production already defined: %s" %
                           (str(self), ))

        # Finally add itself into the production set of the
        # containing pg object
        self.pg.production_set.add(self)

        return

    def get_symbol_index(self, symbol):
        """
        Returns a list of indices a symbol appear in the RHS list

        Note that the symbol could be either terminal or non-terminal
        and we do not check its identify. If the symbol does not
        exist we return an empty list

        :return: list(int)
        """
        # First of all it must be a symbol
        assert(symbol.is_symbol() is True)

        ret = []
        # This tracks the index of the current item
        index = 0
        for s in self.rhs_list:
            if s == symbol:
                ret.append(index)

            index += 1

        return ret

    def compute_substring_first(self, index=0):
        """
        This function computes the FIRST set for a substring. An optional
        index field is also provided to allow the user to start
        computing from a certain starting index

        Note that the FIRST set of the entire production has already been
        computed in compute_first() of a terminal symbol. The algorithm
        there is very similar to the one used here. Nevertheless, the
        result of passing index = 0 and the result computed by the
        non-terminal should be the same

        :return: set(Terminal)
        """
        assert(index < len(self.rhs_list))

        ret = set()
        for i in range(index, len(self.rhs_list)):
            rhs = self.rhs_list[i]

            # If we have seen a terminal, then add it to the list
            # and then return
            if rhs.is_terminal() is True:
                ret.add(rhs)
                return ret
            else:
                # This makes sure that the first set must already been
                # generated before calling this function
                assert(len(rhs.first_set) > 0)

                # Otherwise just union with the non-terminal's
                # first_set
                ret = ret.union(rhs.first_set)
                # Remove potential empty symbol
                ret.discard(Symbol.get_empty_symbol())

                # If the non-terminal could not derive empty then
                # that's it
                if Symbol.get_empty_symbol() not in rhs.first_set:
                    return ret

        # When we get to here we know that all non-terminals could
        # derive to empty string, and there is no terminal in the
        # sequence, so need also to add empty symbol
        ret.add(Symbol.get_empty_symbol())

        return ret

    def clear(self):
        """
        Clears all references from the production to non-terminal
        objects

        :return: None
        """
        # Remove this production from the LHS's LHS set
        # This happens in-place
        self.lhs.lhs_set.remove(self)
        for symbol in self.rhs_list:
            # If it is a non-terminal then we remove
            # the production from its rhs set
            if symbol.is_non_terminal() is True:
                symbol.rhs_set.remove(self)

        # Then clear itself from the generator's
        self.pg.production_set.remove(self)

        return

    def __setattr__(self, key, value):
        """
        Controls attribute access of this object because we do not allow
        accessing LHS and RHS list of this class directly

        Note that unlink getattr(), this is always called on attribute
        access.

        :param key: The attribute name
        :param value: The attribute value
        :return: None
        """
        if key == "lhs" or key == "rhs_list":
            raise KeyError("Cannot set key %s for class Production" %
                           (key, ))

        # Otherwise directly set the attribute into dict
        self.__dict__[key] = value

        return

    def __getitem__(self, item):
        """
        This mimics the list syntax

        :param item: The index
        :return: The i-th object in the rhs list
        """
        return self.rhs_list[item]

    def __hash__(self):
        """
        This function computes the hash for production object.

        The hash of a production object is defined by each of its
        components: lhs and every symbol in RHS list. We combine
        the hash code of each component using XOR and return

        :return: hash code
        """
        # This computes the hash of the lhs name
        h = hash(self.lhs)

        # Then combine the hash by XOR the hash of each RHS symbol
        for rhs in self.rhs_list:
            h ^= hash(rhs)

        return h

    def __eq__(self, other):
        """
        This function checks whether this production equals another

        We check equality by comparing each component, including LHS
        and each member of the RHS list. This is similar to how
        we compute the hash code for this class

        :param other: The other object
        :return: bool
        """
        # If the length differs then we know they will never
        # be the same. We do this before any string comparison
        if len(self.rhs_list) != len(other.rhs_list):
            return False

        if self.lhs != other.lhs:
            return False

        # Use index to fetch component
        for rhs1, rhs2 in zip(self.rhs_list, other.rhs_list):
            # If there is none inequality then just return
            if rhs1.__eq__(rhs2) is False:
                return False

        return True

    def __ne__(self, other):
        """
        This is the reverse of __eq__()

        :param other: The other object
        :return: bool
        """
        return not self.__eq__(other)

    def __repr__(self):
        """
        Returns a unique representation of the object using
        a string

        :return: str
        """
        s = "[" + self.lhs.name + ' ->'
        for rhs in self.rhs_list:
            s += (' ' + rhs.name)

        return s + ']'

    def __str__(self):
        """
        This function returns the string for printing this object

        :return: str
        """
        return self.__repr__()

    def __len__(self):
        """
        Returns the length of the RHS list

        :return: int
        """
        return len(self.rhs_list)


#####################################################################
# class ParserGenerator
#####################################################################

class ParserGenerator:
    """
    This class is the main class we use to generate the parsing code
    for a given LL(1) syntax
    """
    def __init__(self, file_name):
        """
        Initialize the generator object
        """
        # This is the name of the syntax definition file
        self.file_name = file_name

        # This is a mapping from symbol name to either terminals
        # or non-terminals
        self.symbol_dict = {}

        # This is a set of terminal objects
        self.terminal_set = set()

        # This is a set of non-terminal objects
        self.non_terminal_set = set()

        # This is a set of productions
        self.production_set = set()

        # This is the non-terminal where parsing starts
        self.root_symbol = None

        # It is a directory structure using (NonTerminal, Terminal)
        # pair as keys, and production rule object as value (note
        # that we only allow one production per key)
        self.parsing_table = {}

        # Reading the file
        self.read_file(file_name)

        return

    def generate_parsing_table(self):
        """
        This function generates the parsing table with (A, alpha)
        as keys and productions to use as values

        :return: None
        """
        for p in self.production_set:
            lhs = p.lhs
            for i in p.first_set:
                # Do not add empty symbol
                if i == Symbol.get_empty_symbol():
                    continue

                pair = (lhs, i)
                if pair in self.parsing_table:
                    raise KeyError(
                        "Duplicated (A, FIRST) entry for %s" %
                        (str(pair), ))

                self.parsing_table[pair] = p

            # If the production produces empty string
            # then we also need to add everything in FOLLOW(lhs)
            # into the jump table
            # Since we already verified that no FIRST in other
            # productions could overlap with LHS's FOLLOW set
            # this is entirely safe
            if Symbol.get_empty_symbol() in p.first_set:
                for i in lhs.follow_set:
                    pair = (lhs, i)
                    if pair in self.parsing_table:
                        raise KeyError(
                            "Duplicated (A, FOLLOW) entry for %s" %
                            (str(pair), ))

                    self.parsing_table[pair] = p

        return

    @staticmethod
    def dump_symbol_set(fp, ss):
        """
        Dumps a set into a given file handle. This function is
        for convenience of printing the FIRST and FOLLOW set

        The set if printed as follows:
           {eleemnt, element, .. }

        :param fp: The file handler
        :param ss: The set instance
        :return: None
        """
        first = True
        fp.write("{")

        # Make each iteration produce uniform result
        ss = list(ss)
        ss.sort()

        for i in ss:
            # Must be a symbol element
            assert(i.is_symbol() is True)
            if first is False:
                fp.write(", ")
            else:
                first = False

            fp.write(i.name)

        fp.write("}")

        return

    def dump(self, file_name):
        """
        This file dumps the contents of the parser generator into a file
        that has similar syntax as the .syntax input file.

        We dump the following information:
           (1) Revised rules
           (2) FIRST and FOLLOW set for each rule

        :return:
        """
        dbg_printf("Dumping modified syntax to %s", file_name)

        fp = open(file_name, "w")

        # Construct a list and sort them in alphabetical order
        # Since we have already defined the less than function for
        # non-terminal objects this is totally fine
        nt_list = list(self.non_terminal_set)
        nt_list.sort()
        # We preserve these symbols
        for symbol in nt_list:
            fp.write("%s: " % (symbol.name, ))

            ParserGenerator.dump_symbol_set(fp, symbol.first_set)
            fp.write(" ")
            ParserGenerator.dump_symbol_set(fp, symbol.follow_set)

            # End the non-terminal line
            fp.write("\n")

            for p in symbol.lhs_set:
                fp.write("   ")
                for rhs in p.rhs_list:
                    fp.write(" %s" % (rhs.name, ))

                fp.write("; ")
                ParserGenerator.dump_symbol_set(fp, p.first_set)
                #fp.write(" ")
                #ParserGenerator.dump_symbol_set(fp, symbol.follow_set)

                fp.write("\n")

            fp.write("\n")

        fp.close()
        return

    def dump_parsing_table(self, file_name):
        """
        This function dumps a parsing table into a specified file.
        The table is dumped in a format like the following:

           (NonTerminal, Terminal): Production Rule

        And for each entry in the table there is a line like this.
        Empty strings should not appear (they are always the default
        case), and EOF is displayed as T_EOF

        :param file_name: The name of the dumping file
        :return: None
        """
        dbg_printf("Dumping parsing table into %s", file_name)

        fp = open(file_name, "w")

        # Sort the list of keys such that NonTerminals group together
        # and then terminals group together
        key_list = self.parsing_table.keys()
        key_list.sort()

        prev_key = None
        for k in key_list:
            # If the key changes we also print a new line
            if prev_key is None:
                prev_key = k[0]
            elif prev_key != k[0]:
                fp.write("\n")
                prev_key = k[0]

            p = self.parsing_table[k]
            fp.write("(%s, %s): %s\n" %
                     (k[0].name, k[1].name, str(p)))

        fp.close()

        return

    def read_file(self, file_name):
        """
        Read the file into the instance, and do first pass analyze

        The input file is written in the following format:

        # This is a set of production rules:
        # S1 -> V1 V2 V3
        # S1 -> V2 V3
        S1:
          V1 V2 V3
          V2 V3
          ...

        # We use hash tag as comment line indicator
        S2:
          V2 V4
          V1 V3
          ...

        i.e. We treat the line ending with a colon as the left hand side
        of a production rule, and all following lines that do not end
        with a colon as right hand side. Each line represents a separate
        production. All right hand side tokens are separated by spaces,
        and we consider everything that is not space character as token
        names

        The empty symbol "eps" is also a non-terminal, with the special
        name T_ (T + underline)

        :param file_name: The name of the file to read the syntax
        :return: None
        """
        fp = open(file_name, "r")
        s = fp.read()
        fp.close()

        # Split the content of the file into lines
        line_list = s.splitlines()

        # Since we need to iterate through this twice, so let's
        # do the filtering for only once
        # We use list comprehension to filter out lines that are
        # empty or starts with '#'
        line_list = \
            [line.strip()
             for line in line_list
             if (len(line.strip()) != 0 and line.strip()[0] != '#')]

        # This function recognizes terminals and non-terminals
        # and stores them into the corresponding set structure
        self.process_symbol(line_list)
        # This function adds productions and references between
        # productions and symbols
        self.process_production(line_list)
        # This sets self.root_symbol and throws exception is there
        # is problem finding it
        self.process_root_symbol()
        # As suggested by name
        self.process_left_recursion()
        # Compute the first and follow set
        self.process_first_follow()

        # Check feasibility of LL(1)
        self.verify()

        # Then generates the parsing table
        self.generate_parsing_table()

        return

    def verify(self):
        """
        Verify the validity of the grammar as LL(1) for generating
        predictive recursive descent parser

        We check the following properties:
          (1) There is no direct left recursion
          (2) There is no indirect left recursion
          The above two are checked together because indirect
          left recursion includes direct left recursion in our case
          (3) For LHS symbol S, all of its production must have
              disjoint FIRST sets
          (4) For A -> a | b if a derives empty string then FIRST(b)
              and FOLLOW(A) are disjoint sets
          (5) For all productions, if T_ appears then it must be
              A -> T_
          (6) For all non-terminals S, it must only appear once in
              all productions where it appears
          (7) Empty symbol does not appear in all FOLLOW sets

        (This list is subject to change)

        If any of these are not satisfied we throw an exception to
        indicate the user that the grammar needs to be changed

        :return: None
        """
        # This checks both condition
        for symbol in self.non_terminal_set:
            if symbol.exists_indirect_left_recursion() is True:
                raise ValueError("Left recursion is detected" +
                                 " @ symbol %s" %
                                 (str(symbol), ))

        # This checks condition 5
        for p in self.production_set:
            for symbol in p.rhs_list:
                if symbol == Symbol.get_empty_symbol():
                    if len(p.rhs_list) != 1:
                        raise ValueError("Empty string in the" +
                                         " middle of production")

        # This checks condition 6
        for symbol in self.non_terminal_set:
            for p in symbol.rhs_set:
                # This is a list of indices that this symbol
                # appears in the production
                ret = p.get_symbol_index(symbol)

                # Make sure each non-terminal only appears once
                # in all productions
                assert(len(ret) == 1)

        # This checks condition 7
        for symbol in self.non_terminal_set:
            assert(Symbol.get_empty_symbol() not in symbol.follow_set)

        # This checks condition 3
        for symbol in self.non_terminal_set:
            # Make it a list to support enumeration
            lhs = list(symbol.lhs_set)
            size = len(lhs)

            for i in range(1, size):
                for j in range(0, i):
                    # This is the intersection of both sets
                    s = lhs[i].first_set.intersection(lhs[j].first_set)
                    if len(s) != 0:
                        raise ValueError(
                            ("The intersection of %s's first_set is not empty\n" +
                             "  %s (%s)\n  %s (%s)") %
                            (str(symbol),
                             str(lhs[i]),
                             str(lhs[i].first_set),
                             str(lhs[j]),
                             str(lhs[j].first_set)))

        # This checks condition 4
        for symbol in self.non_terminal_set:
            lhs = list(symbol.lhs_set)
            size = len(lhs)

            for i in range(1, size):
                for j in range(0, i):
                    # These two are two productions
                    pi = lhs[i]
                    pj = lhs[j]

                    # If pi could derive empty string then FIRST(pj)
                    # and follow A are disjoint
                    if Symbol.get_empty_symbol() in pi.first_set:
                        t = pj.first_set.intersection(symbol.follow_set)
                        if len(t) != 0:
                            raise ValueError(
                                "FIRST/FOLLOW conflict for %s on: \n  %s\n  %s" %
                                (str(symbol),
                                 str(pi),
                                 str(pj)))

                    if Symbol.get_empty_symbol() in pj.first_set:
                        t = pi.first_set.intersection(symbol.follow_set)
                        if len(t) != 0:
                            raise ValueError(
                                "FIRST/FOLLOW conflict for %s on: \n  %s\n  %s" %
                                (str(symbol),
                                 str(pi),
                                 str(pj)))

        return

    def process_first_follow(self):
        """
        This function computes FIRST and FOLLOW set
        for all non-terminals. The set of non-terminals
        is not changed during iteration, so we do not
        need to make a copy of the set

        :return: None
        """
        # We use this to fix the order of iteration
        nt_list = list(self.non_terminal_set)

        dbg_printf("Compute FIRST set")

        # A list of FIRST set sizes; we iterate until this
        # becomes stable
        count_list = [nt.get_first_length() for nt in nt_list]
        index = 0
        while True:
            index += 1
            dbg_printf("    Iteration %d", index)

            for symbol in self.non_terminal_set:
                symbol.clear_result_available()

            for symbol in self.non_terminal_set:
                symbol.compute_first([])

            # This is the vector after iteration
            t = [nt.get_first_length() for nt in nt_list]
            if t == count_list:
                break

            count_list = t

        dbg_printf("Compute FOLLOW set")

        # First add EOF symbol into the root symbol
        # We need to do this before the algorithm converges
        assert (self.root_symbol is not None)
        self.root_symbol.follow_set.add(Symbol.get_end_symbol())

        count_list = [nt.get_follow_length() for nt in nt_list]
        index = 0
        while True:
            index += 1
            dbg_printf("    Iteration %d", index)

            for symbol in self.non_terminal_set:
                symbol.clear_result_available()

            for symbol in self.non_terminal_set:
                # The path list must be empty list
                # because we start from a fresh new state
                # for every iteration
                symbol.compute_follow([])

            t = [nt.get_follow_length() for nt in nt_list]
            if t == count_list:
                break

            count_list = t

        return

    def process_left_recursion(self):
        """
        This function removes left recursion for all rules

        :return: None
        """
        # Make a copy to avoid changing the size of the set
        temp = self.non_terminal_set.copy()

        # Remove left recursion. Note we should iterate
        # on the set above
        for symbol in temp:
            symbol.eliminate_left_recursion()

        return

    def process_root_symbol(self):
        """
        This function finds root symbols. The root symbol is defined as
        the non-terminal symbol with no reference in its rhs_set, which
        indicates in our rule that the symbol is the starting point of
        parsing

        Note that even in the case that root symbol cannot be found, we
        could always define an artificial root symbol by adding:
            S_ROOT -> S
        if S is supposed to be the root but is referred to in some
        productions. This is guaranteed to work.

        In the case that multiple root symbols are present, i.e. there
        are multiple nodes with RHS list being empty, we report error
        and print all possibilities

        :return: None
        """
        # We use this set to find the root symbol
        # It should only contain 1 element
        root_symbol_list = []
        for symbol in self.non_terminal_set:
            if len(symbol.rhs_set) == 0:
                root_symbol_list.append(symbol)

        # These two are abnormal case
        if len(root_symbol_list) > 1:
            dbg_printf("Multiple root symbols found. " +
                       "Could not decide which one")

            # Print each candidate and exit
            for symbol in root_symbol_list:
                dbg_printf("    Candidate: %s", str(symbol))

            raise ValueError("Multiple root symbols")
        elif len(root_symbol_list) == 0:
            dbg_printf("Root symbol is not found. " +
                       "May be you should define an artificial one")

            raise ValueError("Root symbol not found")

        # This is the normal case - exactly 1 is found
        self.root_symbol = root_symbol_list[0]

        return

    def process_production(self, line_list):
        """
        This function constructs productions and place them into
        a list of productions. It also establishes referencing relations
        between productions and non-terminal symbols (i.e. which symbol
        is referred to in which production)

        :return: None
        """
        # This is the current non-terminal node, and we change it
        # every time a line with ':' is seen
        current_nt = None
        has_body = True
        for line in line_list:
            if line[-1] == ':':
                # When we see the start of a production, must make
                # sure that the previous production has been finished
                if has_body is False:
                    raise ValueError(
                        "Production %s does not have a body" %
                        (line, ))
                else:
                    has_body = False

                current_nt_name = line[:-1]
                assert(current_nt_name in self.symbol_dict)

                current_nt = self.symbol_dict[current_nt_name]
                continue

            # There must be a non-terminal node to use
            if current_nt is None:
                raise ValueError("The syntax must start with a non-terminal")
            else:
                assert(current_nt.is_non_terminal() is True)

            # We have seen a production body
            has_body = True

            # This will be passed into the constructor of
            # class Production
            rhs_list = []

            # This is a list of symbol names
            # which have all been converted into terminals
            # or non-terminals in the first pass
            symbol_list = line.split()
            for symbol_name in symbol_list:
                # The key must exist because we already had one
                # pass to add all symbols
                assert(symbol_name in self.symbol_dict)

                symbol = self.symbol_dict[symbol_name]

                # Add an RHS symbol
                # Establishes from non-terminals to productions
                # are established later when we construct the object
                rhs_list.append(symbol)

            # Finally construct an immutable class Production instance
            # the status could no longer be changed after it is
            # constructed
            # This also adds the production into the production
            # set of the generator
            Production(self, current_nt, rhs_list)

        return

    def process_symbol(self, line_list):
        """
        Recognize symbols, and store them into the dictionary for
        symbols, as well as the sets for terminals and non-terminals

        :param line_list: A list of lines
        :return:
        """
        # This is a set of names for which we are not certain whether
        # it is a terminal or non-terminal
        in_doubt_set = set()

        for line in line_list:
            # We have seen a new LHS of the production rule
            # Also non-terminal is very easy to identify because
            # it must be on the LHS side at least once
            if line[-1] == ':':
                # This is the name of the terminal
                name = line[:-1]
                # Create the non-terminal object and then
                non_terminal = NonTerminal(name)

                # If the non-terminal object already exists then we have
                # seen duplicated definition
                if non_terminal in self.symbol_dict:
                    raise KeyError("Duplication definition of non-terminal: %s" %
                                   (name, ))

                # Add the non-terminal node into both symbol dictionary
                # and the non-terminal set
                self.symbol_dict[name] = non_terminal
                self.non_terminal_set.add(non_terminal)

                # Since we already know that name is a non-terminal
                # we could remove it from this set
                # discard() does not raise error even if the name
                # is not in the set
                in_doubt_set.discard(name)
            else:
                # Split the line using space characters
                name_list = line.split()
                # We do not know whether name is a terminal or non-terminal
                # but we could rule out those that are known to be
                # non-terminals
                for name in name_list:
                    # If the name is already seen and it is a terminal
                    # then we skip it
                    if name in self.symbol_dict:
                        continue

                    # Add the name into in_doubt_set because
                    # we are unsure about its status
                    in_doubt_set.add(name)

        # After this loop, in_doubt_set contains names that do not
        # appear as the left hand side, and must be terminals
        for name in in_doubt_set:
            assert(name not in self.symbol_dict)
            terminal = Terminal(name)
            self.symbol_dict[name] = terminal

            # And then add terminals into the terminal set
            assert(terminal not in self.terminal_set)
            self.terminal_set.add(terminal)

        return

#####################################################################
#####################################################################
#####################################################################
# class ParserGeneratorTestCase - Test cases
#####################################################################
#####################################################################
#####################################################################

class ParserGeneratorTestCase(DebugRunTestCaseBase):
    """
    This is the test case class
    """
    def __init__(self):
        """
        Initialize the testing environment and start testing
        """
        # Note that we did not adopt the new style class definition
        # and therefore must directly refer to the base class
        DebugRunTestCaseBase.__init__(self)

        # Processing command lines
        argv = Argv()

        # Initialize data members that will be used across
        # different test cases
        self.pg = None

        self.run_tests(argv)

        return

    def demo(self):
        """
        Interactive mode to display how a string is parsed

        :return: None
        """
        pg = self.pg
        pt = pg.parsing_table

        # It's like the following:
        # *p + a * b ? func(1, c * *q) : 2

        test_str = [Terminal("T_STAR"),
                    Terminal("T_IDENT"),
                    Terminal("T_PLUS"),
                    Terminal("T_IDENT"),
                    Terminal("T_STAR"),
                    Terminal("T_IDENT"),
                    Terminal("T_QMARK"),
                    Terminal("T_IDENT"),
                    Terminal("T_LPAREN"),
                    Terminal("T_INT_CONST"),
                    Terminal("T_COMMA"),
                    Terminal("T_IDENT"),
                    Terminal("T_STAR"),
                    Terminal("T_STAR"),
                    Terminal("T_IDENT"),
                    Terminal("T_RPAREN"),
                    Terminal("T_COLON"),
                    Terminal("T_INT_CONST"),
                    Symbol.get_end_symbol()]

        index = 0
        step = 1

        # We use a stack to mimic the behavior of the parser
        stack = [pg.root_symbol]
        while len(stack) > 0:
            print step, stack

            step += 1
            top = stack.pop()

            if top.is_terminal() is True:
                if top == Symbol.get_empty_symbol():
                    # Empty symbol does not consume any
                    # tokens in the token stream
                    continue
                elif top == test_str[index]:
                    index += 1
                    continue
                else:
                    raise ValueError("Could not match token: %s @ %d" %
                                     (str(test_str[index]), index))

            pair = (top, test_str[index])
            if pair not in pt:
                dbg_printf("Pair %s (index %d) not in parsing table",
                           pair,
                           index)
                raise ValueError("Could not find entry in parsing table")

            p = pt[pair]
            for i in reversed(p.rhs_list):
                stack.append(i)

        return


    @TestNode()
    def test_read_file(self, argv):
        """
        This function tests whether the input file could be read
        and parsed correctly

        :return: None
        """
        print_test_name()

        # The first argument is the file name
        file_name = argv.arg_list[0]
        dbg_printf("Opening file: %s", file_name)

        # Initialize the object - it will read the file
        # and parse its contents
        self.pg = ParserGenerator(file_name)
        pg = self.pg

        dbg_printf("Root symbol: %s", pg.root_symbol)

        # Check the identity of symbols
        for i in pg.terminal_set:
            assert(i.is_terminal() is True)

        for i in pg.non_terminal_set:
            assert(i.is_non_terminal() is True)

        for p in pg.production_set:
            if p.first_set != p.compute_substring_first():
                print p
                print p.first_set
                print p.compute_substring_first()

            assert(p.first_set == p.compute_substring_first())

        # Finally dump the resulting file
        pg.dump(file_name + ".dump")
        pg.dump_parsing_table(file_name + ".table")

        self.demo()

        return

if __name__ == "__main__":
    ParserGeneratorTestCase()