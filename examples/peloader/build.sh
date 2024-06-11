x86_64-w64-mingw32-gcc -shared -O0 -o FooBar.dll FooBar.c -Wl,--out-implib,FooBar.a -nostdlib
x86_64-w64-mingw32-gcc -nostdlib main.c -L. -lFooBar -o main.exe
