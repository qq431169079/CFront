
#ifndef _TYPE_H
#define _TYPE_H

#include <ctype.h>
#include "list.h"
#include "bintree.h"
#include "token.h"
#include "str.h"
#include "eval.h"

#define SCOPE_LEVEL_GLOBAL  0
#define TYPE_MAX_DERIVATION 64 // Maximum 64 levels of type derivation (deref, array, func, etc.)
#define TYPE_PTR_SIZE       8  // A pointer has 8 bytes
#define TYPE_UNKNOWN_SIZE   ((size_t)-1) // Array decl without concrete size

enum {
 SCOPE_ENUM   = 0,
 SCOPE_VAR    = 1,
 SCOPE_STRUCT = 2,
 SCOPE_UNION  = 3,
 SCOPE_UDEF   = 4,
 SCOPE_TYPE_COUNT,
};

// We track objects using a centralized list per scope to simplify memory management
// All objects allocated within the scope will be freed when the scope gets poped
// No ownership of memory is therefore enforced, i.e. objects do not own each other.
enum {
  OBJ_TYPE = 0,
  OBJ_COMP = 1,
  OBJ_FIELD = 2,
  OBJ_TYPE_COUNT,
};

// A statement block creates a new scope. The bottomost scope is the global scope
typedef struct {
  int level;                            // 0 means global
  hashtable_t *names[SCOPE_TYPE_COUNT]; // enum, var, struct, union, udef, i.e. symbol table
  list_t *objects[OBJ_TYPE_COUNT];
} scope_t;

typedef struct {
  stack_t *scopes;
} type_cxt_t;

typedef uint64_t typeid_t;
typedef uint64_t offset_t;

typedef enum {
  LVALUES_BEGIN = 1, 
  ADDR_STACK, ADDR_HEAP, ADDR_GLOBAL,
  LVALUES_END, RVALUES_BEGIN = 10,
  ADDR_TEMP, // Unnamed variable (intermediate node of an expression)
  ADDR_IMM,  // Immediate value (constants)
  RVALUES_END,
} addrtype_t;

struct comp_t_struct;
typedef struct type_t_struct {
  typeid_t typeid;        // Index in the list
  decl_prop_t decl_prop;   // Can be BASETYPE_ or TYPE_OP_ or DECL_ series
  union {
    struct comp_t_struct *comp; // If base type indicates s/u/e this is a pointer to it; Do not own
    struct type_t_struct *next; // If derived type, this points to the next type by applying the op; Do not own
  };
  union {
    struct {
      list_t *arg_list;     // If decl_prop is function call this stores a list of type_t *; Owns memory
      bintree_t *arg_index; // Binary tree using arg name as key; Owns memory
      int vararg;           // Set if varadic argument function
    };
    int array_size;   // If decl_prop is array sub this stores the (optional) size of the array
  };
  size_t size;  // Always check if it is TYPE_UNKNOWN_SIZE which means compile time size unknown or undefined comp
} type_t;

typedef struct value_t_struct {
  type_t *type;         // Do not own
  addrtype_t addrtype;
  union {
    uint8_t ucharval;
    uint16_t ushortval;
    uint32_t uintval;
    uint64_t ulongval;
    offset_t offset;    // If it represents an address then this is the offset
  };
} value_t;

#define COMP_NO_DEFINITION   0
#define COMP_HAS_DEFINITION  1

// Represents composite type
typedef struct comp_t_struct {
  char *name;             // NULL if no name; Does not own memory
  list_t *field_list;     // A list of field * representing the type of the field; owns memory
  bintree_t *field_index; // These two provides both fast named access, and ordered storage; Owns memory
  size_t size;
  int has_definition;     // Whether it is a forward definition (0 means yes)
} comp_t;

// Single field within the composite type
typedef struct {
  char *name;          // NULL if anonymous field; Does not own memory
  int bitfield_size;   // Set if bit field; -1 if not
  int offset;          // Offset within the composite structure
  size_t size;         // Number of bytes occupied by the actual storage including padding
  type_t *type;        // Type of this field; Do not own memory
} field_t;

scope_t *scope_init(int level);
void scope_free(scope_t *scope);
type_cxt_t *type_sys_init();
void type_sys_free(type_cxt_t *cxt); 

hashtable_t *scope_atlevel(type_cxt_t *cxt, int level, int type);
hashtable_t *scope_top(type_cxt_t *cxt, int type);
int scope_numlevel(type_cxt_t *cxt);
void scope_recurse(type_cxt_t *cxt);
void scope_decurse(type_cxt_t *cxt);
void *scope_top_find(type_cxt_t *cxt, int type, void *key);
void *scope_top_insert(type_cxt_t *cxt, int type, void *key, void *value);
void *scope_search(type_cxt_t *cxt, int type, void *name);

type_t *type_init();
void type_free(type_t *type);
comp_t *comp_init(char *name, int has_definition);
void comp_free(comp_t *comp);
field_t *field_init();
void field_free(field_t *field);

// Returns a type * object given a T_DECL node and optionally base type
type_t *type_gettype(type_cxt_t *cxt, token_t *decl, token_t *basetype); 
comp_t *type_getcomp(type_cxt_t *cxt, token_t *token, int is_forward);
void type_freecomp(comp_t *comp);
#endif