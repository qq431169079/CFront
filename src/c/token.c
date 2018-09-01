
#include "token.h"

// Converts the token type to a string
const char *token_typestr(token_type_t type) {
  switch(type) {
    case T_LPAREN: return "T_LPAREN";
    case T_RPAREN: return "T_RPAREN";
    case T_LSPAREN: return "T_LSPAREN";
    case T_RSPAREN: return "T_RSPAREN";
    case T_DOT: return "T_DOT";
    case T_ARROW: return "T_ARROW";
    case T_INC: return "T_INC";
    case T_DEC: return "T_DEC";
    case T_PLUS: return "T_PLUS";
    case T_MINUS: return "T_MINUS";
    case T_LOGICAL_NOT: return "T_LOGICAL_NOT";
    case T_BIT_NOT: return "T_BIT_NOT";
    case T_STAR: return "T_STAR";
    case T_AND: return "T_AND";
    case T_SIZEOF: return "T_SIZEOF";
    case T_DIV: return "T_DIV";
    case T_MOD: return "T_MOD";
    case T_LSHIFT: return "T_LSHIFT";
    case T_RSHIFT: return "T_RSHIFT";
    case T_LESS: return "T_LESS";
    case T_GREATER: return "T_GREATER";
    case T_LEQ: return "T_LEQ";
    case T_GEQ: return "T_GEQ";
    case T_EQ: return "T_EQ";
    case T_NEQ: return "T_NEQ";
    case T_BIT_XOR: return "T_BIT_XOR";
    case T_BIT_OR: return "T_BIT_OR";
    case T_LOGICAL_AND: return "T_LOGICAL_AND";
    case T_LOGICAL_OR: return "T_LOGICAL_OR";
    case T_QMARK: return "T_QMARK";
    case T_COLON: return "T_COLON";
    case T_ASSIGN: return "T_ASSIGN";
    case T_PLUS_ASSIGN: return "T_PLUS_ASSIGN";
    case T_MINUS_ASSIGN: return "T_MINUS_ASSIGN";
    case T_MUL_ASSIGN: return "T_MUL_ASSIGN";
    case T_DIV_ASSIGN: return "T_DIV_ASSIGN";
    case T_MOD_ASSIGN: return "T_MOD_ASSIGN";
    case T_LSHIFT_ASSIGN: return "T_LSHIFT_ASSIGN";
    case T_RSHIFT_ASSIGN: return "T_RSHIFT_ASSIGN";
    case T_AND_ASSIGN: return "T_AND_ASSIGN";
    case T_OR_ASSIGN: return "T_OR_ASSIGN";
    case T_XOR_ASSIGN: return "T_XOR_ASSIGN";
    case T_COMMA: return "T_COMMA";
    case T_LCPAREN: return "T_LCPAREN";
    case T_RCPAREN: return "T_RCPAREN";
  }

  return NULL;
}

const char *token_symstr(token_type_t type) {
  switch(type) {
    case T_LPAREN: return "(";
    case T_RPAREN: return ")";
    case T_LSPAREN: return "[";
    case T_RSPAREN: return "]";
    case T_DOT: return ".";
    case T_ARROW: return "->";
    case T_INC: return "++";
    case T_DEC: return "--";
    case T_PLUS: return "+";
    case T_MINUS: return "-";
    case T_LOGICAL_NOT: return "!";
    case T_BIT_NOT: return "~";
    case T_STAR: return "*";
    case T_AND: return "&";
    case T_SIZEOF: return "sizeof";
    case T_DIV: return "/";
    case T_MOD: return "%";
    case T_LSHIFT: return "<<";
    case T_RSHIFT: return ">>";
    case T_LESS: return "<";
    case T_GREATER: return ">";
    case T_LEQ: return "<=";
    case T_GEQ: return ">=";
    case T_EQ: return "==";
    case T_NEQ: return "!=";
    case T_BIT_XOR: return "^";
    case T_BIT_OR: return "|";
    case T_LOGICAL_AND: return "&&";
    case T_LOGICAL_OR: return "||";
    case T_QMARK: return "?";
    case T_COLON: return ":";
    case T_ASSIGN: return "=";
    case T_PLUS_ASSIGN: return "+=";
    case T_MINUS_ASSIGN: return "-=";
    case T_MUL_ASSIGN: return "*=";
    case T_DIV_ASSIGN: return "/+";
    case T_MOD_ASSIGN: return "%=";
    case T_LSHIFT_ASSIGN: return "<<=";
    case T_RSHIFT_ASSIGN: return ">>=";
    case T_AND_ASSIGN: return "&=";
    case T_OR_ASSIGN: return "|=";
    case T_XOR_ASSIGN: return "^=";
    case T_COMMA: return ",";
    case T_LCPAREN: return "{";
    case T_RCPAREN: return "}";
  }

  return NULL;
}

// Fill an operator token object according to its type
// Return value:
//   1. If input is not '\0' then return the next unread character
//   2. If input is '\0' then return NULL
//   3. If not valid operator could be found then token type is T_ILLEGAL
//      and the pointer is not changed
// Note: 
//   1. sizeof() is treated as a keyword by the tokenizer
//   2. // and /* and */ and // are not processed
//   3. { and } are processed here
char *token_get_op(char *s, token_t *token) {
  switch(s[0]) {
    case '\0': return NULL;
    // Must be single character operator
    case ',': token->type = T_COMMA; return s + 1;                      // ,
    case '(': token->type = T_LCPAREN; return s + 1;                    // (
    case ')': token->type = T_RCPAREN; return s + 1;                    // )
    case '[': token->type = T_LSPAREN; return s + 1;                    // [
    case ']': token->type = T_RSPAREN; return s + 1;                    // ]
    case '{': token->type = T_LCPAREN; return s + 1;                    // {
    case '}': token->type = T_RCPAREN; return s + 1;                    // }
    case '.': token->type = T_DOT; return s + 1;                        // .
    case '?': token->type = T_QMARK; return s + 1;                      // ?
    case ':': token->type = T_COLON; return s + 1;                      // :
    case '~': token->type = T_BIT_NOT; return s + 1;                    // ~
    // Multi character
    case '-':
      switch(s[1]) {
        case '-': token->type = T_DEC; return s + 2;                    // --
        case '=': token->type = T_MINUS_ASSIGN; return s + 2;           // -=
        case '>': token->type = T_ARROW; return s + 2;                  // ->
        case '\0': 
        default: token->type = T_MINUS; return s + 1;                   // -
      }
    case '+':
      switch(s[1]) {
        case '+': token->type = T_INC; return s + 2;                    // ++
        case '=': token->type = T_PLUS_ASSIGN; return s + 2;            // +=
        case '\0': 
        default: token->type = T_PLUS; return s + 1;                    // +
      }
    case '*':
      switch(s[1]) {
        case '=': token->type = T_MUL_ASSIGN; return s + 2;             // *=
        case '\0': 
        default: token->type = T_STAR; return s + 1;                    // *
      }
    case '/':
      switch(s[1]) {
        case '=': token->type = T_DIV_ASSIGN; return s + 2;             // /=
        case '\0': 
        default: token->type = T_DIV; return s + 1;                     // /
      }
    case '%':
      switch(s[1]) {
        case '=': token->type = T_MOD_ASSIGN; return s + 2;             // %=
        case '\0': 
        default: token->type = T_MOD; return s + 1;                     // %
      }
    case '^':
      switch(s[1]) {
        case '=': token->type = T_XOR_ASSIGN; return s + 2;             // ^=
        case '\0': 
        default: token->type = T_BIT_XOR; return s + 1;                 // ^
      }
    case '<':
      switch(s[1]) {
        case '=': token->type = T_LEQ; return s + 2;                    // <=
        case '<': 
          switch(s[2]) {
            case '=': token->type = T_LSHIFT_ASSIGN; return s + 3;      // <<=
            case '\0':
            default: token->type = T_LSHIFT; return s + 2;              // <<
          } 
        case '\0': 
        default: token->type = T_LESS; return s + 1;                    // <
      }
    case '>':
      switch(s[1]) {
        case '=': token->type = T_GEQ; return s + 2;                    // >=
        case '>': 
          switch(s[2]) {
            case '=': token->type = T_RSHIFT_ASSIGN; return s + 3;      // >>=
            case '\0':
            default: token->type = T_RSHIFT; return s + 2;              // >>
          } 
        case '\0': 
        default: token->type = T_GREATER; return s + 1;                 // >
      }
    case '=':
      switch(s[1]) {
        case '=': token->type = T_EQ; return s + 2;                     // ==
        case '\0': 
        default: token->type = T_ASSIGN; return s + 1;                  // =
      }
    case '!':
      switch(s[1]) {
        case '=': token->type = T_NEQ; return s + 2;                     // !=
        case '\0': 
        default: token->type = T_LOGICAL_NOT; return s + 1;              // !
      }
    case '&':
      switch(s[1]) {
        case '&': token->type = T_LOGICAL_AND; return s + 2;             // &&
        case '=': token->type = T_AND_ASSIGN; return s + 2;              // &=
        case '\0': 
        default: token->type = T_AND; return s + 1;                      // &
      }
    case '|':
      switch(s[1]) {
        case '|': token->type = T_LOGICAL_OR; return s + 2;             // ||
        case '=': token->type = T_OR_ASSIGN; return s + 2;              // |=
        case '\0': 
        default: token->type = T_BIT_OR; return s + 1;                  // |
      }
  }

  token->type = T_ILLEGAL;
  return s;
}

// Returns an identifier, including both keywords and user defined identifier
// Same rule as the get_op call
char *token_get_ident(char *s, token_t *token) {
  char ch = *s;
  if(ch == '\0') {
    return NULL;
  } else if(isalpha(ch) || ch == '_') {
    char *end = s + 1;
    while(isalnum(*end) || *end == '_') end++;
    char *buffer = (char *)malloc(sizeof(char) * (end - s + 1));
    strcpy(buffer, s, end - s);
    token->type = T_IDENT;
    token->str = buffer;
  }
  
  token->type = T_ILLEGAL;
  return s;
}