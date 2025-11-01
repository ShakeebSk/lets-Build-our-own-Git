<h1 align="center">🚀 LETS-BUILD-OUR-OWN-GIT</h1>

<p align="center"><em>Empower Innovation Through Seamless Version Control Mastery</em></p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/ShakeebSk/lets-Build-our-own-Git?color=blue&label=last%20commit">
  <img src="https://img.shields.io/badge/python-100%25-blue">
  <img src="https://img.shields.io/github/languages/count/ShakeebSk/lets-Build-our-own-Git?color=blue&label=languages">
</p>

<p align="center">
  Built with the tools and technologies:<br>
  <img src="https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54">
</p>

---

# 🧬 PyGit — A Simple Yet Complete Git Clone in Python

**PyGit** is a fully functional educational Git clone written entirely in **Python**, re-creating Git’s internals from scratch — including commits, branches, merges, stashes, tags, cherry-picks, and more.  

It’s built for anyone curious to **understand how Git truly works under the hood**.

> 🧠 *“To truly master Git, build your own.”*

---

## 📖 What is PyGit?

PyGit replicates how Git stores, tracks, and manages files — using **blobs**, **trees**, and **commits** — entirely with Python’s standard libraries.  
Every commit, branch, and tag is built the same way Git does it internally.

---

## ⚙️ Core Components

| Component | Description |
|------------|-------------|
| 🧩 **GitObject** | Base class for all Git objects (`Blob`, `Tree`, `Commit`, `Tag`). Handles compression + hashing (SHA-1). |
| 📄 **Blob** | Stores raw file contents. |
| 🌲 **Tree** | Represents directory structure, storing references to blobs and sub-trees. |
| 🕓 **Commit** | Stores metadata (author, message, timestamp) and links to parent commit(s). |
| 🏗️ **Repository** | Manages `.pygit/`, objects, branches, HEAD, and commands. |

---

## 🚀 Major Features

| Category | Commands | Description |
|-----------|-----------|-------------|
| 🧱 Core VCS | `init`, `add`, `commit`, `status`, `log`, `diff` | Basic Git-like operations |
| 🌿 Branching | `branch`, `checkout`, `checkout -b`, `branch -d` | Create, switch, and delete branches |
| 🔀 Merging | `merge` | Fast-forward and 3-way merges with conflict resolution |
| 🍒 Cherry-Pick | `cherry-pick <hash>` | Apply a specific commit onto the current branch |
| 🏷️ Tagging | `tag`, `tag -a`, `tag -d` | Create annotated or lightweight tags |
| 💾 Stashing | `stash save`, `stash list`, `stash pop` | Save uncommitted work and apply later |
| 🔁 Reset | `reset --soft`, `--mixed`, `--hard` | Move HEAD to a previous commit safely |
| 🧭 Checkout Commit | `checkout <commit>` | Enter detached HEAD mode |
| 🧰 Diff System | `diff`, `diff --cached` | Compare changes between index, commits, and working directory |

---

## ⚔️ PyGit vs Git — Feature Comparison

| Feature | Real Git | PyGit |
|----------|-----------|-------|
| Repository Initialization | ✅ | ✅ |
| Add / Commit | ✅ | ✅ |
| Branching & Checkout | ✅ | ✅ |
| Merge (3-way / fast-forward) | ✅ | ✅ |
| Stash | ✅ | ✅ |
| Cherry-pick | ✅ | ✅ |
| Tagging | ✅ | ✅ |
| Reset (soft/mixed/hard) | ✅ | ✅ |
| Remote (`push`, `pull`, `clone`) | ✅ | ❌ (planned) |
| Rebase | ✅ | ❌ (future feature) |
| Signed Commits | ✅ | ❌ |
| Garbage Collection | ✅ | ✅ (basic) |

---

## 📦 Installation & Setup

### 🐍 Requirements
- Python 3.7+
- No external dependencies

### ⚡ Quick Start

```bash
# Clone this repo
git clone https://github.com/ShakeebSk/lets-Build-our-own-Git.git
cd lets-Build-our-own-Git

# Initialize your own PyGit repository
python3 git.py init


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
