#!/usr/bin/env python3 
#
# prune_html.py

import sys, bs4, re

soup = bs4.BeautifulSoup(sys.stdin.read(),'html5lib')
story = soup.find(id='storytext')
story.attrs = None
chapter_name = re.search(
    r'Chapter \d+: (.*), a superman fanfic',
    soup.title.text
    ).group(1)

h = soup.new_tag('h1')
h.string = chapter_name
story.insert(0, h)

print(story)