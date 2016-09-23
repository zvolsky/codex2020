# -*- coding: utf-8 -*-

"""
    python web2py.py -M -S codex2020 -R scripts/fix_answer.py
    fixes derrived data in answer table
"""

from c_fix import all_fix


def main():
    all_fix()


if __name__ == "__main__":
    main()
