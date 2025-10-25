from __future__ import annotations
import argparse
import sys
from pathlib import Path
import json
import hashlib
from time import time
import time
from typing import Dict, List, Optional, Tuple
import zlib

# from git import Tree

"""A simple implementation of a Git-like version control system in Python.
A Git has 4 Objects
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
Serialization --Git objects are serialized to a byte string before they are stored in the .pygit/objects directory.
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

"""
Commit Object Implementation:
What is a Commit Object? --A commit object in Git is a snapshot of the repository at a specific point in time.
It contains metadata about the commit, such as the author, committer, commit message, and a reference to the tree object that represents the state of the repository at the time of the commit.
A commit object also contains references to its parent commits, which allows Git to track the history of changes in the repository.
The commit object is identified by a unique SHA-1 hash, which is generated based on the content of the commit object.
The commit object is stored in the .pygit/objects directory of the repository, along with other Git objects such as blobs and trees.  
Why do we need Commit Object? --Commit objects are essential for version control in Git. They allow developers to track changes to the codebase over time, collaborate with others, and revert to previous versions of the code if necessary.   
Wht do we need hirarchy in Commit Object? --The hierarchy in commit objects allows Git to efficiently manage and navigate the history of changes in a repository. By organizing commits in a tree-like structure, Git can quickly identify the relationships between different commits, making it easier to track changes, merge branches, and resolve conflicts.
"""


class GitObject:
    def __init__(self, obj_type: str, content: bytes):
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
        header = (
            f"{self.type} {len(self.content)}\0".encode()
            # Creating the header for the object self.type is the type of the object(blob,tree,commit) and len(self.content) is the size of the content in bytes /0 is used to separate the header from the content. and encode() is used to convert the string to bytes.
        )
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
    def deserialize(cls, data: bytes) -> GitObject:
        """
        Deserialize the object from a byte string.
        1. Decompress the byte string using zlib decompression
        2. Split the resulting byte string into header and content
        3. Parse the header to get the object type and size
        4. Set the object type and content
        """
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx].decode()
        content = decompressed[null_idx + 1 :]

        obj_type, _ = header.split(" ")

        return cls(obj_type, content)

""" 
The BLOB class represents a blob object in Git.
it inherits from the GitObject class, which provides basic functionality for Git objects such as hashing and serialization.
"""
class Blob(GitObject):
    def __init__(self, content):
        super().__init__("blob", content)

    def get_content(self) -> bytes:
        return self.content


"""
The Tree class represents a tree object in Git.
It inherits from the GitObject class, which provides basic functionality for Git objects such as hashing and serialization.
in the init method we are initializing the entries attribute which is a list of tuples. Each tuple contains three elements: mode, name, and hash. all these represents a single entry in the tree object. which are string values.
and then we are serializing the entries using the _serialize_entries method and passing the serialized content to the super class(GitObject) init method along with the object type "tree".

The _serialize_entries method is used to serialize the entries attribute into a byte string format that can be stored in the Git object database.
Logic is: It iterates over the entries list, sorts them, and for each entry, it creates a byte string in the format <mode> <name>\0<hash>.
it encodes the mode and name as a string and converts the hash from hexadecimal to bytes.
then it concatenates all the byte strings together and returns the final serialized content.
and return type is bytes.

The add_entry method is used to add a new entry to the tree object. 
It takes three parameters: mode, name, and obj_hash. 
It appends a new tuple containing these values to the entries attribute and then updates the content attribute by re-serializing the entries.

@classmethod
The from_content method is used to create a Tree object from a byte string representation of the tree object.
It takes a single parameter content, which is a byte string containing the serialized tree data.
It initializes a new Tree object and then iterates over the content byte string to parse each entry.
It looks for the null byte (\0) to separate the mode and name from the hash.
It decodes the mode and name from bytes to strings and converts the hash from bytes to hexadecimal.
It appends each parsed entry as a tuple to the entries attribute of the Tree object.
"""
class Tree(GitObject):
    def __init__(self, entries:List[Tuple[str, str, str]] = None):
        self.entries = entries  or []# List of (mode, name, hash)
        content = self._serialize_entries()
        super().__init__("tree", content)
        
    def _serialize_entries(self) -> bytes:
        #<mode> <name>\0<hash>
        content = b""
        for mode, name ,obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode() 
            content += bytes.fromhex(obj_hash)
        return content
    
    def add_entry(self, mode:str, name:str, obj_hash:str) -> None:
        self.entries.append((mode, name, obj_hash))
        self.content = self._serialize_entries()
        
    @classmethod
    def from_content(cls, content:bytes) -> Tree:
        tree = cls()
        i=0
        while i < len(content):
            # parse name
            null_idx = content.find(b"\0", i)
            if null_idx == -1:
                break
            
            mode_name = content[i:null_idx].decode()
            mode,name = mode_name.split(" ",1) # split only on the first space
            
            # parse hash
            obj_hash = content[null_idx+1:null_idx+21].hex() # 20 bytes for SHA-1 hash 
            tree.entries.append((mode,name,obj_hash))
            i = null_idx + 21
            # parse mode
            # space_idx = content.find(b" ", i)
            # mode = content[i:space_idx].decode()
            # i = space_idx + 1
            
        return tree
            
            

""" 
The Class Commit represents a commit object in Git.
the Commit class inherits from the GitObject class, which provides basic functionality for Git objects such as hashing and serialization.
The Commit class has the following attributes:
- tree_hash: A string representing the hash of the tree object associated with the commit.
- parent_hashes: A list of strings representing the hashes of the parent commits.
- author: A string representing the author of the commit.
- committer: A string representing the committer of the commit.
- message: A string representing the commit message.
- timestamp: An integer representing the timestamp of the commit (default is the current time).

The Commit class has the following methods:
- __init__: The constructor method that initializes the commit object with the provided attributes and serializes the commit data.
- _serialize_commit: A private method that serializes the commit data into a byte string format.
- from_content: A class method that creates a Commit object from a byte string representation of the commit data.

"""
class Commit(GitObject):
    def __init__(self, tree_hash: str, parent_hashes: List[str], author: str,committer:str, message: str,timestamp:int = None):
        self.tree_hash = tree_hash
        self.parent_hashes = parent_hashes
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())
        # content = self._serialize_commit(tree_hash, parent_hashes, author, message)
        content = self._serialize_commit()
        super().__init__("commit", content)

    # def _serialize_commit(
    #     self, tree_hash: str, parent_hashes: List[str], author: str, message: str
    # ) -> bytes:
    #     lines = []
    #     lines.append(f"tree {tree_hash}")
    #     for parent_hash in parent_hashes:
    #         lines.append(f"parent {parent_hash}")
    #     lines.append(f"author {author}")
    #     lines.append(f"committer {author}")
    #     lines.append("")  # blank line before commit message
    #     lines.append(message)
    #     return "\n".join(lines).encode()
    
    
    """   
    Serialize the commit object to a byte string.
    the parent hashes are serialized by iterating over the list of parent hashes and appending a line for each parent hash to the lines list.
    The author and committer lines include the timestamp and timezone information (+0000 for UTC).
    The commit message is appended after a blank line.
    Finally, the lines are joined with newline characters and encoded to bytes before being returned.
    the return type is bytes.
    """
    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
        for parent in self.parent_hashes:
            lines.append(f"parent {parent}")
            
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("") # blank line before commit message 
        lines.append(self.message)
        
        return "\n".join(lines).encode()
    
    """  
    The class method from_content is used to create a Commit object from a byte string representation of the commit data.
    The method takes a single argument content, which is a byte string containing the serialized commit data
    The method decodes the byte string to a regular string and splits it into lines.
    It then iterates over the lines to extract the tree hash, parent hashes, author, committer, and commit message.
    The commit message is extracted by finding the index of the blank line that separates the header from the message and joining the remaining lines.
    Finally, the method creates and returns a new Commit object using the extracted data.
    The return type is Commit.
    This is basically done in the complete opposite way of _serialize_commit method.
    """
        
    @classmethod
    def from_content(cls, content:bytes) -> Commit:
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        committer = None
        message_start = 0
        # in_message = False
        
        # for line in lines:
        #     if in_message:
        #         message_lines.append(line)
        #     elif line.startswith("tree "):
        #         tree_hash = line[5:]
        #     elif line.startswith("parent "):
        #         parent_hashes.append(line[7:])
        #     elif line.startswith("author "):
        #         author = line[7:]
        #     elif line.startswith("committer "):
        #         committer = line[10:]
        #     elif line == "":
        #         in_message = True
                
        # message = "\n".join(message_lines)
        
        # return cls(tree_hash, parent_hashes, author,committer, message)
        
        """ 
        The for loop iterates over each line in the commit content.
        It checks the beginning of each line to determine its type (tree, parent, author, committer, or message).
        When it encounters a line starting with "tree ", it extracts the tree hash.
        When it encounters a line starting with "parent ", it appends the parent hash to the parent_hashes list.
        When it encounters a line starting with "author ", it splits the line to extract the author name and timestamp.
        Similarly, when it encounters a line starting with "committer ", it splits the line toextract the committer name.
        When it encounters a blank line, it marks the start of the commit message.
        
        i i have used enumerate to get the index of the line as well as the line itself.
        how does the enumerate work here? --The enumerate() function in Python adds a counter to an iterable and returns it as an enumerate object.
        This enumerate object can then be used directly in for loops or be converted into a list of tuples using the list() function.
        Each tuple contains a pair of values: the index (counter) and the corresponding value from the iterable.
        in our case the iterable is lines which is a list of strings.
        
        Finally, it joins the remaining lines after the blank line to form the commit message.
        """
        
        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ",2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("committer "):
                committer_parts = line[10:].rsplit(" ",2)
                committer = committer_parts[0]  
            elif line == "":
                message_start = i + 1
                break
            
        # Extract commit message Logic is : the above for loop will break when it encounters a blank line.
        message = "\n".join(lines[message_start:])

        # here we are creating the commit object using the extracted data.
        
        commit = cls(tree_hash, parent_hashes, author,committer, message,timestamp) 
        return commit   

class Repository:
    # Initialize the repository object
    # Set up paths for .pygit directory and its subdirectories/files
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        """
        Get the absolute path of the current directory
        The resolve() method in Python's pathlib module is used to get the absolute path of a given path. 
        Since we are initializing the repository in the current directory by default, we use Path(".") to represent the current directory.
        """
        self.git_dir = self.path / ".pygit"

        # .pygit/ojects --The objects directory in Git is used to store all the content of the repository, including commits, trees, and blobs.
        self.objects_dir = self.git_dir / "objects"

        # .pygit/refs --The refs directory in Git is used to store references to commits, branches, and tags in the repository.
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"

        # .Head File --The HEAD file in Git is a reference to the current branch or commit that you have checked out in your working directory.
        self.head_file = self.git_dir / "HEAD"

        # .pygit/index  --The index file in Git is a binary file that stores information about the files in your working directory and their corresponding entries in the Git repository.
        self.index_file = self.git_dir / "index"

    def init(self) -> bool:
        if self.git_dir.exists():
            print("Repository already exists.")
            return False

        # create directories
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()

        # create inital HEAD pointing to a branch
        self.head_file.write_text("ref: refs/heads/master\n")

        self.save_index({})

        # self.index_file.write_text(json.dumps({}, indent=4))

        print(f"Initialized empty Git repository in {self.git_dir}")
        return True

    def store_object(self, obj: GitObject):
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

    def save_index(self, index: dict[str, str]) -> None:
        self.index_file.write_text(json.dumps(index, indent=4))

    def add_file(self, path: str) -> None:
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
        9. The index file is stored in the .pygit directory of the repository.   
        """
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)

        print(f"Added file '{path}' to staging area.")

    def add_directory(self, path: str):
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

                # Create & store blob object

                content = file_path.read_bytes()
                blob = Blob(content)
                # blob = Blob(file_path.read_bytes())

                blob_hash = self.store_object(blob)

                # update index file
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

    def add_path(self, path: str) -> None:
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

    
    def load_object(self, obj_hash:str) -> GitObject:
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        
        if not obj_file.exists():
            raise FileNotFoundError(f"Object '{obj_hash}' not found.")
        
        return GitObject.deserialize(obj_file.read_bytes())
        
        # data = obj_file.read_bytes()
        # obj = GitObject.deserialize(data)
        # return obj
        
    
    def create_tree_from_index(self):
        index = self.load_index()
        if not index:
            tree = Tree()
            return self.store_object(tree)
        
        dirs = {}
        files = {}
        
        for file_path, blob_hash in index.items():
            parts = file_path.split("/",1)
            if len(parts) ==1:
                files[parts[0]] = blob_hash
            else:
                # dir_name = parts[0]
                # rest_path = parts[1]
                # if dir_name not in dirs:
                    # dirs[dir_name] = {}
                # dirs[dir_name][rest_path] = blob_hash
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}
                    
                current = dirs[dir_name]
                for part in parts[1:-1]:
                    if part not in current:
                        current[part] = {}
                        
                    current = current[part]
                    
                current[parts[-1]] = blob_hash
        
        def create_tree_recursive(entries_dict:Dict):
            # tree = Tree()
            # for name, value in entries_dict.items():
            #     if isinstance(value, dict):
            #         # directory
            #         subtree_hash = create_tree_recursive(value)
            #         tree.add_entry("40000", name, subtree_hash)
            #     else:
            #         # file
            #         tree.add_entry("100644", name, value)
            # return self.store_object(tree)
            tree = Tree()
            for name, blob_hash in entries_dict.items():
                if isinstance(blob_hash,str):
                    #file
                    tree.add_entry("100644", name,blob_hash)
                    
                if isinstance(blob_hash,dict):
                    subtree_hash = create_tree_recursive(blob_hash)
                    tree.add_entry("40000", name, subtree_hash)
                    
            return self.store_object(tree)
              
        root_entries = {**files}
        
        for dir_name, dir_contents in dirs.items():
            root_entries[dir_name] = dir_contents
        
        # Create and store the root tree from the aggregated entries and return its hash
        return create_tree_recursive(root_entries)
    
    
    def get_current_branch(self) -> str:
        if not self.head_file.exists():
            # raise FileNotFoundError("HEAD file not found. Is this a git repository?")
            return "master"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        
        return "HEAD"
    
    def get_branch_commit(self, current_branch:str):
        branch_file = self.heads_dir / current_branch
        if branch_file.exists():
            return branch_file.read_text().strip()
        
        return None
    
    def set_branch_commit(self, current_branch:str,commit_hash:str):
        branch_file = self.heads_dir / current_branch
        branch_file.write_text(commit_hash + "\n")
    
    def commit(self, message: str, author: str = "PyGit User <user@pygit.com>"):
        # Create a tree object from the current index (staging area)
        tree_hash = self.create_tree_from_index()
        
        current_branch = self.get_current_branch()
        
        parent_commit = self.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else []
        
        index = self.load_index()
        if not index:
            print("No changes to commit. working tree clean...")
            return None
        
        if parent_commit:
            parent_git_commit_obj = self.load_object(parent_commit)
            parent_commit_data = Commit.from_content(parent_git_commit_obj.content)
            if tree_hash == parent_commit_data.tree_hash:
                print("No changes to commit. working tree clean...")
                return None
            # print(f"Parent Commit: {parent_commit}")


        
        commit = Commit(
            tree_hash=tree_hash,
            parent_hashes=parent_hashes,
            author=author,
            committer=author,
            message=message
        )
        
        
        commit_hash = self.store_object(commit)
        
        self.set_branch_commit(current_branch, commit_hash)
        
        self.save_index({})
        print(f"Created Commit: {commit_hash} on branch '{current_branch}'.")
        return commit_hash
        


    def get_files_from_tree_recursive(self, tree_hash:str,prefix:str =""):
        files = set()
        try:
            tree_obj = self.load_object(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode == "40000":  # directory
                    sub_files = self.get_files_from_tree_recursive(obj_hash,full_name + "/")
                    files.update(sub_files)
                else:
                    files.add(full_name)
        except Exception as e:
            print(f"Warning: Could not read tree {tree_hash}: {e}")
            
        return files

    def checkout(self,branch:str, create_branch:bool = False):
        # branch_file = self.heads_dir / branch
        
        # if create_branch:
        #     if branch_file.exists():
        #         print(f"Branch '{branch}' already exists.")
        #         return
            
        #     # create new branch pointing to current commit
        #     current_branch = self.get_current_branch()
        #     current_commit = self.get_branch_commit(current_branch)
        #     if not current_commit:
        #         print("No commits in the current branch to base the new branch on.")
        #         return
            
        #     branch_file.write_text(current_commit + "\n")
        #     print(f"Created and switched to new branch '{branch}'.")
        # else:
        #     if not branch_file.exists():
        #         print(f"Branch '{branch}' does not exist.")
        #         return
            
        #     print(f"Switched to branch '{branch}'.")
        
        # # update HEAD to point to the new branch
        # self.head_file.write_text(f"ref: refs/heads/{branch}\n")
        
        previous_branch = self.get_current_branch()
        files_to_clear = set()
        try:
            previous_commit_hash = self.get_branch_commit(previous_branch)
            # if previous_commit_hash:
            #     previous_commit_obj = self.load_object(previous_commit_hash)
            #     previous_commit_data = Commit.from_content(previous_commit_obj.content)
            #     previous_tree_hash = previous_commit_data.tree_hash
            #     previous_tree_obj = self.load_object(previous_tree_hash)
            #     previous_tree_data = Tree.from_content(previous_tree_obj.content)
                
            #     for mode, name, obj_hash in previous_tree_data.entries:
            #         files_to_clear.add(name)
            if previous_commit_hash:
                prev_commit_object = self.load_object(previous_commit_hash)
                prev_commit = Commit.from_content(prev_commit_object.content)
                if prev_commit.tree_hash:
                    files_to_clear = self.get_files_from_tree_recursive(prev_commit.tree_hash)
                    
        except Exception:
            files_to_clear = set()
            
        branch_file = self.heads_dir / branch
        if not branch_file.exists():
            if create_branch:
                # current_branch = self.get_current_branch()
                # current_commit = self.get_branch_commit(current_branch)
                
                if previous_commit_hash:
                    self.set_branch_commit(branch, previous_commit_hash)
                    print(f"Created and switched to new branch '{branch}'.")
                else:
                    print("No commits yet , cannot create a branch .")
                    return
                
            else:
                print(f"Branch '{branch}' does not exist.")
                print(f"Use 'python pygit.py checkout -b {branch}' to create and switch to a new branch.")
                
        
        self.head_file.write_text(f"ref: refs/heads/{branch}\n")
        
        # restore working directory files from the new branch's latest commit
        self.restore_working_directory(branch, files_to_clear)
        
        print(f"Switched to branch '{branch}'.")



    def restore_tree(self, tree_hash:str, path:Path):
        tree_obj = self.load_object(tree_hash)
        tree = Tree.from_content(tree_obj.content)
        
        for mode, name, obj_hash in tree.entries:
            file_path = path / name
            
            if mode.startswith("100"):  # directory
                blob_obj = self.load_object(obj_hash)
                blob = Blob(blob_obj.content)
                file_path.write_bytes(blob.content)
            elif mode.startswith("400"):
                file_path.mkdir(exist_ok=True)
                subtree_files = self.restore_tree(obj_hash,file_path)
                # files.update(subtree_files)
                
        

    def restore_working_directory(self, branch:str, files_to_clear:set[str]):
        target_commit_hash = self.get_branch_commit(branch)
        if not target_commit_hash:
            return
        
        # remove the files that  are tracked in previous commit but not in the target commit
        for rel_path in sorted(files_to_clear):
            file_path = self.path / rel_path
            try:
                if file_path.is_file():
                    file_path.unlink()
            except Exception as e:
                print(f"Warning: Could not remove file '{rel_path}': {e}")
                
        target_commit_obj = self.load_object(target_commit_hash)
        target_commit = Commit.from_content(target_commit_obj.content)
        
        if target_commit.tree_hash:
            self.restore_tree(target_commit.tree_hash,self.path)
        
        self.save_index({}) # Modify it in future
        
        
    def branch(self,branch_name:str,delete:bool=False):
        if delete and branch_name:
            branch_file = self.heads_dir / branch_name
            if branch_file.exists():
                branch_file.unlink()
                print(f"Deleted Branch: {branch_name}")
            else:
                print(f"Branch {branch_name} not found")
            return
        current_branch = self.get_current_branch()
        if branch_name:
            current_commit = self.get_branch_commit(current_branch)
            if current_commit:
                self.set_branch_commit(branch_name,current_commit)
                print(f"Created branch {branch_name}")
            else:
                print(f"No Commits yets, cannot create a new branch")
        else:
            branches = []
            for branch_file in self.heads_dir.iterdir():
                if branch_file.is_file() and not branch_file.name.startswith("."):
                    branches.append(branch_file.name)
                    
            for branch in sorted(branches):
                current_marker = "* " if branch == current_branch else "  "
                print(f"{current_marker} {branch}")
            
                


def main():
    # What is an arg parser? --argparse is a module in Python's standard library that provides a way to handle command-line arguments passed to a script.
    # what is parser? --A parser is an object that is responsible for parsing command-line arguments.
    # what is subparser? --A subparser is a way to create sub-commands for a command-line application.
    parser = argparse.ArgumentParser(
        description="Git Clone. - A simple script that can execute a basic  git cmd's like init,add commits etc."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command --This command is used to initialize a new git repository in the current directory.
    init_parser = subparsers.add_parser("init", help="Initialize a new git repository")

    # add Command  --This command only use to add files and directories to staging area but it can't commit them.
    add_parser = subparsers.add_parser(
        "add", help="Add file and Directories to staging area"
    )
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

    # Commit Command --This command is used to commit the staged changes to the repository.
    commit_parser = subparsers.add_parser(
        "commit", help="Commit staged changes to the repository"
    )

    commit_parser.add_argument(
        "-m",
        "--message",
        required=True, 
        help="Commit message"
    )
    
    commit_parser.add_argument(
        "-a",
        "--author",
        # required=True, 
        help="Author name & email."
    )
    
    # Checkout Command --This command is used to checkout a specific branch or commit in the repository.
    checkout_parser = subparsers.add_parser("checkout", help = "Move / create a new branch and check it out.")
    checkout_parser.add_argument("branch",help="Branch to switch to.")
    checkout_parser.add_argument("-b", "--create-branch", action="store_true", help="Create and switch to a  new branch and check it out.")
    
    
    
    # branch command 
    branch_parser = subparsers.add_parser("branch",help="Create a new branch")
    branch_parser.add_argument("name",nargs="?")
    branch_parser.add_argument("-d","--delete",action="store_true",help="Delete a branch")
    
    # parse the arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return
    repo = Repository()  # --initialize repository object in the current directory
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
        
        elif args.command == "commit":
            if not repo.git_dir.exists():
                print("Not a git repository. Please run 'init' command first.")
                return

            # author = args.author if args.author else "Anonymous <>"
            author = args.author or "PyGit user <user@pygit.com>"
            repo.commit(args.message,author)
            # print(f"Committing staged changes with message: {args.message}")
        
        elif args.command == "checkout":
            if not repo.git_dir.exists():
                print("Not a git repository. Please run 'init' command first.")
                return
            
            repo.checkout(args.branch, args.create_branch)
        
        elif args.command == "branch":
            if not repo.git_dir.exists():
                print(f"Not a directory. please run 'init' command first...")
                return
            
            repo.branch(args.name,args.delete)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    # print(args)


main()
