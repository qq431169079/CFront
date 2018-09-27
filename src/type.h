
#ifndef _TYPE_H
#define _TYPE_H

#include <ctype.h>
#include "list.h"
#include "bintree.h"
#include "token.h"
#include "str.h"

#define SCOPE_LEVEL_GLOBAL 0
typedef uint64_t type_maxint_t;  // Maximum integer type we support

enum {
 SCOPE_ENUM   = 0,
 SCOPE_VAR    = 1,
 SCOPE_STRUCT = 2,
 SCOPE_UNION  = 3,
 SCOPE_UDEF   = 4,
 SCOPE_TYPE_COUNT,
};

// A statement block creates a new scope. The bottomost scope is the global scope
typedef struct {
  int level;                            // 0 means global
  hashtable_t *names[SCOPE_TYPE_COUNT]; // enum, var, struct, union, udef
} scope_t;

typedef struct {
  stack_t *scopes;
  vector_t *types;    // A list of types. Type objects belong to this list and must be freed upon exit
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

typedef struct {
  typeid_t typeid;        // Index in the list
  decl_prop_t basetype;   // Uses token decl_prop constants
  token_t *decl;          // Uses token tree
  size_t size;
} type_t;

extern type_t builtin_types[]; // Builtin types

#define TYPE_INDEX_VOID   0
#define TYPE_INDEX_CHAR   1
#define TYPE_INDEX_SHORT  2
#define TYPE_INDEX_INT    3
#define TYPE_INDEX_LONG   4
#define TYPE_INDEX_UCHAR  5
#define TYPE_INDEX_USHORT 6
#define TYPE_INDEX_UINT   7
#define TYPE_INDEX_ULONG  8

typedef struct value_t_struct {
  type_t *type;
  addrtype_t addrtype;
  union {
    uint8_t ucharval;
    uint16_t ushortval;
    uint32_t uintval;
    uint64_t ulongval;
    offset_t offset;    // If it represents an address then this is the offset
  };
} value_t;

// Represents composite type
typedef struct {
  list_t *fields;    // A list of type * representing the type of the field
  bintree_t *index;  // These two provides both fast named access, and ordered storage
  char *name;
} comp_t;

int type_intsizes[11];

int type_getintsize(decl_prop_t decl_prop);
scope_t *scope_init(int level);
void scope_free(scope_t *scope);
type_cxt_t *type_init();
void type_free(type_cxt_t *cxt); 
int type_cmpdecl();    // Compares a declaration of a type
int type_cmpbase();    // Compares a definition of a type

hashtable_t *scope_atlevel(type_cxt_t *cxt, int level, int type);
hashtable_t *scope_top(type_cxt_t *cxt, int type);
int scope_numlevel(type_cxt_t *cxt);
void scope_recurse(type_cxt_t *cxt);
void scope_decurse(type_cxt_t *cxt);
void *scope_top_find(type_cxt_t *cxt, int type, void *key);
void *scope_top_insert(type_cxt_t *cxt, int type, void *key, void *value);
void *scope_search(type_cxt_t *cxt, int type, void *name);

void type_serialize_decl(token_t *decl, str_t *str);
#endif