#!/usr/bin/env python3

# build.py: Download The Metropolitan Man from fanfiction.net and typeset it to PDF. 

# TODO: type annotations
# TODO: merge this into doit file dodo.py

# TODO: Update this:

# Run it by typing "./build.sh" at your terminal (no quotes).
#
# It creates several intermediate files in files/ with names like 3_a_orig.html.
# To remove all the files it creates, run "./build.sh cleanall".
# To remove all the files it creates except for the saved-to-disk raw HTML
# files from fanfiction.net, run "./build.sh clean".
#
# Note: _a_orig.html, _b_pruned.html, and _c_fix.html all have the story on 1 line,
# (needed to prevent
#        incorrect spaces when parsed by pandoc and tex).

import re, os, requests
from bs4 import BeautifulSoup
import subprocess

def main():
    texs = []
    for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
        url  = f'https://www.fanfiction.net/s/10360716/{i}/The-Metropolitan-Man'

        html = download(    url,  saveas=f'files/{i:02}_a_orig.html'    )
        assert type(html) == str
        assert len(html) > 300
        assert len(html.splitlines()) > 100
        assert html.startswith('<!DOCTYPE html><html><head>')
        assert html.endswith('</body></html>')
        assert "<div class='storytext xcontrast_txt nocopy' id='storytext'>" in html
        
        html = prune_html(  html, saveas=f'files/{i:02}_b_pruned.html'  )
        assert type(html) == str
        assert len(html) > 300
        assert len(html.splitlines()) == 2
        assert html.startswith('<div><h1>')
        assert html.endswith('</p>\n</div>\n'), f'Wrong ending: {html[-20:]}'

        html = fix_html(    html, saveas=f'files/{i:02}_c_fix.html'     )
        assert type(html) == str
        assert len(html) > 300
        assert len(html.splitlines()) == 2
        assert html.startswith('<div><h1>')
        assert html.endswith('</p>\n</div>\n'), f'Wrong ending: {html[-20:]}'

        tex  = html_to_tex( html, saveas=f'files/{i:02}_d_pandoc1.tex'   )
        assert type(tex) == str
        assert len(tex) > 300
        assert len(tex.splitlines()) > 100

        tex  = fix_tex(     tex,  saveas=f'files/{i:02}_e_good.tex'     )
        assert type(tex) == str
        assert len(tex) > 300
        assert len(tex.splitlines()) > 100

        texs.append(tex)

    with open('mm.tex','w') as f:
        f.write(open('header.tex').read())
        for t in texs:
            f.write('\n\n%%%%%%%%%%%%%%%%%%% NEW CHAPTER %%%%%%%%%%%%%%%%%%%%%%%%\n\n')
            f.write(t)
        f.write(open('footer.tex').read())

    verify_tex('mm.tex')
    tex_to_pdf('mm.tex', 'mm')

def download(url, saveas):
    'Download chapters 1 thru 13 of MM from fanfiction.net, as 1_a_orig.html, ..., 13_a_orig.html.'
    # If file exists on disk, retrieve that instead.

    if os.path.isfile(saveas):
        print(f'Found cached html file {saveas}, returning it.')
        return open(saveas).read()
    else:
        html = requests.get(url).content
        # TODO: verify html.
        open(saveas,'w').write(html)
        return html

def prune_html(html, saveas):
    'Discard non-story HTML from 1_a_orig.html, creating 1_b_pruned.html'
    # prune_html.py: a python3 program that parses the HTML with BeautifulSoup.

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

    txt = str(story)
    # txt = txt.replace('\n','')
    txt += '\n'

    open(saveas,'w').write(txt)
    return txt

def fix_html(html, saveas):
    'Fix HTML formatting issues, creating 1_c_fix.html'

    # sed: fix typos and replace hyphens with en-dashes or em-dashes if necessary:
    #      - "pages 10-20" : en-dash
    #      - "his well-being" : hyphen (letters)
    #      - "Uranium U-238" : hyphen (letter & number)
    #      - "I thought -" : em-dash for all other cases
    #      - Use nonbreaking em-dash \=== from extdash pkg to ensure ---''
    #        doesn't linebreak as ---\n''
    #      - Ensure all double-quotes " get smart-quoted.
    #      - Replace "reviews/favorites" with "reviews / favorites" etc
    #        for better linebreaking. Note: a/b/c/d/e requires two separate
    #        replacement passes; the first only yields a / b/c / d/e .
    #      - Note that all sed commands should have the trailing "g" (global)
    #        because the HTML is all one long line (needed to prevent
    #        incorrect spaces when parsed by pandoc and tex).

    def fix_html_all(s):
        s = fix_html_typos(s)
        s = fix_html_hyphens(s)
        s = fix_html_slashes(s)
        s = fix_html_ellipses(s)
        return s


    def fix_html_typos(s):
        for old, new in [
              [ 'spaceship inside..'       , 'spaceship inside.'          ]
            , [ 'I got opening portion'    , 'I got the opening portion'  ]
            , [ 'as a mathematician"'      , 'as a mathematician."'       ]
            , [ 'December 19th, 1934</p>'  , 'December 19th, 1934:</p>'   ]
            , [ 'as he stood..'            , 'as he stood.'               ]
            , [ 'Genesis 18:23 '           , 'Genesis 18:23, '            ]
        ]:
            s = s.replace(old, new)
        return s

    def fix_html_hyphens(s):
        # Replace - with hyphen, en-dash, or em-dash as appropriate.
        # But first replace --- with em-dash and -- with en-dash.
        #
        # Note: each replacement needs to be run twice to deal with cases
        # like "bric-a-brac" where re.sub doesn't replace the 2nd "-" because
        # it resumed replacement after the 2nd matched group (the "a").
        #
        # WARNING / NOTE: pandoc replaces hyphens not with the "-" character 
        # (ascii code 45, unicode name HYPHEN-MINUS)
        # but with the "‐" character ('ascii' code 8208, unicode name HYPHEN).
        for old, new in [
              [  r'([^-])---([^-])'               ,  r'\1&mdash;\2'   ]
            , [  r'([^-])--([^-])'                ,  r'\1&ndash;\2'   ]
            , [  r'([0-9])-([0-9])'               ,  r'\1&ndash;\2'   ]
            , [  r'([a-zA-Z0-9])-([a-zA-Z0-9])'   ,  r'\1&hyphen;\2'  ]
            , [  r'-'                             ,  r'&mdash;'       ]
        ]:
            s = re.sub(old, new, s)
            s = re.sub(old, new, s)
        return s

    def fix_html_slashes(s):
        # The phrase "reviews/comments/favorites/recommendations" needs to appear
        # as "reviews / comments / favorites / recommendations" otherwise
        # tex typesets it as a single huge word.
        #
        # Note: gotta run this pattern twice, because the first
        # pass continues parsing the line after the matching foo/bar,
        # resulting in "reviews / comments/favorites / recommendations".

        old = r'([a-zA-Z]{3,})/([a-zA-Z]{3,})'
        new = r'\1 / \2'
        s = re.sub(old, new, s)
        s = re.sub(old, new, s)
        return s


    def fix_html_ellipses(s):
        # 1. Replace "..." with the unicode "…" for uniformity.
        s = re.sub(r'\.\.\.','…',s)

        # 2. Remove space before ellipsis, ie,
        #    convert "he said ..." into "he said..." .
        #    This looks better and also prevents linebreaks before "..." .
        s = re.sub( r'([a-zA-Z0-9]) …', r'\1…', s)
        return s

    html = fix_html_all(html)
    open(saveas,'w').write(html)
    return html

def html_to_tex(html, saveas):
    'Use pandoc to convert HTML to TEX, creating 1_d_pandoc1.tex'
    # pandoc: convert from html to tex.
    #         --top-level-division: converts <h1> HTML tags
    #         to \chapter latex commands.
    #         html+smart / latex+smart: use smart-quotes ``like this.''
    #         Warning: doesn't smart-quote if leave off html+smart.
    #         Seems like a bug, bc docs say html no support +smart extension.
    #         https://pandoc.org/MANUAL.html#extension-smart

    p = subprocess.run(
            [ 'pandoc'
            , '-f', 'html+smart'
            , '-t', 'latex+smart'
            , '--top-level-division=chapter'
            ]
            , capture_output=True
            , text=True
            , check=True
            , input=html
            )
    tex = p.stdout
    open(saveas,'w').write(tex)
    return tex

def fix_tex(tex, saveas):
    'Fix TEX formatting issues, creating 1_e_good.tex'

    def fix_tex_all(s):
        s = fix_tex_smartquotes(s)
        s = fix_tex_newlines(s)
        s = fix_tex_final_one_off_problems(s)
        return s

    def fix_tex_smartquotes(s):
        # In theory, since we used pandoc with latex+smart (to make ``smart quotes''),
        # there should be no normal double-quotes. But it missed some. So let's make extra-sure.

        s = re.sub(r'"([a-zA-Z0-9\.,!-\?])', r'``\1', s) # "Hello ...  --> ``Hello ...
        s = re.sub(r'([a-zA-Z0-9\.,!-\?])"', r"\1''", s) # ... end." --> ... end.''
        return s

    def fix_tex_newlines(s):
        # Fix 2 problems with linebreaks near em-dashes.
        # (1) Don't linebreak ``he said ---'' into ``he said\n---'' .
        #     Use a non-breaking space ``he said~---'' to acheive this.
        # (2) Don't linebreak between emdash and close-quote, ie,
        #     don't linebreak ``he said ---'' into ``he said ---\n'' .
        #     To do this, replace --- with \=== which is a non-breaking em-dash
        #     provided by the extdash latex package (see header.tex).
        #
        #     Note: Can't use nonbreaking em-dashes everywhere, because
        #     for some reason they eat the spaces surrounding them and it
        #     looks ugly.

        s = re.sub(r'([a-zA-Z0-9]) ---', r'\1~---', s)
        s = re.sub(r"---''", r"\\===''", s)
        return s

    def fix_tex_final_one_off_problems(s):
        # Crappy line-breaking: your home---'' extends into the margin.
        # Force newline: your \\ home---''
        s = re.sub(r'pistols into your home', r'pistols into your \\\\ home', s)
        return s

    tex = fix_tex_all(tex)
    open(saveas,'w').write(tex)
    return tex


def tex_to_pdf(tex_file, pdf_file):
    'Pdflatex to create final PDF.'

    # For TOC generation, gotta run twice.
    for _ in [1,2]:
        subprocess.run(
            [ 
            'pdflatex'
            , '-interaction=batchmode'
            , f'-jobname={pdf_file}'
            , tex_file
            ]
        )

def verify_tex(tex_file):
    'Verify that mm.tex is correct; certain fixed strings should appear in it.'
    story = open(tex_file).read()
    strs_should_be_present = [
        "bringing pistols into"
      , "to explain how I got"
      , "goodness of humanity"
      , "he could actually"
      , "--- that he"
      , "bric‐a‐brac"
      , "presumptions."
    ]
    for s in strs_should_be_present:
        assert s in story, f'UH OH: String "{s}" not found in final story "{tex_file}"!'
    print(f'Great! All test-strings were present in final story "{tex_file}"!')

if __name__=='__main__':
    main()