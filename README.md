# 🧬 PyGit – A Simple Git Clone in Python

## 📖 What is PyGit?

PyGit is a lightweight Python-based implementation of Git that helps you understand the core internals of version control systems.
It mimics how Git stores files, tracks history, and manages branches — all using Python’s standard library.

🔍 Ideal for developers and students who want to see how Git actually works behind the scenes.

### ⚙️ Core Components
- 🧩 1. GitObject Class

- Base class for all Git objects (Blob, Tree, Commit)

- Handles serialization/deserialization with zlib compression

- Generates SHA-1 hashes for unique object identification

### 📄 2. Blob Objects

- Represent individual files

- Store and compress raw file data

### 🌲 3. Tree Objects

- Represent directory structures

- Store references to blobs and other trees

- Maintain file names and permissions

### 🕓 4. Commit Objects

- Contain metadata (author, timestamp, message)

- Point to a tree object and a parent commit

- Form a linked commit history chain

### 🏗️ 5. Repository Class

- Manages the .git/ directory

- Handles object storage/retrieval

- Implements core Git operations: init, add, commit, checkout, etc.

## 🚀 Features

✅ Repository Initialization (init)
✅ File Staging (add)
✅ Commit Creation (commit)
✅ Branch Management (checkout, branch)
✅ Commit History (log)
✅ Status Checking (status)
✅ Object Storage with SHA-1 hashing and zlib compression

##📦 Installation & Setup
Prerequisites

### 🐍 Python 3.7+

No external libraries required!

Quick Start

# Clone the repository
```bash
git clone <this-repo-url>
cd git_clone
```

# Initialize and use PyGit
```bash
python3 main.py init
python3 main.py add README.md
python3 main.py commit -m "Initial commit"
```

# 💻 Usage Examples
🔧 Initialize Repository
```bash
python3 main.py init
# Output: Initialized empty Git repository in ./.git
```

# ➕ Add Files
```bash
python3 main.py add main.py
python3 main.py add src/
python3 main.py add file1.py file2.py src/
```

# 🧾 Commit Changes
```bash
python3 main.py commit -m "Add new feature"
python3 main.py commit -m "Fix bug" --author "Shakeeb Shaikh <shakeeb@shaikh.com>"
```

# 🌿 Branch Operations
```bash
python3 main.py branch
python3 main.py checkout -b feature-branch
python3 main.py checkout main
python3 main.py branch feature-branch -d
```

# 🧭 View Status & Log
```bash
python3 main.py status
python3 main.py log -n 5
```

# 🗂️ Project Structure
```text
git_clone/
├── main.py          # Main PyGit implementation
├── README.md        # Project documentation
└── .git/            # Git-like directory (created after init)
    ├── objects/     # Git object database
    ├── refs/        # References and branches
    ├── HEAD         # Current branch pointer
    └── index        # Staging area
```

# 🔍 How It Works (Visualized)
## 🗃️ 1. Object Storage (Blobs, Trees, Commits)
```text
                ┌────────────────────────┐
                │       Commit Object     │
                │────────────────────────│
                │ tree: <hash-of-tree>   │
                │ parent: <hash-of-prev> │
                │ author: Shakeeb        │
                │ message: "Initial"     │
                └────────────┬───────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │        Tree Object      │
                │────────────────────────│
                │ blob  file1.py (abcd)  │
                │ blob  file2.py (efgh)  │
                │ tree  src/ (ijkl)      │
                └────────────┬───────────┘
                             │
                             ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │ Blob (abcd)  │   │ Blob (efgh)  │   │ Blob (ijkl)  │
        │──────────────│   │──────────────│   │──────────────│
        │ print("A")   │   │ print("B")   │   │ def main():  │
        └──────────────┘   └──────────────┘   └──────────────┘
```
## 🧺 2. Staging Process
### Working Directory  →  Staging Area (index)  →  Object Database (.git/objects)
```text
file1.py, file2.py
     │
     ├─► Blob (content compressed + hashed)
     ├─► Index stores SHA-1 references
     └─► Tree object created at commit time
```
## 🧱 3. Commit History Chain
```text
HEAD → master → Commit (hash1)
                   │
                   ▼
              Commit (hash0)
                   │
                   ▼
                (initial)
```
## 🌱 4. Branches & HEAD
```text
refs/
 ├── heads/
 │    ├── main → (hash3)
 │    └── feature → (hash2)
 └── HEAD → refs/heads/main
```
When switching branches, HEAD changes its reference and updates the working tree.
# 🧠 Why PyGit?

## “To truly master Git, build your own.”

PyGit helps you:

Understand how Git stores and links data

Learn about hash-based object models

Explore commits, trees, and branches from a systems perspective

Build a foundation for distributed version control concepts

🧾 License

This project is licensed under the MIT License — free for personal and educational use.

👨‍💻 Author--Shakeeb Shaikh
