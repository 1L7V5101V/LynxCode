from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())


# DEBUG
def _debug_args():
    import sys
    print(f"args: {sys.argv[1:]}", file=sys.stderr)
