#!/usr/bin/env python3
"""Build the reviewed status baseline, then the English/Turkish presentation layer."""
import release_editorial
import build_bilingual
if __name__=='__main__':
    release_editorial.main()
    build_bilingual.main()
