
// Typedef must specify a name
//typedef 
const static register enum enum_struct {
  A = 1,
  B = 2,
  C = 3
};

static const volatile register int aaa = 0x012345678ABCDEFL;

void f();

/*
 * main() - The entry point of the program
 */
// Note that declaration list followed by function header is not supported
int main(int argc, char **argv, ...) /* int x, y, z; */ {
  // This is the declaration without an identifier (WTF do we allow this?)
  //static const register long; 
  
  static const volatile register int * const * (*xyz)(int(*)(), long *, char()) = C;
  long x = 1 & xyz;
  void *c;
  typedef int aa;
  // This struct is used to store data
  static typedef struct struct_type {
    int a;
    char b : 20;   // 20 bit field
    long c;
  } aa, bb, cc;
  
  int long register typedef ;
    
  printf("Hello, world!\n");
  
  a.a = 20UL;
  a.b = 0x12345 >> (5 & 0xFFFFFFFF);
  a.c = 0777;
  b.b = '\n';
  
  return 0;
}
