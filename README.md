# Git Plumbing Toolkit
    Some Instructions or Scripts from Plumbing Angle for Better Understanding of Git Principles.

## Blob
    git object was referenced by sha1 hashcode, how is this code generated and reprented.

    every time you use git add, the file was hashed as a whole and was stored in .git/object/'hashcode'

    git has three types of data structures, blob/commit/tree
    take sample.c as example

### HashCode

    ``` bash

    $ cat sample.c | wc
          5      12      77

    ```
    namely 77 characters total. 
    the blob data structure is just like "blob ${chars_total}\0${Contents}"
    we suppose this sample.c will be stored as "blob 77\0${Contents}" to a object file.


    ``` bash
    echo -ne "blob 77\0" | cat - sample.c
    blob 77#include <stdio.h>

    int main(int argc, const char *argv[]) {
            return 0;
    }
    echo -ne "blob 77\0" | cat - sample.c | shasum -a 1
    bee80fe26e979b11a5ed10f4802c6aa9fbee3375  -

    git add sample.c
    find .git/objects/ -type f
    .git/objects/be/e80fe26e979b11a5ed10f4802c6aa9fbee3375

    ```

    and it was right there.

![next1](http://img1.tuicool.com/2E36nuQ.png!web)


## Usage

```bash    
    > make
    g++ -Wall -g3 -std=c++11 -c kmp.cpp -o kmp.o
    g++ -Wall -g3 -std=c++11 -c demo.cpp -o demo.o
    g++ kmp.o demo.o -o demo

    > ./demo 
    Original Pattern: BCDABDE
    Original String:  BBCABCDABABCDABCDABDET
    Next Array:  -1  0  0  0  0  1  0
     Optimized:  -1  0  0  0 -1  1  0

     0123456789012345678901       [ index = 14 ]
     BBCABCDABABCDABCDABDET
                   BCDABDE

```    

## Reference 

[Git Plumbing](http://git.oschina.net/progit/9-Git-%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86.html)
