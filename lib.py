import re, os
from bs4 import BeautifulSoup
import subprocess
from functools import reduce 

# TODO: type annotations.

def url_for_chapter(i, cached=False):
    if cached:
        s = f'files/{i:02}_a_orig.html'
        if not os.path.isfile(s):
            raise ValueError(f"You set cached={cached} but I can't find cached file '{s}' for chapter {i}!")
        return s
    else:
        return f'https://www.fanfiction.net/s/10360716/{i}/The-Metropolitan-Man'


def download(url, saveas=None):
    '''
    Step A: Download chapters 1 thru 13 of MM from fanfiction.net (or a local file),
    possibly saving the contents to a local file (eg 1_a_orig.html).

    Warning: since I started this project, fanfiction.net now seems to have bot-detection logic,
    so this downloading logic does not retreive the correct HTML, but rather, a captcha-type webpage.
    So we use an automated browser (Selenium Webdriver) rather than curl or the 'requests' module.
    '''

    def verify_html(html):
        assert type(html) == str, f'Expected html to have type str, not {type(html)}'
        assert len(html) > 300
        assert len(html.splitlines()) > 100
        assert html.startswith('<!DOCTYPE html><html><head>')
        assert html.endswith('</body></html>')
        assert "<div class='storytext xcontrast_txt nocopy' id='storytext'>" in html
        return html

    # Guard clause: If local file, just return it.
    if not url.startswith('http'):
        print(f'URL {url} is not HTTP; assuming it\'s a local file and returning it.')
        return verify_html(open(url).read())

    # Else, download the remote url and return the text HTML.
    from selenium import webdriver
    d = webdriver.Firefox()
    d.get(url)
    html = d.page_source
    d.close()

    verify_html(html)
    if saveas: open(saveas,'w').write(html)
    return html

def prune_html(html, saveas=None):
    '''
    Step B: Discard non-story HTML from 1_a_orig.html, creating 1_b_pruned.html.

    Insert the chapter name to an <h1> tag, so it appears as Chater headings in the LaTeX files later.
    '''

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
    txt += '\n'

    assert type(txt) == str
    assert len(txt) > 300
    assert len(txt.splitlines()) == 2
    assert txt.startswith('<div><h1>')
    assert txt.endswith('</p>\n</div>\n'), f'Wrong ending: {txt[-20:]}'

    if saveas: open(saveas,'w').write(txt)
    return txt


def fix_html(html, saveas=None):
    '''
    Step C: Fix HTML formatting issues in 1_b_pruned.html, creating 1_c_fix.html.

    - Fix typos, hyphenation, slashes, and ellipses:
    - Replace "reviews/favorites" with "reviews / favorites" etc
      for better linebreaking. Note: a/b/c/d/e requires two separate
      replacement passes; the first only yields a / b/c / d/e .
    - Note that the HTML is all one long line -- needed to prevent
      incorrect spaces when parsed by pandoc and tex.
    '''

    def fix_html_typos(s):
        for old, new in [
              [ 'spaceship inside..'               , 'spaceship inside.'                   ]
            , [ 'I got opening portion'            , 'I got the opening portion'           ]
            , [ 'as a mathematician"'              , 'as a mathematician."'                ]
            , [ 'December 19th, 1934</p>'          , 'December 19th, 1934:</p>'            ]
            , [ 'as he stood..'                    , 'as he stood.'                        ]
            , [ 'Genesis 18:23 '                   , 'Genesis 18:23, '                     ]
            , [ 'a hundreds of millions'           , 'hundreds of millions'                ]
            , [ 'hammered down the keys to,'       , 'hammered down the keys,'             ]
            , [ 'insane. She could decide whether' , "insane. She couldn't decide whether" ]
            , [ 'overwhelm positive effects'       , 'overwhelm the positive effects'      ]
        ]:
            s = s.replace(old, new)
        return s

    def fix_html_hyphens(s):
        '''
        Replace --- with em-dash and -- with en-dash, then replace all 
        remaining '-' characters with hyphen, en-dash, or em-dash as appropriate.

        Hyphenation rules:

        - "pages 10-20" : en-dash
        - "his well-being" : hyphen (letters)
        - "Uranium U-238" : hyphen (letter & number)
        - "I thought -" : em-dash for all other cases

        Note: each replacement needs to be run twice to deal with cases
        like "bric-a-brac" where re.sub doesn't replace the 2nd "-" because
        it resumed replacement after the 2nd matched group (the "a").
        
        WARNING / NOTE: pandoc replaces hyphens not with the "-" character 
        (ascii code 45, unicode name HYPHEN-MINUS)
        but with the "‐" character ('ascii' code 8208, unicode name HYPHEN).
        '''

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
        '''
        The phrase "reviews/comments/favorites/recommendations" needs to appear
        as "reviews / comments / favorites / recommendations" otherwise
        tex typesets it as a single huge word.
        
        Note: gotta run this pattern twice, because the first
        pass continues parsing the line after the matching foo/bar,
        resulting in "reviews / comments/favorites / recommendations".
        '''

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

    html = reduce( lambda x,f: f(x)
                 , [ fix_html_typos
                   , fix_html_hyphens
                   , fix_html_slashes
                   , fix_html_ellipses
                   ]
                 , html
                 )

    assert type(html) == str
    assert len(html) > 300
    assert len(html.splitlines()) == 2
    assert html.startswith('<div><h1>')
    assert html.endswith('</p>\n</div>\n'), f'Wrong ending: {html[-20:]}'

    if saveas: open(saveas,'w').write(html)
    return html


def html_to_tex(html, saveas=None):
    '''
    Step D: Use pandoc to convert HTML 1_c_fix.html to TEX 1_d_pandoc.tex.

    pandoc notes:

    --top-level-division: converts <h1> HTML tags
    to \chapter latex commands.

    html+smart / latex+smart: use smart-quotes ``like this.''

    Warning: doesn't smart-quote if leave off html+smart.
    Seems like a bug, bc docs say html no support +smart extension.
    https://pandoc.org/MANUAL.html#extension-smart
    '''

    p = subprocess.run( # TODO: subprocess.check_output returns stdout
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
    print(f'pandoc run:')
    print(f'returncode: {p.returncode}')
    print(f'len stdout: {len(p.stdout)}')
    print(f'stderr: "{p.stderr}"')

    tex = p.stdout

    assert type(tex) == str
    assert len(tex) > 300
    assert len(tex.splitlines()) > 100

    if saveas: open(saveas,'w').write(tex)
    return tex

def fix_tex(tex, saveas=None):
    '''
    Step E: Fix TEX formatting issues, creating 1_e_good.tex.
    '''

    def fix_tex_smartquotes(s):
        '''
        In theory, since we used pandoc with latex+smart (to make ``smart quotes''),
        there should be no normal double-quotes ("). But it missed some (at least 
        with the version of pandoc I used when I first wrote this in 2017). 
        So let's make extra-sure.
        '''

        s = re.sub(r'"([a-zA-Z0-9\.,!\-\?])', r'``\1', s) # "Hello ...  --> ``Hello ...
        s = re.sub(r'([a-zA-Z0-9\.,!\-\?])"', r"\1''", s) # ... end." --> ... end.''
        return s

    def fix_tex_newlines(s):
        '''
        Fix 2 problems with linebreaks near em-dashes.

        (1) Don't linebreak ``he said ---'' into ``he said\n---'' .
            Use a non-breaking space ``he said~---'' to acheive this.

        (2) Don't linebreak between emdash and close-quote, ie,
            don't linebreak ``he said ---'' into ``he said ---\n'' .
            To do this, replace --- with \=== which is a non-breaking em-dash
            provided by the extdash latex package (see header.tex).
        
            Note: Can't simply use nonbreaking em-dashes everywhere, because
            for some reason they eat the spaces surrounding them and it
            looks ugly. So use nonbreaking em-dashes ONLY before close-quotes.
        '''

        s = re.sub(r'([a-zA-Z0-9]) ---', r'\1~---', s)
        s = re.sub(r"---''", r"\\===''", s)
        return s

    def fix_tex_final_one_off_problems(s):
        '''
        Crappy line-breaking: in the final typeset PDF, the particular text

          pistols into your home---''

        extends into the margin.

        Solution: force newline: 

          pistols into your \\ home---''

        Warning: since the TeX files are not one long line, this 
        function is vulnerable to breaking if pandoc ever writes 
        the tex file like "pistols into \n your home".
        '''

        s = re.sub(r'pistols into your home', r'pistols into your \\\\ home', s)
        return s

    tex = reduce( lambda x,f: f(x)
                , [ fix_tex_smartquotes
                  , fix_tex_newlines
                  , fix_tex_final_one_off_problems 
                  ]
                , tex
                )

    assert type(tex) == str
    assert len(tex) > 300
    assert len(tex.splitlines()) > 100

    if saveas: open(saveas,'w').write(tex)
    return tex


def make_final_tex(texs, saveas):
    '''
    Step F: Given a list of strings, each one representing a tex-formatted chapter of
    the story, concatenate them along with header.tex and footer.tex,
    saving it into the file specified.
    '''

    s = '\n%%%%%%%%%%%%%%%%%%% NEW CHAPTER %%%%%%%%%%%%%%%%%%%%%%%%\n\n'
    story = '\n'.join([ open('header.tex').read()
                      , *[s+t for t in texs]
                      , open('footer.tex').read() 
                      ])

    # Verify that mm.tex is correct; certain fixed strings should appear in it.

    strs_should_be_present = [
        "bringing pistols into"
      , "to explain how I got"
      , "goodness of humanity"
      , "he could actually"
      , "--- that he"
      , "bric‐a‐brac"
      , "presumptions."
    ]
    for exp in strs_should_be_present:
        assert exp in story, f'UH OH: Expected string "{exp}" not found in final story "{tex_file}"!'
    print(f'Great! All test-strings were present in final story!')

    open(saveas,'w').write(story)


def tex_to_pdf(tex_file, saveas):
    '''
    Step G: Given a complete tex file, use pdflatex to convert it into the final PDF, saving the PDF under the given name.

    Note: Would've liked to be consistent with the other functions and 
    have this function take a string, and I can't figure out how to make pdflatex run from stdin
    without producing weird little error messages: "Please type a command or say 'end'". See:
    https://tex.stackexchange.com/questions/614919/passing-stdin-to-pdflatex-gives-please-type-a-command-or-say-end
    '''

    # For TOC generation, gotta run twice.
    for i in [1,2]:
        p = subprocess.run(
            [ 
            'pdflatex'
            , '-interaction=batchmode'
            , f'-jobname={saveas[:-4]}' # no file extension
            , tex_file
            ]
            , capture_output=True
            , text=True
            , check=True
        )

        print(f'pdflatex run #{i}:')
        print(f'returncode: "{p.returncode}"')
        print(f'stdout: "{p.stdout}"')
        print(f'stderr: "{p.stderr}"')

