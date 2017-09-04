# KMP Algorithm Implementation
    K.M.P Algorithm was very useful in sub string search context.

## Basic KMP 
    You May Know Well about the Next Array From Below Two Figures.

![next1](http://img1.tuicool.com/2E36nuQ.png!web)

![next2](http://img1.tuicool.com/qYN3u2v.png!web)

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
