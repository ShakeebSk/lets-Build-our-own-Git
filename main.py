import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Git Clone. - A simple script that can execute a basic  git cmd's like init,add commits etc."
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )
    
    init_parser = subparsers.add_parser("init", help="Initialize a new git repository")
    
    args = parser.parse_args()
    
    print(args)

main()



