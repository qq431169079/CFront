

#include "parse_exp.h"
#include "parse_decl.h"

parse_decl_cxt_t *parse_decl_init(char *input) {
  return parse_exp_init(input);
}

void parse_decl_free(parse_decl_cxt_t *cxt) {
  parse_exp_free(cxt);
}

// Whether the token is a type modifier (qualifier/specifier)
int parse_decl_istype(parse_decl_cxt_t *cxt, token_t *token) {
  if(kwd_isdecl(token->type)) return 1;
  else if(token->type == T_IDENT && ht_find(cxt->udef_types, token->str) != HT_NOTFOUND) return 1;
  return 0;
}

// Whether the next token is decl. Note that this is context dependent, and thus 
// makes C syntex not context-free. Need to check typedef table
// Note: The following tokens are considered as part of a type expression:
//   1. ( ) [ ] *  2. specifiers, qualifiers and types 3. typedef'ed names
// struct, union and enum are recognized here, but they need another parser
int parse_decl_isdecl(parse_decl_cxt_t *cxt, token_t *token) {
  token_type_t type = token->type;
  if(parse_exp_isempty(cxt, OP_STACK) && (type == T_RPAREN || type == T_RSPAREN)) return 0; 
  else if(kwd_isdecl(token->type)) return 1;
  else if(token->type == T_IDENT && ht_find(cxt->udef_types, token->str) != HT_NOTFOUND) return 1;
  switch(token->type) {
    case T_LPAREN: case T_RPAREN: case T_STAR: case T_LSPAREN: case T_RSPAREN: return 1;
  }
  return 0;
}

// Same rule as parse_exp_next_token()
token_t *parse_decl_next_token(parse_decl_cxt_t *cxt) {
  token_t *token = token_alloc();
  char *before = cxt->s;
  cxt->s = token_get_next(cxt->s, token);
  if(cxt->s == NULL || !parse_decl_isdecl(cxt, token)) {
    cxt->s = before;
    token_free(token);
    return NULL;
  }
  switch(token->type) {
    case T_LPAREN:   // The only symbol that can have two meanings
      token->type = cxt->last_active_stack == OP_STACK ? EXP_LPAREN : EXP_FUNC_CALL; break;
    case T_RPAREN: token->type = EXP_RPAREN; break;
    case T_STAR: token->type = EXP_DEREF; break;
    case T_LSPAREN: token->type = EXP_ARRAY_SUB; break;
    case T_RSPAREN: token->type = EXP_RSPAREN; break;
    case T_IDENT: if(ht_find(cxt->udef_types, token->str) != HT_NOTFOUND) token->type = T_UDEF_TYPE; break;
  }
  return token;
}

token_t *parse_decl(parse_decl_cxt_t *cxt) {
  assert(parse_exp_size(cxt, OP_STACK) == 0 && parse_exp_size(cxt, AST_STACK) == 0);
  // Artificial node that is not in the token stream
  token_t *root = token_alloc();
  root->type = T_DECL;
  parse_exp_shift(cxt, OP_STACK, root);
  while(1) {
    token_t *token = parse_decl_next_token(cxt);
    if(token == NULL) {
      // TODO: REDUCE UNTIL STACK EMPTY
      // TODO: RETURN THE LAST TOKEN
    }

    token_t *top = cxt->
    switch()
  }
}