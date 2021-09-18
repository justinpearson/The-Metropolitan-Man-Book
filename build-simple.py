# build-simple.py

import re, subprocess
from bs4 import BeautifulSoup
from selenium import webdriver

texs = []

for i in range(1,14):
    # Download:
    # (Gotta re-open FF each time, to avoid Cloudflare captcha.)
    d = webdriver.Firefox() 
    d.get(f'https://www.fanfiction.net/s/10360716/{i}/The-Metropolitan-Man')
    html = d.page_source
    d.close()

    # Parse HTML:
    soup = BeautifulSoup(html, features='html.parser')
    story = soup.find(id='storytext')
    story.attrs = None
    chapter_name = re.search(
        r'Chapter \d+: (.*), a superman fanfic',
        soup.title.text
    ).group(1)
    h = soup.new_tag('h1')
    h.string = chapter_name
    story.insert(0, h)
    html = str(story) + '\n'

    # HTML to TeX:
    tex = subprocess.check_output([ 'pandoc'
            , '-f', 'html+smart', '-t', 'latex+smart'
            , '--top-level-division=chapter'
            ], text=True, input=html )
    texs.append(tex)

# Assemble chapters:
open('mm.tex','w').write(
    '\n'.join([ open('header.tex').read()
              , *texs
              , open('footer.tex').read() 
              ])
)

# TeX to PDF:
# (For pdflatex's TOC generation, gotta run twice.)
for _ in [1,2]:
    subprocess.run([ 'pdflatex', '-interaction=batchmode', 'mm.tex' ])
