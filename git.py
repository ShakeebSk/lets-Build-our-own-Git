from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple, Set
import zlib
import difflib


class GitObject:
    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content

    def hash(self) -> str:
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()

    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def deserialize(cls, data: bytes) -> GitObject:
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx].decode()
        content = decompressed[null_idx + 1 :]
        obj_type, _ = header.split(" ")
        return cls(obj_type, content)

class Blob(GitObject):
    def __init__(self, content: bytes):
        super().__init__("blob", content)

class Tree(GitObject):
    def __init__(self, entries: List[Tuple[str, str, str]] = None):
        self.entries = entries or []
        content = self._serialize_entries()
        super().__init__("tree", content)

    def _serialize_entries(self) -> bytes:
        content = b""
        for mode, name, obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)
        return content

    def add_entry(self, mode: str, name: str, obj_hash: str):
        self.entries.append((mode, name, obj_hash))
        self.content = self._serialize_entries()

    @classmethod
    def from_content(cls, content: bytes) -> Tree:
        tree = cls()
        i = 0
        while i < len(content):
            null_idx = content.find(b"\0", i)
            if null_idx == -1:
                break
            mode_name = content[i:null_idx].decode()
            mode, name = mode_name.split(" ", 1)
            obj_hash = content[null_idx + 1 : null_idx + 21].hex()
            tree.entries.append((mode, name, obj_hash))
            i = null_idx + 21
        return tree

class Commit(GitObject):
    def __init__(
        self,
        tree_hash: str,
        parent_hashes: List[str],
        author: str,
        committer: str,
        message: str,
        timestamp: int = None,
    ):
        self.tree_hash = tree_hash
        self.parent_hashes = parent_hashes
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())
        content = self._serialize_commit()
        super().__init__("commit", content)

    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
        for parent in self.parent_hashes:
            lines.append(f"parent {parent}")
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("")
        lines.append(self.message)
        return "\n".join(lines).encode()

    @classmethod
    def from_content(cls, content: bytes) -> Commit:
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        committer = None
        timestamp = int(time.time())
        message_start = 0

        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ", 2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("committer "):
                committer_parts = line[10:].rsplit(" ", 2)
                committer = committer_parts[0]
            elif line == "":
                message_start = i + 1
                break

        message = "\n".join(lines[message_start:])
        commit = cls(tree_hash, parent_hashes, author, committer, message, timestamp)
        return commit

class Tag(GitObject):
    def __init__(
        self,
        object_hash: str,
        object_type: str,
        tag_name: str,
        tagger: str,
        message: str,
        timestamp: int = None,
    ):
        self.object_hash = object_hash
        self.object_type = object_type
        self.tag_name = tag_name
        self.tagger = tagger
        self.message = message
        self.timestamp = timestamp or int(time.time())
        content = self._serialize_tag()
        super().__init__("tag", content)

    def _serialize_tag(self):
        lines = [
            f"object {self.object_hash}",
            f"type {self.object_type}",
            f"tag {self.tag_name}",
            f"tagger {self.tagger} {self.timestamp} +0000",
            "",
            self.message
        ]
        return "\n".join(lines).encode()

    @classmethod
    def from_content(cls, content: bytes) -> Tag:
        lines = content.decode().split("\n")
        object_hash = None
        object_type = None
        tag_name = None
        tagger = None
        timestamp = int(time.time())
        message_start = 0

        for i, line in enumerate(lines):
            if line.startswith("object "):
                object_hash = line[7:]
            elif line.startswith("type "):
                object_type = line[5:]
            elif line.startswith("tag "):
                tag_name = line[4:]
            elif line.startswith("tagger "):
                tagger_parts = line[7:].rsplit(" ", 2)
                tagger = tagger_parts[0]
                timestamp = int(tagger_parts[1])
            elif line == "":
                message_start = i + 1
                break

        message = "\n".join(lines[message_start:])
        return cls(object_hash, object_type, tag_name, tagger, message, timestamp)


class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".git"
        self.objects_dir = self.git_dir / "objects"
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"
        self.tags_dir = self.ref_dir / "tags"
        self.head_file = self.git_dir / "HEAD"
        self.index_file = self.git_dir / "index"
        self.merge_head_file = self.git_dir / "MERGE_HEAD"
        self.merge_msg_file = self.git_dir / "MERGE_MSG"
        self.stash_file = self.git_dir / "stash"

    def init(self) -> bool:
        if self.git_dir.exists():
            return False
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()
        self.tags_dir.mkdir(exist_ok=True)
        self.head_file.write_text("ref: refs/heads/master\n")
        self.save_index({})
        print(f"Initialized empty Git repository in {self.git_dir}")
        return True

    def store_object(self, obj: GitObject) -> str:
        obj_hash = obj.hash()
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        if not obj_file.exists():
            obj_dir.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())
        return obj_hash

    def load_index(self) -> Dict[str, str]:
        if not self.index_file.exists():
            return {}
        try:
            return json.loads(self.index_file.read_text())
        except:
            return {}


    def save_index(self, index: Dict[str, str]):
        self.index_file.write_text(json.dumps(index, indent=2))

    def add_file(self, path: str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        content = full_path.read_bytes()
        blob = Blob(content)
        blob_hash = self.store_object(blob)
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        print(f"Added {path}")

    def add_directory(self, path: str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Directory {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")
        index = self.load_index()
        added_count = 0
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".git" in file_path.parts:
                    continue
                content = file_path.read_bytes()
                blob = Blob(content)
                blob_hash = self.store_object(blob)
                rel_path = str(file_path.relative_to(self.path))
                index[rel_path] = blob_hash
                added_count += 1
        self.save_index(index)
        if added_count > 0:
            print(f"Added {added_count} files from directory {path}")
        else:
            print(f"Directory {path} already up to date")


    def add_path(self, path: str) -> None:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")



    def load_object(self, obj_hash: str) -> GitObject:
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        if not obj_file.exists():
            raise FileNotFoundError(f"Object {obj_hash} not found")
        return GitObject.deserialize(obj_file.read_bytes())


    def create_tree_from_index(self):
        index = self.load_index()
        if not index:
            tree = Tree()
            return self.store_object(tree)

        dirs = {}
        files = {}

        for file_path, blob_hash in index.items():
            parts = file_path.split("/")
            if len(parts) == 1:
                files[parts[0]] = blob_hash
            else:
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}
                current = dirs[dir_name]
                for part in parts[1:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = blob_hash

        def create_tree_recursive(entries_dict: Dict):
            tree = Tree()
            for name, blob_hash in entries_dict.items():
                if isinstance(blob_hash, str):
                    tree.add_entry("100644", name, blob_hash)
                if isinstance(blob_hash, dict):
                    subtree_hash = create_tree_recursive(blob_hash)
                    tree.add_entry("40000", name, subtree_hash)
            return self.store_object(tree)

        root_entries = {**files}
        for dir_name, dir_contents in dirs.items():
            root_entries[dir_name] = dir_contents

        return create_tree_recursive(root_entries)


    def get_current_branch(self) -> str:
        if not self.head_file.exists():
            return "master"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        return "HEAD"


    def is_detached_head(self) -> bool:
        if not self.head_file.exists():
            return False
        head_content = self.head_file.read_text().strip()
        return not head_content.startswith("ref:")

    def get_head_commit(self) -> Optional[str]:
        if not self.head_file.exists():
            return None
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            branch = head_content[16:]
            return self.get_branch_commit(branch)
        else:
            return head_content

    def get_branch_commit(self, branch: str) -> Optional[str]:
        branch_file = self.heads_dir / branch
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None

    def set_branch_commit(self, branch: str, commit_hash: str):
        branch_file = self.heads_dir / branch
        branch_file.write_text(commit_hash + "\n")



    def commit(self, message: str, author: str = "PyGit User <user@pygit.com>"):
        tree_hash = self.create_tree_from_index()
        
        # Check for merge in progress
        parent_hashes = []
        if self.merge_head_file.exists():
            # Merge commit
            current_head = self.get_head_commit()
            merge_head = self.merge_head_file.read_text().strip()
            if current_head:
                parent_hashes = [current_head, merge_head]
            else:
                parent_hashes = [merge_head]
            
            # Use merge message if available
            if self.merge_msg_file.exists() and not message:
                message = self.merge_msg_file.read_text().strip()
        else:
            # Normal commit
            current_head = self.get_head_commit()
            parent_hashes = [current_head] if current_head else []

        index = self.load_index()
        if not index:
            print("nothing to commit, working tree clean")
            return None

        if parent_hashes and len(parent_hashes) == 1:
            parent_git_commit_obj = self.load_object(parent_hashes[0])
            parent_commit_data = Commit.from_content(parent_git_commit_obj.content)
            if tree_hash == parent_commit_data.tree_hash:
                print("nothing to commit, working tree clean")
                return None

        commit = Commit(
            tree_hash=tree_hash,
            parent_hashes=parent_hashes,
            author=author,
            committer=author,
            message=message,
        )
        commit_hash = self.store_object(commit)

        # Update HEAD
        if self.is_detached_head():
            self.head_file.write_text(commit_hash + "\n")
            print(f"Created commit {commit_hash} (detached HEAD)")
        else:
            current_branch = self.get_current_branch()
            self.set_branch_commit(current_branch, commit_hash)
            print(f"Created commit {commit_hash} on branch {current_branch}")

        # Clean up merge state
        if self.merge_head_file.exists():
            self.merge_head_file.unlink()
        if self.merge_msg_file.exists():
            self.merge_msg_file.unlink()

        self.save_index({})
        return commit_hash


    def get_files_from_tree_recursive(self, tree_hash: str, prefix: str = "") -> Set[str]:
        files = set()
        try:
            tree_obj = self.load_object(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    files.add(full_name)
                elif mode.startswith("400"):
                    subtree_files = self.get_files_from_tree_recursive(obj_hash, f"{full_name}/")
                    files.update(subtree_files)
        except Exception as e:
            print(f"Warning: Could not read tree {tree_hash}: {e}")
        return files


    def checkout(self, target: str, create_branch: bool = False):
        # Check if target is a commit hash
        is_commit = False
        try:
            if len(target) >= 7 and all(c in '0123456789abcdef' for c in target):
                # Try to load as object
                self.load_object(target)
                is_commit = True
        except:
            pass

        if is_commit:
            # Checkout commit (detached HEAD)
            self.checkout_commit(target)
        else:
            # Checkout branch
            self.checkout_branch(target, create_branch)



    def checkout_commit(self, commit_hash: str):
        """Checkout a specific commit (detached HEAD state)"""
        # Get files from current state
        files_to_clear = set()
        current_head = self.get_head_commit()
        if current_head:
            try:
                commit_obj = self.load_object(current_head)
                commit = Commit.from_content(commit_obj.content)
                if commit.tree_hash:
                    files_to_clear = self.get_files_from_tree_recursive(commit.tree_hash)
            except:
                pass

        # Clear working directory
        for rel_path in sorted(files_to_clear):
            file_path = self.path / rel_path
            try:
                if file_path.is_file():
                    file_path.unlink()
            except:
                pass

        # Restore commit's tree
        commit_obj = self.load_object(commit_hash)
        commit = Commit.from_content(commit_obj.content)
        if commit.tree_hash:
            self.restore_tree(commit.tree_hash, self.path)

        # Set HEAD to commit hash (detached)
        self.head_file.write_text(commit_hash + "\n")
        self.save_index({})
        print(f"HEAD is now at {commit_hash[:7]} (detached HEAD)")
        print(f"Commit message: {commit.message}")




