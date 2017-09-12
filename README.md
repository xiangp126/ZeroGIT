# Git Plumbing Toolkit
    Some Instructions or Scripts from Plumbing Angle for Better Understanding of Git Principles.

## Blob Object
    git object was referenced by sha1 hashcode, how is this code generated and reprented.

    every time you use git add, the file was hashed as a whole and was stored in .git/object/'hashcode'

    git has three types of data structures, blob/commit/tree
    take sample.c as example

### HashCode

* Part One 
``` bash

    $ cat sample.c | wc
          5      12      77
    namely 77 characters total. 
    the blob data structure is just like "blob ${chars_total}\0${Contents}"
    we suppose this sample.c will be stored as "blob 77\0${Contents}" in a object file.

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
    and it was right there.

```
* Part Two
```bash
    contents stored in the object file was compressed by zlib. In linux we can use 
    gunzip to decompress it.
    
    printf "\x1f\x8b\x08\x00\x00\x00\x00\x00" | cat - .git/objects/be/e80fe26e979b11a5ed10f4802c6aa9fbee3375 | gzip -d 2>/dev/null
    blob 77#include <stdio.h>

    int main(int argc, const char *argv[]) {
            return 0;
    }

    It was correct.

```

## Tree Object

### Index Object
    So much enhanced by this part, and you can use my self-writted script: 
    after git add sample.c we see the .git/index

    virl@virl:.git$ cat index
    KY�����m�
             �K����M���n�����,j���3sample.c�'m~�3 (���/�λvirl@virl:.git$

    virl@virl:.git$ xxd index
    0000000: 4449 5243 0000 0002 0000 0001 59ac c102  DIRC........Y...
    0000010: 190d 104b 59ac c0fd 0fbc d36d 0000 fc00  ...KY......m....
    0000020: 0ba2 024b 0000 81a4 0000 03e8 0000 03e8  ...K............
    0000030: 0000 004d bee8 0fe2 6e97 9b11 a5ed 10f4  ...M....n.......
    0000040: 802c 6aa9 fbee 3375 0008 7361 6d70 6c65  .,j...3u..sample
    0000050: 2e63 0000 da27 6d06 7e90 3320 ceac 7f28  .c...'m.~.3 ...(
    0000060: 88ac d72f e28b cebb                      .../....

## Usage

```bash    
    > python3 parse_index.py .git/index
    > 

```    

## Reference 

[Git Plumbing](http://git.oschina.net/progit/9-Git-%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86.html)

[index-format](https://github.com/git/git/blob/master/Documentation/technical/index-format.txt)

[What does the git index contain Exactly](https://stackoverflow.com/questions/4084921/what-does-the-git-index-contain-exactly/4086986#4086986)

