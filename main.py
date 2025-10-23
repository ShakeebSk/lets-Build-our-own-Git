from __future__ import annotations
import argparse
import sys
from pathlib import Path
import json
import hashlib
import zlib

"""A simple implementation of a Git-like version control system in Python.
A Hit has 4 Objects
1. Blob --Binary Large Object --It is used to store the content of files.
2. Tree --It is used to represent the directory structure of the repository.
3. Commit --It is used to represent a snapshot of the repository at a specific point in time.
4. Tag --It is used to create a reference to a specific commit in the repository.

The first three objects (Blob, Tree, Commit) are the core objects of Git, while Tag is an optional object that can be used to create references to specific commits.
In our Project we are only going to implement the Blob,Tree & object .
We are going to skip the Tag object for now.
We are going to do the following commands:
1. init --Initialize a new git repository
2. add --Add files and directories to the staging area
3. commit --Commit the staged changes to the repository


For the Implementation of these commands we are going to create a Repository class that will handle all the operations related to the repository.

git object implementation:
We are going to create a base class called GitObject that will be inherited by the Blob,Tree & Commit classes.
Beacuse all these classes will have some common functionality like hashing,compressing,decompressing etc. 
Hash Function --Git uses SHA-1 hashing algorithm to create a unique hash for each object.
In real Git SHA-1 produces a 40-character hexadecimal string, but for simplicity, we can use a shorter hash in our implementation.
The hash is generated based on the content of the object and its type (blob, tree, commit).
The hash is used to uniquely identify the object in the repository.
In the real GIT they have migrated from SHA-1 to SHA-256 which is more secure but for our implementation we are going to use SHA-1 only.
What is SHA-1? --SHA-1 (Secure Hash Algorithm 1) is a cryptographic hash function that takes an input and produces a fixed-size 160-bit (20-byte) hash value, typically represented as a 40-character hexadecimal string.
SHA-1 is widely used in various security applications and protocols, including TLS and SSL, PGP, SSH, and IPsec.
However, SHA-1 is no longer considered secure against well-funded attackers, and its use is being phased out in favor of more secure hash functions like SHA-256 and SHA-3.
What is SHA-256? --SHA-256 (Secure Hash Algorithm 256) is a cryptographic hash function that produces a fixed-size 256-bit (32-byte) hash value, typically represented as a 64-character hexadecimal string.
SHA-256 is part of the SHA-2 family of hash functions, which were designed to provide improved security over the earlier SHA-1 algorithm.
SHA-256 is widely used in various security applications and protocols, including TLS and SSL, PGP, SSH, and IPsec.
SHA-256 is considered to be more secure than SHA-1 and is recommended for use in new applications.

What is Zlib Compression? --Zlib is a software library used for data compression. It provides in-memory compression and decompression functions, as well as support for reading and writing compressed files.
Zlib uses the DEFLATE compression algorithm, which is a combination of LZ77 and Huffman coding.
Zlib is widely used in various applications and protocols, including PNG image format, HTTP compression, and ZIP file format.
Serialization --Git objects are serialized to a byte string before they are stored in the .git/objects directory.
Serialization is the process of converting an object into a byte string that can be stored in a file or transmitted over a network.--Compress the Object and Store it,.
Deserialization --Deserialization is the process of converting a byte string back into an object. --Read the Object from the file and Decompress it.
The GitObject class will have the following methods:
    Base class for Git objects (Blob, Tree, Commit).
    1. hash_object --This method is used to hash the object using SHA-1 algorithm.
    2. compress_object --This method is used to compress the object using zlib compression.
    3. decompress_object --This method is used to decompress the object using zlib decompression.
    4. store_object --This method is used to store the object in the .pygit/objects directory.
    5. read_object --This method is used to read the object from the .pygit/objects directory.
    6. get_object_type --This method is used to get the type of the object (blob, tree, commit).
    7. get_object_size --This method is used to get the size of the object.
    8. serialize --This method is used to serialize the object to a byte string.
    9. deserialize --This method is used to deserialize the object from a byte string.
    10. create_from_data --This method is used to create an object from raw data.
    11. create_from_file --This method is used to create an object from a file.
    12. create_from_hash --This method is used to create an object from a hash.
    13. get_hash --This method is used to get the hash of the object.
    14. get_data --This method is used to get the raw data of the object.
    15. get_size --This method is used to get the size of the object.
    16. get_type --This method is used to get the type of the object.
    17. save --This method is used to save the object to the .pygit/objects directory.
    18. load --This method is used to load the object from the .pygit/objects directory.
    19. delete --This method is used to delete the object from the .pygit/objects directory.
    20. exists --This method is used to check if the object exists in the .pygit/objects directory.
    21. list_objects --This method is used to list all objects in the .pygit/objects directory.
    22. find_objects --This method is used to find objects in the .pygit/objects directory based on certain criteria.
    23. update_object --This method is used to update the object in the .pygit/objects directory.
    24. copy_object --This method is used to copy the object in the .pygit/objects directory.
    25. move_object --This method is used to move the object in the .pygit/objects directory.
    26. rename_object --This method is used to rename the object in the .py git/objects directory.
    27. get_object_path --This method is used to get the path of the object in the .pygit/objects directory.        
    
"""


class GitObject:
    def __init__(self,obj_type:str, content:bytes):
        self.type = obj_type
        self.content = content
    
    def hash(self) -> str:
        """
        What is HASH? --A hash is a fixed-size string of characters that is generated by a hash function based on the input data.
        In Git, a hash is used to uniquely identify an object (such as a commit, tree, or blob) based on its content.
        The hash is generated using the SHA-1 hashing algorithm, which produces a 40-character hexadecimal string.
        The hash is calculated by taking the content of the object, prepending a header that includes the object type and size, and then applying the SHA-1 algorithm to the resulting byte string.
        HashFormat -- f(<type> <size>\0<content>)
        <type> -- object type (blob, tree, commit)
        <size> -- size of the content in bytes
        <content> -- raw content of the object
        """
        header = f"{self.type} {len(self.content)}\0".encode() #Creating the header for the object self.type is the type of the object(blob,tree,commit) and len(self.content) is the size of the content in bytes /0 is used to separate the header from the content. and encode() is used to convert the string to bytes.
        # return hashlib.sha256(header + self.content).hexdigest() --Using SHA-256 if u want more security / use this instead of SHA-1 
        return hashlib.sha1(header + self.content).hexdigest()
    
    def serialize(self) -> bytes:
        """
        Serialize the object to a byte string for storage.
        The serialization format is: <type> <size>\0<content>
        where <type> is the object type (blob, tree, commit),
        <size> is the size of the content in bytes,
        and <content> is the raw content of the object.
        1. Create the header for the object
        2. Concatenate the header and content
        3. Compress the resulting byte string using zlib compression
        4. Return the compressed byte string
        What is Zlib Compression? --Zlib is a software library used for data compression. It provides in-memory compression and decompression functions, as well as support for reading and writing compressed files.
        Zlib uses the DEFLATE compression algorithm, which is a combination of LZ77 and Huffman coding.
        Zlib is widely used in various applications and protocols, including PNG image format, HTTP compression, and ZIP file format.
        """
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)
    
    @classmethod
    # def deserialize(self, data:bytes) -> "GitObject":
    def deserialize(cls, data:bytes) -> GitObject:
        """
        Deserialize the object from a byte string.
        1. Decompress the byte string using zlib decompression
        2. Split the resulting byte string into header and content
        3. Parse the header to get the object type and size
        4. Set the object type and content
        """
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx + 1:]
        
        obj_type, _ = header.split(" ")
        
        return cls(obj_type, content)
    
class Blob(GitObject):
    def __init__(self, content):
        super().__init__("blob", content)
        
    def get_content(self) -> bytes:
        return self.content
    
    

class Repository:
    # Initialize the repository object
    # Set up paths for .pygit directory and its subdirectories/files
    def __init__(self,path="." ):
        self.path = Path(path).resolve()  
        """
        Get the absolute path of the current directory
        The resolve() method in Python's pathlib module is used to get the absolute path of a given path. 
        Since we are initializing the repository in the current directory by default, we use Path(".") to represent the current directory.
        """
        self.git_dir = self.path / ".pygit"
        
        
        #.git/ojects --The objects directory in Git is used to store all the content of the repository, including commits, trees, and blobs.
        self.objects_dir = self.git_dir / "objects"
        
        #.git/refs --The refs directory in Git is used to store references to commits, branches, and tags in the repository.
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"
        
        #.Head File --The HEAD file in Git is a reference to the current branch or commit that you have checked out in your working directory.
        self.head_file = self.git_dir / "HEAD"
        
        #.git/index  --The index file in Git is a binary file that stores information about the files in your working directory and their corresponding entries in the Git repository.
        self.index_file = self.git_dir / "index"
        
    def init(self) -> bool:
        if self.git_dir.exists():
            print("Repository already exists.")
            return False
        
        #create directories
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()
        
        #create inital HEAD pointing to a branch
        self.head_file.write_text("ref: refs/heads/master\n")
        
        self.save_index({})
        
        # self.index_file.write_text(json.dumps({}, indent=4))
        
        print(f"Initialized empty Git repository in {self.git_dir}")
        return True
    
    def store_object(self, obj:GitObject):
        obj_hash = obj.hash()
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        
        if not obj_file.exists():
            obj_dir.mkdir(exist_ok=True)
            serialized_data = obj.serialize()
            obj_file.write_bytes(serialized_data)
            
        return obj_hash
    
    def load_index(self) -> dict[str, str]:
        if not self.index_file.exists():
            return {}
        
        try:
            return json.loads(self.index_file.read_text())
        
        except:
            return {}
        # index_content = self.index_file.read_text()
        # return json.loads(index_content)
        
    def save_index(self, index:dict[str,str]) -> None:
        self.index_file.write_text(json.dumps(index, indent=4))
    
    def add_file(self,path:str) -> None:
        full_path = self.path / path
        
        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"File '{path}' Not Found.")
        """
        1. Read the file content
        """
        
        content = full_path.read_bytes()
        
        """
        2. Create BLOB object in .pygit/objects Binary Large Object. 
            This BLOB object is stored in the .pygit/objects directory.
            This BlOB object is going to be Compressed and Hashed.
            So Once the Object are created we have to store them in the .pygit/objects directory.
        3. Store the BLOB object in database(.pygit/object) 
        """
        blob = Blob(content)
        blob_hash = self.store_object(blob)
        """
        4. Update the index file to include the new file.
        5. The index file is a binary file that stores information about the files in your working directory and their corresponding entries in the Git repository.
        6. The index file is used by Git to keep track of the files that are staged for the next commit.
        7. The index file is updated whenever you run the git add command to stage changes for the next commit.
        8. The index file is also used by Git to determine which files have been modified, added, or deleted since the last commit.
        9. The index file is stored in the .git directory of the repository.   
        """
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        
        print(f"Added file '{path}' to staging area.")
        
    
    def add_directory(self, path:str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"File '{path}' Not Found.")
        
        if not full_path.is_dir():
            raise NotADirectoryError(f"Path '{path}' is not a directory.")
        index = self.load_index()
        added_count = 0
        # recursively traverse the directory and add all files
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".pygit" in file_path.parts:
                    continue  # Skip files in the .pygit directory
                
                
                #Create & store blob object
                
                content = file_path.read_bytes()
                blob = Blob(content)
                # blob = Blob(file_path.read_bytes())
                
                blob_hash = self.store_object(blob)
                
                #update index file
                relative_path = file_path.relative_to(self.path)
                index[str(relative_path)] = blob_hash
                added_count += 1
                
                
        self.save_index(index)
        
        if added_count > 0:
            print(f"Added {added_count} files from dorectory '{path}' to staging area.")
        else:
            print(f"Directory :'{path}' already up to date.")
        
        # print(f"Added directory '{path}' to staging area.")
        # Create blob objects for each file and store them in .pygit/objects
        # Update the index file to include all files in the directory
        
        
    
    def add_path(self, path:str) -> None:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path '{path}' does not exist. ")
        
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            # for item in full_path.iterdir():
            #     relative_item_path = item.relative_to(self.path)
            #     self.add_path(str(relative_item_path))
            self.add_directory(path)
        else:
            raise ValueError(f"Path '{path}' is neither a file nor a directory.")
        

def main():
    #What is an arg parser? --argparse is a module in Python's standard library that provides a way to handle command-line arguments passed to a script.
    #what is parser? --A parser is an object that is responsible for parsing command-line arguments.
    #what is subparser? --A subparser is a way to create sub-commands for a command-line application.
    parser = argparse.ArgumentParser(
        description="Git Clone. - A simple script that can execute a basic  git cmd's like init,add commits etc."
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )
    
    #init command --This command is used to initialize a new git repository in the current directory.
    init_parser = subparsers.add_parser("init", help="Initialize a new git repository")
    
    #add Command  --This command only use to add files and directories to staging area but it can't commit them.
    add_parser = subparsers.add_parser("add", help="Add file and Directories to staging area")
    """
    let's say in the git we can use git add . --this will add all files in the current directory or 
    we can add a single file like git add file.txt or 
    multiple file like git add file1.txt file2.txt dir1/ dir2/
    But above all these cases we can use nargs="+" to accept one or more arguments from the command line.
    So here in our add command we are using nargs="+" to accept one or more file and directory paths to add to the staging area.
    There are other options like nargs="*" which means zero or more arguments, nargs="?" which means zero or one argument. 
    But in our case we are using nargs="+" because we want to make sure that at least one file or directory is provided to add to the staging area.
    """
    
    add_parser.add_argument("paths", nargs="+", help="Files and directories to add")
    
    #parse the arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    repo = Repository() #--initialize repository object in the current directory
    try:
        if args.command == "init":
            
            if not repo.init():
                print("Repository already exists.")
                return
            # print("Initializing a new git repository...")
        elif args.command == "add":
            if not repo.git_dir.exists():
                print("Not a git repository. Please run 'init' command first.")
                
                return
            
            # print(f"Adding files and directories to staging area: {args.paths}")
            for path in args.paths:
                repo.add_path(path)
                
            """ 
            Now we have to add the function add() in the Repository class to handle the adding of files and directories to the staging area.
            So there are multiple thing we have to 
            Step 1: Check if the file/directory even exists if not then we have to raise an error/Exception.
            Step 2: If it is a file,we need to store it in Index. we have to read its content and create a blob object in the .pygit/objects directory.
            Step 3: If it is a directory,we need to list out all the file that are present in that Directory recursively.
            Because there is a possibility that a folder has a folder which has a folder and so on. So
            we have to recursively add all the files and sub-directories in it.
            """
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    
    # print(args)

main()



