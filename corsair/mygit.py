#!/usr/bin/python3

import sys, os, zlib, struct, math, argparse
import getopt, hashlib, collections, binascii

# ./.mygit, same as ./.git
baseName = '.mygit'

# Data for one entry in the git index (.git/index)
''' Parse Index File.
      | 0           | 4            | 8           | C              |
      |-------------|--------------|-------------|----------------|
    0 | DIRC        | Version      | File count  | Ctime          | 0
      | Nano-Sec    | Mtime        | Nano-Sec    | Device         |
    2 | Inode       | Mode         | UID         | GID            | 2
      | File size   | Entry SHA-1    ...           ...            |
    4 | ...           ...          | Flags  | File Name(\0x00)    | 4
      | Ext-Sig     | Ext-Size     | Ext-Data (Ext was optional)  | 
    6 | Checksum      ...            ...           ...            | 6

-->> 
    2 | Mode - 32 bit     |      4 | Flags - 16 bit                
      |-------------------|        |-------------------------|
      | 16-bit unknown    |        | 1-bit assume-valid flag |
      | 4-bit object type |        | 1-bit extended flag     |
      | 3-bit unused      |        | 2-bit stage             |
      | 9-bit unix perm   |        | 12-bit name length      |
'''
# IndexEntry = <class '__main__.IndexEntryType'>
IndexEntry = collections.namedtuple('IndexEntryType', [
    'ctime_s', 'ctime_n', 'mtime_s', 'mtime_n', 'dev', 'ino', 'mode', 'uid',
    'gid', 'size', 'sha1', 'flags', 'path'])

def readIndex():
    ''' Read index file, return list of IndexEntry object. '''
    try:
         data = readFile(os.path.join(baseName, 'index'))
    except FileNotFoundError:
        return []

    # calculate checksum leaving the last 20 bytes(checksum itself).
    # data[0:20], left included, right not.
    checkSum = hashlib.sha1(data[0:-20]).digest()
    assert checkSum == data[-20:], "Error, Invalid Index CheckSum."
    sigh, ver, fileCnt = struct.unpack('!4sLL', data[0:12])
    assert sigh == b'DIRC', \
            'Error, Invalid Index Signature {}'.format(sigh)
    assert ver == 2, 'Error, Unknown Index Version {}'.format(ver)

    # omit header and checksum part.
    allEntryPart = data[12:-20]
    entries = []
    # per entry data length.
    entryDataLen = 62

    i = 0
    while i + entryDataLen < len(allEntryPart):
        # not included, as j in [i:j]
        fieldEnd = i + entryDataLen
        ''' fields = (1505637351, 0, 1505637351, 0, 16777220, 35245842, 
                    33188, 502, 20, 83, 
             b'\x0c\x02Q\xe0\x9eya\xf9\x92s\xa5\xa8\xe9S\xf6Q\xeb_=Y', 8)
        '''
        fields = struct.unpack('>LLLLLLLLLL20sH', allEntryPart[i:fieldEnd])
        # parse path name, multiple b'\x00' terminatered.
        pathLen = fields[-1]
        entryLen = (((entryDataLen + pathLen) // 8) + 1) * 8
        path = allEntryPart[fieldEnd:fieldEnd + pathLen]
        # (path.decode('utf-8'),) convert str to tuple.
        ''' fields + (path.decode('utf-8'),) = 
                (1505637351, 0, 1505637351, 0, 16777220, 35245842, 33188, 
                 502, 20, 83, 
                 b'\x0c\x02Q\xe0\x9eya\xf9\x92s\xa5\xa8\xe9S\xf6Q\xeb_=Y', 
                 8, 'main.cpp')
        '''
        ''' IndexEntry(*(fields + (path.decode(),))) = 
            IndexEntry(ctime_s=1505637351, ctime_n=0, mtime_s=1505637351, 
            mtime_n=0, dev=16777220, ino=35245842, mode=33188, uid=502,
            gid=20, size=83, 
            sha1=b'\x0c\x02Q\xe0\x9eya\xf9\x92s\xa5\xa8\xe9S\xf6Q\xeb_=Y',
            flags=8, path='main.cpp')
        '''
        entry = IndexEntry(*(fields + (path.decode(),)))
        entries.append(entry)
        i += entryLen

    assert len(entries) == fileCnt, "Error, File Count Not Match."
    return entries

def getStatus():
    ''' Get status of working tree, return (changedPaths, newPaths, delPath)
        as a tuple. '''
    paths = set()
    ''' > for root, dirs, files in os.walk('.'):
          ...  dirs[:] = [d for d in dirs if d != '.mygit']
          ...  print("root = ", root, ", dirs = ", dirs, ", files = ", files)
          ...
          root =  . , dirs =  ['deer', 'lala'] , files =  ['pygit.py', 
                                    'main.cpp', 'parse_index.py', 'mygit.py']
          root =  ./deer , dirs =  [] , files =  ['data.txt', 'raw.txt']
          root =  ./lala , dirs =  [] , files =  []
    '''
    for root, dirs, files in os.walk('.'):
        # omit dir '.mygit'
        dirs[:] = [d for d in dirs if d != baseName]
        for file in files:
            path = os.path.join(root, file)
            if path.startswith('./'):
                path = path[2:]
            paths.add(path)
    ''' entries_by_path = {e.path: e for e in read_index()} = 
        {'parse_index.py': IndexEntry(..., ..., path='parse_index.py'), 
        'main.cpp': IndexEntry(..., ..., path='main.cpp')}
    '''
    # type(entries_by_path) = <class 'dict'>, convert to Key -> Value.
    entriesByPath = {entry.path: entry for entry in readIndex()}
    # entryPaths = {'parse_index.py', 'main.cpp'}
    entryPaths = set(entriesByPath)
    
    changedFiles = set()
    # check if SHA1 of the file has changed.
    # binascii.hexlify(entries_by_path['main.cpp'].sha1).decode('utf-8') =
    # '0c0251e09e7961f99273a5a8e953f651eb5f3d59'
    for path in (paths & entryPaths):
        sha1 = hashObject(path, 'blob', write = False)
        oriSHA1 = \
            binascii.hexlify(entriesByPath[path].sha1).decode('utf-8')
        if sha1 != oriSHA1:
            changedFiles.add(path)
    # only two set() can minus each other.
    newFiles = paths - entryPaths
    deletedFiles = entryPaths - paths
    #print(changedFiles, newFiles, deletedFiles)
      
    return (sorted(changedFiles), sorted(newFiles), sorted(deletedFiles))

def status():
    ''' The upper function of getStatus(). In case the latter is too large. '''
    changed, new, deleted = getStatus()
    if changed:
        print('changed files:')
        for path in changed:
            print('   ', path)
    if new:
        print('new files:')
        for path in new:
            print('   ', path)
    if deleted:
        print('deleted files:')
        for path in deleted:
            print('   ', path)

def add(paths):
    ''' Add files to 'stage', same as 'git add main.cpp'. '''
    entries = []
    # type(paths) = <class 'list'>
    for path in paths:
        sha1 = hashObject(path, 'blob')
        ''' os.stat(path) = os.stat_result(st_mode=33204, st_ino=195100843, 
            st_dev=64512, st_nlink=1, st_uid=1000, st_gid=1000, st_size=82,
            st_atime=1505454057, st_mtime=1505453832, st_ctime=1505453832). 
        '''
        st = os.stat(path)
        # Default encoding is 'utf-8'
        # 0 0 00 {12 bit} -> 'name length', 16 bit total.
        flags = len(path.encode('utf-8'))
        # only case lowest 12 bit(name length) not overflow.
        assert flags < (1 << 12)
        entry = IndexEntry(
                int(st.st_ctime), 0, int(st.st_mtime), 0, st.st_dev, st.st_ino,
                st.st_mode, st.st_uid, st.st_gid, st.st_size, bytes.fromhex(sha1),
                flags, path)
        entries.append(entry)
        writeIndex(entries)

def writeIndex(entries):
    ''' Write IndexEntry objects to mygit index file. '''
    packedEntries = []
    for entry in entries:
        # >: big-endian, std. size & alignment
        # L:unsigned long
        # s:string (array of char)
        # H:unsigned short
        # these can be preceded by a decimal repeat count
        # 20s, 20 char-length of string
        # type(entryHead) = <class 'bytes'>
        entryData = struct.pack('>LLLLLLLLLL20sH', 
                entry.ctime_s, entry.ctime_n, entry.mtime_s, entry.mtime_n,
                entry.dev, entry.ino, entry.mode, entry.uid, entry.gid,
                entry.size, entry.sha1, entry.flags)
        # 'main.cpp' -> b'main.cpp'
        path = entry.path.encode('utf-8')
        ''' 1-8 nul bytes as necessary to pad the this entry to a multiple of 
            eight bytes while keeping the name NUL-terminated. 
        '''
        # math.floor 70 / 8 = 8.75, 70 // 8 = 8 
        # len(entryData) = 62 = 10 * 4 + 20 + 2
        entryDataLen = len(entryData)
        pathLen = len(path)
        # calculate how many b'\x00' will be appeded after file name.
        trueLen = (math.floor((entryDataLen + pathLen) / 8) + 1) * 8
        packedEntry = entryData + path + b'\x00' * (trueLen - entryDataLen - pathLen)
        packedEntries.append(packedEntry)
    # | DIRC        | Version      | File count  | ...       | 
    packHeader = struct.pack('>4sLL', b'DIRC', 2, len(entries))
    # The result is returned as a new bytes object.
    # Example: b'.'.join([b'ab', b'pq', b'rs']) -> b'ab.pq.rs'.
    # bytes + b''.join(list) => bytes
    allData = packHeader + b''.join(packedEntries)
    indexSha1 = hashlib.sha1(allData).digest()
    allData += indexSha1
    writeFile(os.path.join(baseName, 'index'), allData)

def hashObject(fName, objType = 'blob', write = False):
    ''' Compute sha1 hashcode of specified file and write data to object
        directory if needed.  '''
    ''' The sample form stored in object file: 
                       '${objType} ${len_of_char}' + '\0' + ${true_content}. '''
    fRd = open(fName, "rb")
    data = fRd.read()
    # Unicode-objects must be encoded before hashing
    # type(header) = <class 'bytes'>
    header = "{} {}".format(objType, len(data)).encode('utf-8')
    fullData = header + b'\x00' + data
    # 0c0251e09e7961f99273a5a8e953f651eb5f3d59
    sha1 = hashlib.sha1(fullData).hexdigest()

    if write:
        # .git/objects/0c/0251e09e7961f99273a5a8e953f651eb5f3d59
        path = os.path.join('.git', 'objects', sha1[:2], sha1[2:])
        dirName = os.path.dirname(path)
        if not os.path.exists(path):
            os.makedirs(dirName, exist_ok = True)
        # zlib compress the data to be stored.
        zlibData = zlib.compress(fullData)
        writeFile(path, zlibData)

    return sha1

def readFile(path):
    ''' Read file as bytes at given path. '''
    with open(path, "rb") as file:
        return file.read()

def writeFile(path, data):
    ''' write bytes to file at given path. '''
    # type(data) = <class 'bytes'>
    with open(path, "wb") as file:
        file.write(data)

def init(repo):
    ''' Init .mygit associated files. '''
    global baseName
    # if base dir not exists, just create it.
    if not os.path.exists(baseName):
        os.makedirs(baseName, exist_ok = True)
        # ./.mygit/{objects, refs}
        for name in ['objects', 'refs', 'refs/heads']:
            newDir = os.path.join(baseName, name)
            os.makedirs(newDir, exist_ok = True)
        # ./.mygit/HEAD
        writePath = baseName + '/HEAD'
        writeFile(writePath, b'ref: refs/heads/master')
        print("Initialized Empty Repository {}".format(baseName))
    else:
        print("Warnning: Repository {} Not Empty.".format(baseName))

def usage():
    print("fix me usage")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest='command', metavar='command')
    sub_parsers.required = True

    sub_parser = sub_parsers.add_parser('add',
            help='add file(s) to index')
    sub_parser.add_argument('paths', nargs='+', metavar='path',
            help='path(s) of files to add')

    sub_parser = sub_parsers.add_parser('cat-file',
            help='display contents of object')
    valid_modes = ['commit', 'tree', 'blob', 'size', 'type', 'pretty']
    sub_parser.add_argument('mode', choices=valid_modes,
            help='object type (commit, tree, blob) or display mode (size, '
                 'type, pretty)')
    sub_parser.add_argument('hash_prefix',
            help='SHA-1 hash (or hash prefix) of object to display')

    sub_parser = sub_parsers.add_parser('commit',
            help='commit current state of index to master branch')
    sub_parser.add_argument('-a', '--author',
            help='commit author in format "A U Thor <author@example.com>" '
                 '(uses GIT_AUTHOR_NAME and GIT_AUTHOR_EMAIL environment '
                 'variables by default)')
    sub_parser.add_argument('-m', '--message', required=True,
            help='text of commit message')

    sub_parser = sub_parsers.add_parser('diff',
            help='show diff of files changed (between index and working '
                 'copy)')

    sub_parser = sub_parsers.add_parser('hash-object',
            help='hash contents of given path (and optionally write to '
                 'object store)')
    sub_parser.add_argument('path',
            help='path of file to hash')
    sub_parser.add_argument('-t', choices=['commit', 'tree', 'blob'],
            default='blob', dest='type',
            help='type of object (default %(default)r)')
    sub_parser.add_argument('-w', action='store_true', dest='write',
            help='write object to object store (as well as printing hash)')

    sub_parser = sub_parsers.add_parser('init',
            help='initialize a new repo')
#    sub_parser.add_argument('repo',
#            help='directory name for new repo')

    sub_parser = sub_parsers.add_parser('ls-files',
            help='list files in index')
    sub_parser.add_argument('-s', '--stage', action='store_true',
            help='show object details (mode, hash, and stage number) in '
                 'addition to path')

    sub_parser = sub_parsers.add_parser('push',
            help='push master branch to given git server URL')
    sub_parser.add_argument('git_url',
            help='URL of git repo, eg: https://github.com/benhoyt/pygit.git')
    sub_parser.add_argument('-p', '--password',
            help='password to use for authentication (uses GIT_PASSWORD '
                 'environment variable by default)')
    sub_parser.add_argument('-u', '--username',
            help='username to use for authentication (uses GIT_USERNAME '
                 'environment variable by default)')

    sub_parser = sub_parsers.add_parser('status',
            help='show status of working copy')

    args = parser.parse_args()
    if args.command == 'add':
        add(args.paths)
    elif args.command == 'cat-file':
        try:
            cat_file(args.mode, args.hash_prefix)
        except ValueError as error:
            print(error, file=sys.stderr)
            sys.exit(1)
    elif args.command == 'commit':
        commit(args.message, author=args.author)
    elif args.command == 'diff':
        diff()
    elif args.command == 'hash-object':
        sha1 = hashObject(args.path, args.type, write=args.write)
        print(sha1)
    elif args.command == 'init':
        init('.')
    elif args.command == 'ls-files':
        ls_files(details=args.stage)
    elif args.command == 'push':
        push(args.git_url, username=args.username, password=args.password)
    elif args.command == 'status':
        status()
    else:
        assert False, 'unexpected command {!r}'.format(args.command)

#    try:
#        options, argv = getopt.getopt(sys.argv[1:], "h:t")
#        print("options = ", options)
#        print("argv = ", argv)
#    except getopt.GetoptError:
#        print("Usage Error. Exit Now.")
#        sys.exit()
#    for name, value in options:
#        if name in ("-h", "--help"):
#            usage()
#        if name in ("-t", "--type"):
#            print('type is----', value)
#    
#    command = argv[0]
#    if command == 'init':
#        init()        
#    elif command == 'status':
#        print(command)
#        # status()
#    elif command == 'hash-object':
#        for prefix, type in options:
#            if prefix in ("-t", "--type"):
#                print('type is----', value)
#                sha1 = hashObject(argv[1], type, True)
#                print(sha1)
#            else:
#                print("Syntax Error.")
#        print("Nothing Happened.")
#    elif command == 'add':
#        add(argv[1:])
#
