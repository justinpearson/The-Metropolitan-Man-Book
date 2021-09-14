#!/usr/bin/env python3

# build.py: Download The Metropolitan Man from fanfiction.net and typeset it to PDF. 
#
# Run it by typing "python3 build.py" at your terminal (no quotes).
#
# It creates several intermediate files in files/ with names like 3_a_orig.html.
#
# Note: The cached HTML files *_a_orig.html, *_b_pruned.html, and *_c_fix.html are all 1 long line,
# needed to prevent incorrect spaces being added when parsed by pandoc and tex.
#
# Note: the "cached=True" in url_for_chapter(i, cached=True) sets the URL 
# to be the LOCAL file 'files/*_a_orig.html', NOT the actual URL from fanfiction.net.
# This is for faster development and to avoid hitting their server too much.
# Also, since I started this project, fanfiction.net now seems to have bot-detection logic,
# so this downloading logic no longer works: instead of retreiving the correct HTML, it gets a captcha-type webpage.
# To get the real HTML, I believe you'd have to tell the requests.get function to fake certain headers.

from lib import url_for_chapter, download, prune_html, fix_html, html_to_tex, fix_tex, make_final_tex, tex_to_pdf

from functools import reduce 

def funcs_for_chapter(i):
    return [ lambda x: download(    x, saveas=f'files/{i:02}_a_orig.html' )
           , lambda x: prune_html(  x, saveas=f'files/{i:02}_b_pruned.html' )
           , lambda x: fix_html(    x, saveas=f'files/{i:02}_c_fix.html' )
           , lambda x: html_to_tex( x, saveas=f'files/{i:02}_d_pandoc1.tex' )
           , lambda x: fix_tex(     x, saveas=f'files/{i:02}_e_good.tex' )
           ]
texs = [
        reduce( lambda x,f: f(x)
              , funcs_for_chapter(i)
              , url_for_chapter(i, cached=True)
              )
        for i in range(1,14)
        ]
make_final_tex( texs, saveas='mm.tex')
tex_to_pdf('mm.tex', saveas='mm.pdf')
