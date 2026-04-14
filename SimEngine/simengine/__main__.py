"""Allow running as: python -m simengine <config.yaml>"""
from simengine.run import main
import asyncio
import sys

if len(sys.argv) < 2:
    print("Usage: python -m simengine <config.yaml>")
    sys.exit(1)

asyncio.run(main(sys.argv[1]))
