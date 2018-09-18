
#ifndef _BIN_TREE_H
#define _BIN_TREE_H

#include "hashtable.h"

// Binary tree node type
typedef struct btnode {
  void *key, *value;
  struct btnode *left, *right;
} btnode_t;

typedef struct {
  int size;
  cmp_cb_t cmp;
  eq_cb_t eq;
  btnode_t *root;
} bintree_t;

#endif