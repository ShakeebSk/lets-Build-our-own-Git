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



    def checkout_branch(self, branch: str, create_branch: bool):
        previous_branch = self.get_current_branch()
        files_to_clear = set()
        
        try:
            previous_commit_hash = self.get_head_commit()
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
                previous_commit_hash = self.get_head_commit()
                if previous_commit_hash:
                    self.set_branch_commit(branch, previous_commit_hash)
                    print(f"Created new branch {branch}")
                else:
                    print("No commits yet, cannot create a branch")
                    return
            else:
                print(f"Branch '{branch}' not found.")
                print(f"Use 'python3 main.py checkout -b {branch}' to create and switch to a new branch.")
                return
        
        self.head_file.write_text(f"ref: refs/heads/{branch}\n")
        self.restore_working_directory(branch, files_to_clear)
        print(f"Switched to branch {branch}")


    def restore_tree(self, tree_hash: str, path: Path):
        tree_obj = self.load_object(tree_hash)
        tree = Tree.from_content(tree_obj.content)
        for mode, name, obj_hash in tree.entries:
            file_path = path / name
            if mode.startswith("100"):
                blob_obj = self.load_object(obj_hash)
                file_path.write_bytes(blob_obj.content)
            elif mode.startswith("400"):
                file_path.mkdir(exist_ok=True)
                self.restore_tree(obj_hash, file_path)


    def restore_working_directory(self, branch: str, files_to_clear: Set[str]):
        target_commit_hash = self.get_branch_commit(branch)
        if not target_commit_hash:
            return

        for rel_path in sorted(files_to_clear):
            file_path = self.path / rel_path
            try:
                if file_path.is_file():
                    file_path.unlink()
            except:
                pass

        target_commit_obj = self.load_object(target_commit_hash)
        target_commit = Commit.from_content(target_commit_obj.content)

        if target_commit.tree_hash:
            self.restore_tree(target_commit.tree_hash, self.path)

        self.save_index({})



    def branch(self, branch_name: str = None, delete: bool = False):
        if delete and branch_name:
            branch_file = self.heads_dir / branch_name
            if branch_file.exists():
                branch_file.unlink()
                print(f"Deleted branch {branch_name}")
            else:
                print(f"Branch {branch_name} not found")
            return

        current_branch = self.get_current_branch()
        if branch_name:
            current_commit = self.get_head_commit()
            if current_commit:
                self.set_branch_commit(branch_name, current_commit)
                print(f"Created branch {branch_name}")
            else:
                print(f"No commits yet, cannot create a new branch")
        else:
            branches = []
            for branch_file in self.heads_dir.iterdir():
                if branch_file.is_file() and not branch_file.name.startswith("."):
                    branches.append(branch_file.name)

            for branch in sorted(branches):
                current_marker = "* " if branch == current_branch else "  "
                print(f"{current_marker}{branch}")


    def log(self, max_count: int = 10):
        commit_hash = self.get_head_commit()
        if not commit_hash:
            print("No commits yet!")
            return

        count = 0
        while commit_hash and count < max_count:
            commit_obj = self.load_object(commit_hash)
            commit = Commit.from_content(commit_obj.content)

            print(f"commit {commit_hash}")
            if len(commit.parent_hashes) > 1:
                parents_str = " ".join(commit.parent_hashes)
                print(f"Merge: {parents_str[:14]}...")
            print(f"Author: {commit.author}")
            print(f"Date: {time.ctime(commit.timestamp)}")
            print(f"\n    {commit.message}\n")

            commit_hash = commit.parent_hashes[0] if commit.parent_hashes else None
            count += 1


    def build_index_from_tree(self, tree_hash: str, prefix: str = "") -> Dict[str, str]:
        index = {}
        try:
            tree_obj = self.load_object(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    index[full_name] = obj_hash
                elif mode.startswith("400"):
                    subindex = self.build_index_from_tree(obj_hash, f"{full_name}/")
                    index.update(subindex)
        except Exception as e:
            print(f"Warning: Could not read tree {tree_hash}: {e}")
        return index



    def get_all_files(self) -> List[Path]:
        files = []
        for item in self.path.rglob("*"):
            if ".git" in item.parts:
                continue
            if item.is_file():
                files.append(item)
        return files




    def status(self):
        current_branch = self.get_current_branch()
        if self.is_detached_head():
            head_commit = self.get_head_commit()
            print(f"HEAD detached at {head_commit[:7] if head_commit else 'unknown'}")
        else:
            print(f"On branch {current_branch}")

        # Check for merge in progress
        if self.merge_head_file.exists():
            print("\nMerge in progress")
            print("  (fix conflicts and run 'commit' to complete merge)")

        index = self.load_index()
        current_commit_hash = self.get_head_commit()

        last_index_files = {}
        if current_commit_hash:
            try:
                commit_obj = self.load_object(current_commit_hash)
                commit = Commit.from_content(commit_obj.content)
                if commit.tree_hash:
                    last_index_files = self.build_index_from_tree(commit.tree_hash)
            except:
                last_index_files = {}

        working_files = {}
        for item in self.get_all_files():
            rel_path = str(item.relative_to(self.path))
            try:
                content = item.read_bytes()
                blob = Blob(content)
                working_files[rel_path] = blob.hash()
            except:
                continue

        staged_files = []
        unstaged_files = []
        untracked_files = []
        deleted_files = []

        for file_path in set(index.keys()) | set(last_index_files.keys()):
            index_hash = index.get(file_path)
            last_index_hash = last_index_files.get(file_path)

            if index_hash and not last_index_hash:
                staged_files.append(("new file", file_path))
            elif index_hash and last_index_hash and index_hash != last_index_hash:
                staged_files.append(("modified", file_path))

        if staged_files:
            print("\nChanges to be committed:")
            for stage_status, file_path in sorted(staged_files):
                print(f"   {stage_status}: {file_path}")

        for file_path in working_files:
            if file_path in index:
                if working_files[file_path] != index[file_path]:
                    unstaged_files.append(file_path)

        if unstaged_files:
            print("\nChanges not staged for commit:")
            for file_path in sorted(unstaged_files):
                print(f"   modified: {file_path}")

        for file_path in working_files:
            if file_path not in index and file_path not in last_index_files:
                untracked_files.append(file_path)

        if untracked_files:
            print("\nUntracked files:")
            for file_path in sorted(untracked_files):
                print(f"   {file_path}")

        for file_path in index:
            if file_path not in working_files:
                deleted_files.append(file_path)

        if deleted_files:
            print("\nDeleted files:")
            for file_path in sorted(deleted_files):
                print(f"   deleted: {file_path}")

        if not staged_files and not unstaged_files and not deleted_files and not untracked_files:
            print("\nnothing to commit, working tree clean")

    def merge(self, branch: str, no_ff: bool = False):
        """Merge another branch into current branch"""
        if self.is_detached_head():
            print("Cannot merge in detached HEAD state")
            return

        current_branch = self.get_current_branch()
        if branch == current_branch:
            print(f"Cannot merge branch '{branch}' into itself")
            return

        # Get branch commit
        branch_commit_hash = self.get_branch_commit(branch)
        if not branch_commit_hash:
            print(f"Branch '{branch}' not found")
            return

        current_commit_hash = self.get_head_commit()
        if not current_commit_hash:
            print("No commits on current branch")
            return

        # Check if already up to date
        if current_commit_hash == branch_commit_hash:
            print("Already up to date")
            return

        # Check if fast-forward is possible
        if not no_ff and self.is_ancestor(current_commit_hash, branch_commit_hash):
            # Fast-forward merge
            self.set_branch_commit(current_branch, branch_commit_hash)
            self.restore_working_directory(current_branch, set())
            print(f"Fast-forward merge to {branch_commit_hash[:7]}")
            return

        # Three-way merge needed
        print(f"Merging branch '{branch}' into '{current_branch}'")
        
        # Find common ancestor
        common_ancestor = self.find_common_ancestor(current_commit_hash, branch_commit_hash)
        
        if not common_ancestor:
            print("No common ancestor found, cannot merge")
            return

        # Get file indexes for all three commits
        base_index = self.get_commit_file_index(common_ancestor)
        current_index = self.get_commit_file_index(current_commit_hash)
        branch_index = self.get_commit_file_index(branch_commit_hash)

        # Perform three-way merge
        merged_index, conflicts = self.three_way_merge(
            base_index, current_index, branch_index
        )

        if conflicts:
            print(f"\nAutomatic merge failed; fix conflicts and then commit the result.")
            print(f"Conflicts in files:")
            for file in sorted(conflicts):
                print(f"   {file}")
            
            # Save merge state
            self.merge_head_file.write_text(branch_commit_hash + "\n")
            self.merge_msg_file.write_text(f"Merge branch '{branch}' into {current_branch}\n")
            
            # Write conflicted files
            self.save_index(merged_index)
            self.restore_merged_files(merged_index, conflicts)
        else:
            # Auto-merge successful
            self.save_index(merged_index)
            self.restore_merged_files(merged_index, set())
            
            # Create merge commit
            tree_hash = self.create_tree_from_index()
            merge_commit = Commit(
                tree_hash=tree_hash,
                parent_hashes=[current_commit_hash, branch_commit_hash],
                author="PyGit User <user@pygit.com>",
                committer="PyGit User <user@pygit.com>",
                message=f"Merge branch '{branch}' into {current_branch}",
            )
            commit_hash = self.store_object(merge_commit)
            self.set_branch_commit(current_branch, commit_hash)
            self.save_index({})
            print(f"Merge successful. Created commit {commit_hash[:7]}")


    def is_ancestor(self, ancestor_hash: str, descendant_hash: str) -> bool:
        """Check if ancestor_hash is an ancestor of descendant_hash"""
        current = descendant_hash
        visited = set()
        
        while current and current not in visited:
            if current == ancestor_hash:
                return True
            visited.add(current)
            
            try:
                commit_obj = self.load_object(current)
                commit = Commit.from_content(commit_obj.content)
                current = commit.parent_hashes[0] if commit.parent_hashes else None
            except:
                break
        
        return False

    def find_common_ancestor(self, commit1: str, commit2: str) -> Optional[str]:
        """Find the common ancestor of two commits"""
        ancestors1 = self.get_all_ancestors(commit1)
        
        current = commit2
        visited = set()
        
        while current and current not in visited:
            if current in ancestors1:
                return current
            visited.add(current)
            
            try:
                commit_obj = self.load_object(current)
                commit = Commit.from_content(commit_obj.content)
                current = commit.parent_hashes[0] if commit.parent_hashes else None
            except:
                break
        
        return None


    def get_all_ancestors(self, commit_hash: str) -> Set[str]:
        """Get all ancestors of a commit"""
        ancestors = set()
        stack = [commit_hash]
        
        while stack:
            current = stack.pop()
            if current in ancestors:
                continue
            ancestors.add(current)
            
            try:
                commit_obj = self.load_object(current)
                commit = Commit.from_content(commit_obj.content)
                stack.extend(commit.parent_hashes)
            except:
                continue
        
        return ancestors


    def get_commit_file_index(self, commit_hash: str) -> Dict[str, str]:
        """Get file index from a commit"""
        try:
            commit_obj = self.load_object(commit_hash)
            commit = Commit.from_content(commit_obj.content)
            if commit.tree_hash:
                return self.build_index_from_tree(commit.tree_hash)
        except:
            pass
        return {}


    def three_way_merge(
        self,
        base: Dict[str, str],
        current: Dict[str, str],
        branch: Dict[str, str]
    ) -> Tuple[Dict[str, str], Set[str]]:
        """Perform three-way merge, return merged index and conflicts"""
        merged = {}
        conflicts = set()
        
        all_files = set(base.keys()) | set(current.keys()) | set(branch.keys())
        
        for file in all_files:
            base_hash = base.get(file)
            current_hash = current.get(file)
            branch_hash = branch.get(file)
            
            # File unchanged in both branches
            if current_hash == branch_hash:
                if current_hash:
                    merged[file] = current_hash
            # File unchanged in current, changed in branch
            elif current_hash == base_hash and branch_hash != base_hash:
                if branch_hash:
                    merged[file] = branch_hash
            # File unchanged in branch, changed in current
            elif branch_hash == base_hash and current_hash != base_hash:
                if current_hash:
                    merged[file] = current_hash
            # File changed in both branches differently - CONFLICT
            elif current_hash != branch_hash:
                if current_hash and branch_hash:
                    # Both modified - create conflict
                    conflicts.add(file)
                    merged[file] = current_hash  # Keep current for now
                elif current_hash and not branch_hash:
                    # Modified in current, deleted in branch - CONFLICT
                    conflicts.add(file)
                    merged[file] = current_hash
                elif branch_hash and not current_hash:
                    # Deleted in current, modified in branch - CONFLICT
                    conflicts.add(file)
                    merged[file] = branch_hash
        
        return merged, conflicts



    def restore_merged_files(self, index: Dict[str, str], conflicts: Set[str]):
        """Restore files after merge, creating conflict markers for conflicts"""
        for file_path, blob_hash in index.items():
            full_path = self.path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path in conflicts:
                # Create conflict markers
                try:
                    current_content = full_path.read_bytes() if full_path.exists() else b""
                    branch_content = self.load_object(blob_hash).content
                    
                    conflict_content = (
                        b"<<<<<<< HEAD\n" +
                        current_content +
                        b"\n=======\n" +
                        branch_content +
                        b"\n>>>>>>> MERGE_HEAD\n"
                    )
                    full_path.write_bytes(conflict_content)
                except:
                    pass
            else:
                # Normal file restore
                blob_obj = self.load_object(blob_hash)
                full_path.write_bytes(blob_obj.content)


    def cherry_pick(self, commit_hash: str):
        """Apply changes from a specific commit to current branch"""
        try:
            # Load the commit to cherry-pick
            commit_obj = self.load_object(commit_hash)
            commit = Commit.from_content(commit_obj.content)
        except:
            print(f"Commit {commit_hash} not found")
            return

        if not commit.parent_hashes:
            print("Cannot cherry-pick initial commit")
            return

        # Get file indexes
        parent_hash = commit.parent_hashes[0]
        parent_index = self.get_commit_file_index(parent_hash)
        commit_index = self.get_commit_file_index(commit_hash)
        current_head = self.get_head_commit()
        current_index = self.get_commit_file_index(current_head) if current_head else {}

        # Calculate changes in the commit
        changes = {}
        for file in set(parent_index.keys()) | set(commit_index.keys()):
            parent_blob = parent_index.get(file)
            commit_blob = commit_index.get(file)
            
            if parent_blob != commit_blob:
                changes[file] = commit_blob

        # Apply changes to current index
        index = self.load_index()
        conflicts = []
        
        for file, new_blob in changes.items():
            if file in current_index and current_index[file] != parent_index.get(file):
                # File was modified in both - potential conflict
                conflicts.append(file)
            else:
                if new_blob:
                    index[file] = new_blob
                elif file in index:
                    del index[file]

        if conflicts:
            print(f"Conflicts detected in: {', '.join(conflicts)}")
            print("Please resolve conflicts and commit manually")
            return

        # Save index and restore files
        self.save_index(index)
        for file, blob_hash in index.items():
            if blob_hash:
                full_path = self.path / file
                full_path.parent.mkdir(parents=True, exist_ok=True)
                blob_obj = self.load_object(blob_hash)
                full_path.write_bytes(blob_obj.content)

        print(f"Cherry-picked commit {commit_hash[:7]}")
        print(f"Message: {commit.message}")
        print("Changes staged. Run 'commit' to create a new commit.")




    def stash(self, message: str = None):
        """Save current changes to stash"""
        index = self.load_index()
        
        if not index:
            print("No local changes to save")
            return

        # Create stash entry
        stash_entry = {
            "index": index,
            "message": message or f"WIP on {self.get_current_branch()}",
            "timestamp": int(time.time()),
            "branch": self.get_current_branch(),
            "commit": self.get_head_commit()
        }

        # Load existing stashes
        stashes = []
        if self.stash_file.exists():
            try:
                stashes = json.loads(self.stash_file.read_text())
            except:
                stashes = []

        stashes.insert(0, stash_entry)
        self.stash_file.write_text(json.dumps(stashes, indent=2))

        # Clear working directory and index
        for file_path in index:
            full_path = self.path / file_path
            try:
                if full_path.exists():
                    full_path.unlink()
            except:
                pass

        self.save_index({})
        
        # Restore HEAD state
        head_commit = self.get_head_commit()
        if head_commit:
            commit_obj = self.load_object(head_commit)
            commit = Commit.from_content(commit_obj.content)
            if commit.tree_hash:
                self.restore_tree(commit.tree_hash, self.path)

        print(f"Saved working directory and index state")
        print(f"Stash message: {stash_entry['message']}")



    def stash_list(self):
        """List all stashes"""
        if not self.stash_file.exists():
            print("No stashes found")
            return

        try:
            stashes = json.loads(self.stash_file.read_text())
        except:
            print("No stashes found")
            return

        if not stashes:
            print("No stashes found")
            return

        for i, stash in enumerate(stashes):
            timestamp = time.ctime(stash['timestamp'])
            message = stash['message']
            branch = stash['branch']
            print(f"stash@{{{i}}}: On {branch}: {message} ({timestamp})")



    def stash_pop(self, index: int = 0):
        """Apply and remove a stash"""
        if not self.stash_file.exists():
            print("No stashes found")
            return

        try:
            stashes = json.loads(self.stash_file.read_text())
        except:
            print("No stashes found")
            return

        if not stashes or index >= len(stashes):
            print(f"Stash@{{{index}}} not found")
            return

        stash = stashes[index]
        stash_index = stash['index']

        # Restore stashed files
        for file_path, blob_hash in stash_index.items():
            full_path = self.path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                blob_obj = self.load_object(blob_hash)
                full_path.write_bytes(blob_obj.content)
            except:
                print(f"Warning: Could not restore {file_path}")

        # Update index
        current_index = self.load_index()
        current_index.update(stash_index)
        self.save_index(current_index)

        # Remove stash
        stashes.pop(index)
        self.stash_file.write_text(json.dumps(stashes, indent=2))

        print(f"Applied stash@{{{index}}}")
        print(f"Dropped stash@{{{index}}}")



    def stash_apply(self, index: int = 0):
        """Apply a stash without removing it"""
        if not self.stash_file.exists():
            print("No stashes found")
            return

        try:
            stashes = json.loads(self.stash_file.read_text())
        except:
            print("No stashes found")
            return

        if not stashes or index >= len(stashes):
            print(f"Stash@{{{index}}} not found")
            return

        stash = stashes[index]
        stash_index = stash['index']

        # Restore stashed files
        for file_path, blob_hash in stash_index.items():
            full_path = self.path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                blob_obj = self.load_object(blob_hash)
                full_path.write_bytes(blob_obj.content)
            except:
                print(f"Warning: Could not restore {file_path}")

        # Update index
        current_index = self.load_index()
        current_index.update(stash_index)
        self.save_index(current_index)

        print(f"Applied stash@{{{index}}}")


    def stash_drop(self, index: int = 0):
        """Remove a stash"""
        if not self.stash_file.exists():
            print("No stashes found")
            return

        try:
            stashes = json.loads(self.stash_file.read_text())
        except:
            print("No stashes found")
            return

        if not stashes or index >= len(stashes):
            print(f"Stash@{{{index}}} not found")
            return

        stashes.pop(index)
        self.stash_file.write_text(json.dumps(stashes, indent=2))
        print(f"Dropped stash@{{{index}}}")

    def tag_create(self, tag_name: str, commit_hash: str = None, message: str = None, annotated: bool = False):
        """Create a tag"""
        target_commit = commit_hash or self.get_head_commit()
        
        if not target_commit:
            print("No commits to tag")
            return

        tag_file = self.tags_dir / tag_name
        if tag_file.exists():
            print(f"Tag '{tag_name}' already exists")
            return

        if annotated and message:
            # Create annotated tag
            tag_obj = Tag(
                object_hash=target_commit,
                object_type="commit",
                tag_name=tag_name,
                tagger="PyGit User <user@pygit.com>",
                message=message
            )
            tag_hash = self.store_object(tag_obj)
            tag_file.write_text(tag_hash + "\n")
            print(f"Created annotated tag '{tag_name}' at {target_commit[:7]}")
        else:
            # Create lightweight tag
            tag_file.write_text(target_commit + "\n")
            print(f"Created tag '{tag_name}' at {target_commit[:7]}")



    def tag_list(self):
        """List all tags"""
        if not self.tags_dir.exists():
            return

        tags = []
        for tag_file in self.tags_dir.iterdir():
            if tag_file.is_file():
                tags.append(tag_file.name)

        if not tags:
            print("No tags found")
            return

        for tag in sorted(tags):
            print(tag)

    def tag_delete(self, tag_name: str):
        """Delete a tag"""
        tag_file = self.tags_dir / tag_name
        if not tag_file.exists():
            print(f"Tag '{tag_name}' not found")
            return

        tag_file.unlink()
        print(f"Deleted tag '{tag_name}'")

    def reset(self, commit_hash: str, mode: str = "mixed"):
        """Reset current HEAD to specified state"""
        try:
            commit_obj = self.load_object(commit_hash)
            commit = Commit.from_content(commit_obj.content)
        except:
            print(f"Commit {commit_hash} not found")
            return

        if mode == "soft":
            # Move HEAD only, keep index and working directory
            if self.is_detached_head():
                self.head_file.write_text(commit_hash + "\n")
            else:
                current_branch = self.get_current_branch()
                self.set_branch_commit(current_branch, commit_hash)
            print(f"Reset HEAD to {commit_hash[:7]} (soft)")

        elif mode == "mixed":
            # Move HEAD and reset index, keep working directory
            if self.is_detached_head():
                self.head_file.write_text(commit_hash + "\n")
            else:
                current_branch = self.get_current_branch()
                self.set_branch_commit(current_branch, commit_hash)
            
            # Reset index to commit's tree
            if commit.tree_hash:
                new_index = self.build_index_from_tree(commit.tree_hash)
                self.save_index(new_index)
            else:
                self.save_index({})
            
            print(f"Reset HEAD and index to {commit_hash[:7]} (mixed)")

        elif mode == "hard":
            # Move HEAD, reset index, and reset working directory
            if self.is_detached_head():
                self.head_file.write_text(commit_hash + "\n")
            else:
                current_branch = self.get_current_branch()
                self.set_branch_commit(current_branch, commit_hash)
            
            # Clear working directory
            current_files = self.get_files_from_tree_recursive(commit.tree_hash) if commit.tree_hash else set()
            all_files = set(str(f.relative_to(self.path)) for f in self.get_all_files())
            
            for file_path in all_files:
                full_path = self.path / file_path
                try:
                    if full_path.is_file():
                        full_path.unlink()
                except:
                    pass
            
            # Restore commit's tree
            if commit.tree_hash:
                self.restore_tree(commit.tree_hash, self.path)
                new_index = self.build_index_from_tree(commit.tree_hash)
                self.save_index(new_index)
            else:
                self.save_index({})
            
            print(f"Reset HEAD, index, and working directory to {commit_hash[:7]} (hard)")





    def diff(self, target1: str = None, target2: str = None):
        """Show differences between commits, commit and working tree, etc."""
        if not target1 and not target2:
            # Diff between index and working directory
            self.diff_index_working()
        elif target1 and not target2:
            # Diff between commit and working directory
            self.diff_commit_working(target1)
        elif target1 and target2:
            # Diff between two commits
            self.diff_commits(target1, target2)

    def diff_index_working(self):
        """Diff between staged changes and working directory"""
        index = self.load_index()
        
        if not index:
            print("No staged changes")
            return

        for file_path, blob_hash in sorted(index.items()):
            full_path = self.path / file_path
            
            if not full_path.exists():
                print(f"\n--- a/{file_path}")
                print(f"+++ /dev/null")
                print(f"@@ File deleted @@")
                continue
            
            try:
                current_content = full_path.read_bytes().decode('utf-8', errors='ignore')
                blob_obj = self.load_object(blob_hash)
                staged_content = blob_obj.content.decode('utf-8', errors='ignore')
                
                if current_content != staged_content:
                    print(f"\ndiff --git a/{file_path} b/{file_path}")
                    print(f"--- a/{file_path}")
                    print(f"+++ b/{file_path}")
                    
                    diff = difflib.unified_diff(
                        staged_content.splitlines(keepends=True),
                        current_content.splitlines(keepends=True),
                        lineterm=''
                    )
                    
                    for line in diff:
                        print(line.rstrip())
            except:
                print(f"\nBinary files differ: {file_path}")


    def diff_commit_working(self, commit_hash: str):
        """Diff between a commit and working directory"""
        try:
            commit_index = self.get_commit_file_index(commit_hash)
        except:
            print(f"Commit {commit_hash} not found")
            return

        working_files = {}
        for item in self.get_all_files():
            rel_path = str(item.relative_to(self.path))
            working_files[rel_path] = item

        all_files = set(commit_index.keys()) | set(working_files.keys())

        for file_path in sorted(all_files):
            blob_hash = commit_index.get(file_path)
            working_file = working_files.get(file_path)

            if blob_hash and not working_file:
                print(f"\ndiff --git a/{file_path} b/{file_path}")
                print(f"deleted file")
            elif not blob_hash and working_file:
                print(f"\ndiff --git a/{file_path} b/{file_path}")
                print(f"new file")
            elif blob_hash and working_file:
                try:
                    blob_obj = self.load_object(blob_hash)
                    old_content = blob_obj.content.decode('utf-8', errors='ignore')
                    new_content = working_file.read_bytes().decode('utf-8', errors='ignore')
                    
                    if old_content != new_content:
                        print(f"\ndiff --git a/{file_path} b/{file_path}")
                        print(f"--- a/{file_path}")
                        print(f"+++ b/{file_path}")
                        
                        diff = difflib.unified_diff(
                            old_content.splitlines(keepends=True),
                            new_content.splitlines(keepends=True),
                            lineterm=''
                        )
                        
                        for line in diff:
                            print(line.rstrip())
                except:
                    print(f"\nBinary files differ: {file_path}")



    
    def diff_commits(self, commit1: str, commit2: str):
        """Diff between two commits"""
        try:
            index1 = self.get_commit_file_index(commit1)
            index2 = self.get_commit_file_index(commit2)
        except:
            print("One or both commits not found")
            return

        all_files = set(index1.keys()) | set(index2.keys())

        for file_path in sorted(all_files):
            hash1 = index1.get(file_path)
            hash2 = index2.get(file_path)

            if hash1 and not hash2:
                print(f"\ndiff --git a/{file_path} b/{file_path}")
                print(f"deleted file")
            elif not hash1 and hash2:
                print(f"\ndiff --git a/{file_path} b/{file_path}")
                print(f"new file")
            elif hash1 != hash2:
                try:
                    blob1 = self.load_object(hash1)
                    blob2 = self.load_object(hash2)
                    content1 = blob1.content.decode('utf-8', errors='ignore')
                    content2 = blob2.content.decode('utf-8', errors='ignore')
                    
                    print(f"\ndiff --git a/{file_path} b/{file_path}")
                    print(f"--- a/{file_path}")
                    print(f"+++ b/{file_path}")
                    
                    diff = difflib.unified_diff(
                        content1.splitlines(keepends=True),
                        content2.splitlines(keepends=True),
                        lineterm=''
                    )
                    
                    for line in diff:
                        print(line.rstrip())
                except:
                    print(f"\nBinary files differ: {file_path}")







