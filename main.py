import argparse
import sys
from pathlib import Path
import json

class Repository:
    def __init__(self,path="." ):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".pygit"
        
        #.git/ojects
        self.objects_dir = self.git_dir / "objects"
        
        #.git/refs
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"
        
        #.Head File
        self.head_file = self.git_dir / "HEAD"
        
        #.git/index
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
        
        self.index_file.write_text(json.dumps({}, indent=4))
        
        print(f"Initialized empty Git repository in {self.git_dir}")
        return True
    

def main():
    parser = argparse.ArgumentParser(
        description="Git Clone. - A simple script that can execute a basic  git cmd's like init,add commits etc."
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )
    
    init_parser = subparsers.add_parser("init", help="Initialize a new git repository")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "init":
            repo = Repository()
            if not repo.init():
                print("Repository already exists.")
                return
            # print("Initializing a new git repository...")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    
    # print(args)

main()



