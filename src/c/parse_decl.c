

#include "parse_exp.h"
#include "parse_decl.h"

parse_decl_cxt_t *parse_decl_init(char *input) { return parse_exp_init(input); }
void parse_decl_free(parse_decl_cxt_t *cxt) { parse_exp_free(cxt); }

// Whether the token could start a declaration, i.e. being a type or modifier
int parse_decl_istype(parse_decl_cxt_t *cxt, token_t *token) {
  if(token->decl_prop & DECL_MASK) return 1; // built-in type & modifier
  else if(token->type == T_IDENT && 
          ht_find(cxt->udef_types, token->str) != HT_NOTFOUND) return 1; // udef types
  return 0;
}

// Same rule as parse_exp_next_token()
// Note: The following tokens are considered as part of a type expression:
//   1. ( ) [ ] *  2. specifiers, qualifiers and types 3. typedef'ed names
token_t *parse_decl_next_token(parse_decl_cxt_t *cxt) {
  token_t *token = token_alloc();
  char *before = cxt->s;
  int valid = 1;
  cxt->s = token_get_next(cxt->token_cxt, cxt->s, token);
  if(cxt->s == NULL || 
     (parse_exp_isempty(cxt, OP_STACK) && (token->type == T_RPAREN || token->type == T_RSPAREN)))
    valid = 0;
  else
    switch(token->type) {
      case T_LPAREN:   // The only symbol that can have two meanings
        token->type = cxt->last_active_stack == OP_STACK ? EXP_LPAREN : EXP_FUNC_CALL; break;
      case T_RPAREN: token->type = EXP_RPAREN; break;
      case T_STAR: token->type = EXP_DEREF; break;
      case T_LSPAREN: token->type = EXP_ARRAY_SUB; break;
      case T_RSPAREN: token->type = EXP_RSPAREN; break;
      case T_IDENT: // Identifiers are allowed but udef types must be marked as types
        if(ht_find(cxt->udef_types, token->str) != HT_NOTFOUND) { 
          token->type = T_UDEF; token->decl_prop |= DECL_UDEF;
        } 
        break;
      default: // For keywords and other symbols. Only allow DECL keywords (see token.h)
        if(!(token->decl_prop & DECL_MASK)) valid = 0;
    }
  if(!valid) {
    cxt->s = before;
    token_free(token);
    return NULL;
  }
  return token;
}

// Could be at most one AST on the current virtual stack
void parse_decl_shift(parse_decl_cxt_t *cxt, int stack_id, token_t *token) {
  if(stack_id == AST_STACK && parse_exp_size(cxt, AST_STACK) != 0) 
    error_row_col_exit(token->offset, "At most one name is allowed in a declaration\n");
  parse_exp_shift(cxt, stack_id, token);
}

token_t *parse_decl_reduce(parse_decl_cxt_t *cxt, token_t *root) {
  if(parse_exp_size(cxt, OP_STACK) == 0) return NULL;
  token_t *top = stack_pop(cxt->stacks[OP_STACK]);
  if(parse_exp_size(cxt, AST_STACK) == 0) { // Unnamed declaration
    if(top->type == EXP_DEREF) {
      assert(root->type == T_DECL);
      root->type = T_ABS_DECL;
    } else {
      error_row_col_exit(top->offset, "")
    }
  }
  

}

token_t *parse_decl(parse_decl_cxt_t *cxt) {
  assert(parse_exp_size(cxt, OP_STACK) == 0 && parse_exp_size(cxt, AST_STACK) == 0);
  // Artificial node that is not in the token stream
  token_t *root = token_alloc();
  root->type = T_DECL;
  while(1) {
    token_t *token = parse_decl_next_token(cxt);
    if(token == NULL) {
      // TODO: REDUCE UNTIL STACK EMPTY
      // TODO: RETURN THE LAST TOKEN
    }

    assert(parse_exp_size(cxt, OP_STACK) != 0);
    token_t *top = stack_peek(cxt->stacks[OP_STACK]);
    switch(top->type) {
      case T_DECL: { 
        if(token->decl_prop & DECL_MASK) {
          decl_prop_t after = token_decl_apply(token, top->decl_prop);
          if(after == DECL_INVALID) 
            error_row_col_exit(token->offset, 
                               "Incompatible type specifier \"%s\" with declaration \"%s\"\n", 
                               token->str, token_decl_print(top->decl_prop));
          top->decl_prop = after;
          if(token->type == T_STRUCT || token->type == T_UNION || token->type == T_ENUM) {
            // TODO: EXTRA PROCESSING
            assert(0);
          } else {
            token_free(token);
          }
        } else if(token->type == EXP_DEREF) {
          parse_exp_shift(cxt, OP_STACK, token);
        } else if(0) {
          // process [
        } else if(0) {
          if(ast == NULL)
        }
      }
      case EXP_DEREF: break;
    }
  }
}