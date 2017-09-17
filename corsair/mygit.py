#!/usr/bin/python3

import sys, os, zlib, struct
import getopt, hashlib, collections

# ./.mygit, same as ./.git
baseName = '.mygit'

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
        entryHead = struct.pack('>LLLLLLLLLL20sH', 
                entry.ctime_s, entry.ctime_n, entry.mtime_s, entry.mtime_n,
                entry.dev, entry.ino, entry.mode, entry.uid, entry.gid,
                entry.size, entry.sha1, entry.flags)

        # math.floor  //



    # | DIRC        | Version      | File count  | Ctime          | 
    packHeader = struct.pack('>4sLL', b'DIRC', 2, len(entries))
    # determin how many b'\x00' will be appeded after file name.
    allData = packHeader + b''

    """Write list of IndexEntry objects to git index file."""
    packed_entries = []
    for entry in entries:
        entry_head = struct.pack('!LLLLLLLLLL20sH',
                entry.ctime_s, entry.ctime_n, entry.mtime_s, entry.mtime_n,
                entry.dev, entry.ino, entry.mode, entry.uid, entry.gid,
                entry.size, entry.sha1, entry.flags)
        path = entry.path.encode()
        length = ((62 + len(path) + 8) // 8) * 8
        packed_entry = entry_head + path + b'\x00' * (length - 62 - len(path))
        packed_entries.append(packed_entry)
    header = struct.pack('!4sLL', b'DIRC', 2, len(entries))
    all_data = header + b''.join(packed_entries)
    digest = hashlib.sha1(all_data).digest()
    write_file(os.path.join('.git', 'index'), all_data + digest)

def add(paths):
    ''' Add files to 'stage', same as 'git add main.cpp'. '''
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

   --->> 
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
        print(entries)

def readFile(path):
    ''' Read file as bytes at given path. '''
    with open(path, "rb") as file:
        return file.read()

def writeFile(path, data):
    ''' write bytes to file at given path. '''
    # type(data) = <class 'bytes'>
    with open(path, "wb") as file:
        file.write(data)

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

def init():
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
    print("fix me")

if __name__ == '__main__':

    try:
        options, argv = getopt.getopt(sys.argv[1:], "h:t", ["help","type="])
    except getopt.GetoptError:
        print("Usage Error. Exit Now.")
        sys.exit()
    for name, value in options:
        if name in ("-h", "--help"):
            usage()
        if name in ("-t", "--type"):
            print('type is----', value)
    
    command = argv[0]
    if command == 'init':
        init()        
    elif command == 'status':
        print(command)
        # status()
    elif command == 'hash-object':
        sha1 = hashObject(argv[1], "blob", True)
        print(sha1)
    elif command == 'add':
        print(argv[1:])
        add(argv[1:])

