#
# This file includes routines for transforming the abstract
# syntax tree
#

class TypeNode:
    """
    This class represents the type node that represents type

    Note that types form a singly linked list that are represented
    as derived from a less complicated type (i.e. the type node in
    next_node)
    """

    # Here we define all possible type operations
    OP_BASE_TYPE = 0
    OP_FUNC_CALL = 1
    OP_ARRAY_SUB = 2
    OP_DEREF = 3
    # Composite types
    OP_STRUCT = 4

    # This is a list of primitive types
    # Note that enum type is always translated as INT
    TYPE_CHAR = 0
    TYPE_SHORT = 1
    TYPE_INT = 2
    TYPE_LONG = 3
    TYPE_VOID = 4

    def __init__(self, op, next_node=None, data=None):
        """
        Initialize the type node with a next pointer (which means
        the type that it derives from) and optional data
        which is either array range, function argument (they are types,
        too), pointer dereference spec
        """
        # This is the operation that this node
        # performs over its sub-type
        self.op = op
        # If this is a base type this points to the integer type
        self.next_node = next_node
        # For base type this is type spec; For DEREF operation
        # this is also type spec
        self.data = data

        return

    @staticmethod
    def get_base_type(syntax_node, type_spec):
        """
        This function returns a base type given the syntax node that
        could construct a base type (i.e. struct, enum which is always INT
        and primitive types)

        :param syntax_node: The syntax node that defines the base type
        :return: TypeNode object
        """
        if syntax_node.symbol == "T_CHAR":
            t = TypeNode.TYPE_CHAR
        elif syntax_node.symbol == "T_INT":
            t = TypeNode.TYPE_INT
        elif syntax_node.symbol == "T_SHORT":
            t = TypeNode.TYPE_SHORT
        elif syntax_node.symbol == "T_LONG":
            t = TypeNode.TYPE_LONG
        elif syntax_node.symbol == "T_ENUM":
            t = TypeNode.TYPE_INT
        elif syntax_node.symbol == "T_STRUCT":
            t = TYPE_STRUCT

            #TODO: Parse struct type here
            return TypeNode

        # In all other cases just use the type and return
        return TypeNode(TypeNode.OP_BASE_TYPE,
                        t,
                        type_spec)

    @staticmethod
    def derive(self, op):
        pass

#####################################################################
# class SyntaxNode
#####################################################################

class SyntaxNode:
    """
    This is the syntax node we use for demonstrating the parser's
    parsing process
    """
    def __init__(self, symbol):
        """
        Initialize the node with a symbol. The symbol could be
        either terminal or non-terminal

        :param symbol: The symbol of this syntax node
        """
        # Must be a string or unicode type
        assert(isinstance(symbol, str))

        self.symbol = symbol
        # These are child nodes that appear as derived nodes
        # in the syntax specification
        self.child_list = []

        # This holds the token value and will be set
        # during parsing. If there is no token value just keep
        # it as None
        self.data = None

        return

    def append(self, symbol):
        """
        Append a new symbol into the child list

        :param symbol: Terminal or NonTerminal
        :return: None
        """
        self.child_list.append(symbol)
        return

    def __getitem__(self, item):
        """
        Returns the i-th item in the child node

        :param item: integer
        :return: Symbol
        """
        return self.child_list[item]

    def __str__(self):
        """
        Returns a string representation of the syntax node

        If the node has data we also append the data; Otherwise
        just print its name

        :return:
        """
        if self.data is None:
            return self.symbol
        else:
            return "%s [%s]" % (self.symbol,
                                self.data)

#####################################################################
# Type Rules for AST
#####################################################################

# This is a set of type modifiers that maps from the syntax node
# name to the mask value
TYPE_MODIFIER_DICT = {
    "T_CONST": 0x00000001,
    "T_VOLATILE": 0x00000002,
    "T_STATIC": 0x00000004,
    "T_REGISTER": 0x00000008,
    "T_EXTERN": 0x00000010,
    "T_UNSIGNED": 0x00000020,
    "T_AUTO": 0x00000040,
    "T_SIGNED": 0x00000080,
    "T_TYPEDEF": 0x00000100,
}

# These are constant values we use to check whether a flag is set or not
TYPE_MODIFIER_CONST = TYPE_MODIFIER_DICT["T_CONST"]
TYPE_MODIFIER_VOLATILE = TYPE_MODIFIER_DICT["T_VOLATILE"]
TYPE_MODIFIER_STATIC = TYPE_MODIFIER_DICT["T_STATIC"]
TYPE_MODIFIER_REGISTER = TYPE_MODIFIER_DICT["T_REGISTER"]
TYPE_MODIFIER_EXTERN = TYPE_MODIFIER_DICT["T_EXTERN"]
TYPE_MODIFIER_UNSIGNED = TYPE_MODIFIER_DICT["T_UNSIGNED"]
TYPE_MODIFIER_AUTO = TYPE_MODIFIER_DICT["T_AUTO"]
TYPE_MODIFIER_SIGNED = TYPE_MODIFIER_DICT["T_SIGNED"]
TYPE_MODIFIER_TYPEDEF = TYPE_MODIFIER_DICT["T_TYPEDEF"]

def get_type_modifier(child_list):
    """
    This function returns a bit set that identifies the type
    modifier

    If multiple modifiers are defined we throw an exception

    :param child_list: A list where syntax node of modifiers
                       are stored
    :return: (int (the bit set), node for type)
             If there is a type then it is returned in the second
             component of the tuple
             If no type is found then return None
    """
    base_type_node = None
    type_modifier_mask = 0x00000000

    for spec in child_list:
        # It must exist otherwise the parsing is wrong
        spec_mask = TYPE_MODIFIER_DICT.get(spec.symbol, None)
        # Then it is a type name because it does not belong to
        # any of the specifiers we have seen
        if spec_mask is None:
            if base_type_node is not None:
                raise TypeError("Could not specify" +
                                " more than one type in a" +
                                " declaration (%s and %s)!" %
                                (spec.symbol, base_type_node.symbol))

            base_type_node = spec
        else:
            # If the modifier has already been seen then this is
            # an error also
            if (type_modifier_mask & spec_mask) != 0x00000000:
                raise TypeError("Could not specify %s twice!" %
                                (spec.symbol,))

            # Then add the spec onto the mask
            type_modifier_mask |= spec_mask

    return type_modifier_mask, base_type_node

def transform_type_decl(decl_root):
    """
    This function transforms the AST declaration into a form
    that is easier for the parser to process

    If the declaration does not have a body we return T_DECL
    with data being set to (base type, mask)

    If the declaration has a body we return T_DECL with
    a list of (name, type, init) triples, with init be an
    optionally None object

    :param decl_root: The T_DECL node
    :return: SyntaxNode, bool
    """
    decl_spec = decl_root.child_list[0]
    if len(decl_root.child_list) == 2:
        init_decl_list = decl_root.child_list[1]
    else:
        init_decl_list = None

    # This function returns the base type
    # as well as the bit set on type specifiers
    type_modifier_mask, base_type_node = \
        get_type_modifier(decl_spec.child_list)
    print base_type_node.symbol

    # If we did not find the base type then throw error
    if base_type_node is None:
        raise TypeError("Need to specify a base type for declaration!")

    # If there is no decl list (i.e. name + expression to
    # derive the type)
    if init_decl_list is None:
        # If we specify typedef then there must be a name to
        # be defined
        if type_modifier_mask & TYPE_MODIFIER_TYPEDEF != 0x0:
            raise TypeError("typedef must define a name!")

        # Build a new node and return it as a replacement
        new_node = SyntaxNode(decl_root.symbol)
        new_node.data = (base_type_node, type_modifier_mask)

        return new_node, False

    # For each declarator + init in the list we do the same processing
    for init_decl in init_decl_list:
        pass

    return decl_root, True

#####################################################################
# The following is the driver for transformation
#####################################################################

# This is the dict for transforming the AST
# The key is the type of the syntax node, and the value
# is the routine for transforming it.
#
# The return value of the function should be also a
# syntax node object, and it will be used to replace
# the node we passed to the function
TRANSFORM_DICT = {
    "T_DECL": transform_type_decl,
}

def transform_ast(root):
    """
    This function traverses the AST using pre-order traversal
    and then invoke routines to transform nodes based on its
    node type

    Note that in case we exceed the maximum depth for recursion
    in a very deep AST, we maintain a stack manually in this function
    and emulate recursion using the stack

    The return value also indicates whether we need to transform
    the child node of the current node after it has been transformed.
    If the returned boolean is False then we do not attempt to
    transform its child nodes; Otherwise we continue with its child

    :param root: The root of the AST
    :return: root (may have been changed), bool
    """
    # This stores tuple: (child list, index)
    stack = []

    # To keep consistency we pretend that the root also comes
    # from a child list of only one element that is the root
    root_child_list = [root]

    current_child_list = root_child_list
    current_index = 0
    current_level = 0

    while True:
        # While there is still a node to transform in the child list
        while current_index < len(current_child_list):
            current_node = current_child_list[current_index]
            func = TRANSFORM_DICT.get(current_node.symbol, None)

            # Enable this to check we are traversing in the
            # correct order (i.e. pre-order)
            #print " " * current_level + current_node.symbol

            # If the current node has something to transform
            if func is not None:
                new_node, transform_child = func(current_node)
                # Update the node into the child list
                # Note that the child list is just a reference
                # so we could update it directly and the change will be
                # reflected into the syntax node
                current_child_list[current_index] = new_node
            else:
                # Otherwise we must continue transforming the children
                # of the current node
                transform_child = True

            # If transform child is True then just append the current
            # index into the stack and start a new instance
            if transform_child is True:
                stack.append((current_child_list, current_index + 1))
                current_child_list = current_node.child_list
                current_index = 0
                current_level += 1
                continue
            else:
                current_index += 1

        # If the stack is empty which means we have finished transforming all
        # nodes, then just return the new root node
        if len(stack) == 0:
            break
        else:
            # Just finished the current node's children, need to
            # go up one level and continue
            current_child_list, current_index = stack.pop()
            current_level -= 1

    return root_child_list[0]
