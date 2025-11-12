from __future__ import annotations
from sam_tools.registry import recent

def main():
    rows = recent(20)
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
