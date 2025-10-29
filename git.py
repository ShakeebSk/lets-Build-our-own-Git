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

    
