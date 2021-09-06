'''
things to add to doit tutorial
=================================

subtlty to string-interp
--------------------------

'actions': 2*[f'pdflatex -interaction=batchmode -jobname={dependencies} {targets}']

error:
NameError: name 'dependencies' is not defined

remove 'f' in the f-string, bc doit will string-interp later (I hope):

'actions': 2*['pdflatex -interaction=batchmode -jobname={dependencies} {targets}']

or: use old-style interp syntax:

'actions': 2*['pdflatex -interaction=batchmode -jobname=%(dependencies)s %(targets)s']


how to list info for all tasks
-------------------------------

$ doit list | tr -s ' ' | cut -d' ' -f1 | xargs -I xxx doit info xxx



task order
-------------

error:

$ doit info 2_prune_html

status     : error
 * The following targets do not exist:
    - 1_b_pruned.html
    - 2_b_pruned.html
    - 3_b_pruned.html
    - 4_b_pruned.html
    - 5_b_pruned.html
    - 6_b_pruned.html
    - 7_b_pruned.html
    - 8_b_pruned.html
    - 9_b_pruned.html
    - 10_b_pruned.html
    - 11_b_pruned.html
    - 12_b_pruned.html
    - 13_b_pruned.html
 * The following file dependencies are missing:
    - 2_a_orig.html
    - 4_a_orig.html
    - 10_a_orig.html
    ...



'''


# dodo.py: A build-script for pydoit, which downloads The Metropolitan Man
# from fanfiction.net and typesets it to PDF.
#
# It uses these programs:
#
# curl: download the raw HTML from fanfiction.net.
# prune_html.py: a python3 program that parses the HTML with BeautifulSoup.
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
#        sed passes; the first only yields a / b/c / d/e .
#      - Note that all sed commands should have the trailing "g" (global)
#        because the HTML is all one long line (needed to prevent
#        incorrect spaces when parsed by pandoc and tex).
# pandoc: convert from html to tex.
#         --top-level-division: converts <h1> HTML tags
#         to \chapter latex commands.
#         --smart: use smart-quotes ``like this.''
#         Also, re-pandoc it to get smart-quotes everywhere,
#         fixing a parsing bug where <em> tags in quotes cause
#         pandoc to not smart-quote the quotes.
#
# Run it by typing "./build.sh" at your terminal (no quotes).
#
# It creates several intermediate files in files/ with names like 3_a_orig.html.
# To remove all the files it creates, run "./build.sh cleanall".
# To remove all the files it creates except for the saved-to-disk raw HTML
# files from fanfiction.net, run "./build.sh clean".
#
# Note: _a_orig.html, _b_pruned.html, and _c_fix.html all have the story on 1 line,
# for some parsing reason.

# Qs for spence:
# Q1: clunky to have all helper fns of the form def f(dependencies).

from doit.tools import run_once
import re, os

CHAPTER_NUMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

def task_1_download():
    'Download chapters 1 thru 13, creating 1_a_orig.html, ...'

    # Approach 1: sequential download, no sub-tasks.
    #
    def download(targets):
        for t in targets:
            print(f'Downloading to create {t} ...')
            i = re.search(r'(\d+)',t).groups()[0]
            html = requests.get(
                f'https://www.fanfiction.net/s/10360716/{i}/The-Metropolitan-Man'
                ).content
            open(t,'w').write(html)

    return {
          'targets': [f'files/{i}_a_orig.html' for i in CHAPTER_NUMS]
        , 'actions': [download]
        # , 'uptodate': [run_once]
    }

    # Approach 2: parallelize into sub-tasks.
    #
    # for i in CHAPTER_NUMS:
    #     yield {
    #         'name': str(i),
    #         'targets': [f'files/{i}_a_orig.html'],
    #         'actions': [
    #                      'curl --silent '
    #                     f'https://www.fanfiction.net/s/10360716/{i}/The-Metropolitan-Man '
    #                      '> {targets}' # NOTE: subtle: can use f-string {targets} but without the , gotta use %(targets)s to delay interpolation
    #                    ],
    #         'uptodate': [run_once]
    #     }

# from doit import create_after
# @create_after(executed='1_download')
def task_2_prune_html():
    'Discard non-story HTML from 1_a_orig.html, creating 1_b_pruned.html'

    def prune_html(dependencies, targets):
        import bs4, re

        fn_in = dependencies[0]
        fn_out = targets[0]

        soup = bs4.BeautifulSoup(open(fn_in,'r').read(), features='html.parser')
        story = soup.find(id='storytext')
        story.attrs = None
        chapter_name = re.search(
            r'Chapter \d+: (.*), a superman fanfic',
            soup.title.text
            ).group(1)

        h = soup.new_tag('h1')
        h.string = chapter_name
        story.insert(0, h)

        open(fn_out,'w').write(story)

    return {
        'file_dep': [f'{i}_a_orig.html' for i in CHAPTER_NUMS],
        'targets': [f'{i}_b_pruned.html' for i in CHAPTER_NUMS],
        'actions': [prune_html]
    }

def task_3_fix_html():
    'Fix HTML formatting issues, creatign 1_c_fix.html'
    '''
    | fix_html_typos                                                    \
    | fix_html_hyphens                                                  \
    | fix_html_slashes                                                  \
    | fix_html_ellipses                                                 \
    | tee "files/${i}_c_fix.html"                                       \
    '''
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
        s = re.sub('...','…',s)

        # 2. Remove space before ellipsis, ie,
        #    convert "he said ..." into "he said..." .
        #    This looks better and also prevents linebreaks before "..." .
        s = re.sub( r'([a-zA-Z0-9]) …', r'\1…', s)

        return s

    def fix_all_html(dependencies, targets):
        fin = dependencies[0]
        fout = targets[0]
        s = open(fin,'r').read()
        s = fix_html_typos(s)
        s = fix_html_hyphens(s)
        s = fix_html_slashes(s)
        s = fix_html_ellipses(s)
        open(fout,'w').write(s)

    return {
        'file_dep': [f'{i}_b_pruned.html' for i in CHAPTER_NUMS],
        'targets': [f'{i}_c_fix.html' for i in CHAPTER_NUMS],
        'actions': [fix_all_html]
    }


def task_4_html_to_tex():
    'Use pandoc to convert HTML to TEX, creating 1_d_pandoc1.tex'
    '''
    | pandoc -f html  -t latex --top-level-division=chapter --smart     \
    | tee "files/${i}_d_pandoc1.tex"                                    \
    | pandoc -f latex -t latex --top-level-division=chapter --smart     \
    '''
    return {
        'file_dep': [f'{i}_c_fix.html' for i in CHAPTER_NUMS],
        'targets': [f'{i}_d_pandoc1.tex' for i in CHAPTER_NUMS],
        'actions': [ f'pandoc -f html  -t latex '
                     f'--top-level-division=chapter --smart '
                     f'--output={i}_d_pandoc1.tex '
                     f'{i}_c_fix.html'
                     for i in CHAPTER_NUMS
                   ]
    }

def task_5_pandoc2():
    'Run pandoc twice to fix a formatting bug, creating 1_d_pandoc2.tex'
    return {
        'file_dep': [f'{i}_d_pandoc1.tex' for i in CHAPTER_NUMS],
        'targets': [f'{i}_d_pandoc2.tex' for i in CHAPTER_NUMS],
        'actions': [ f'pandoc -f latex -t latex '
                     f'--top-level-division=chapter --smart '
                     f'--output {i}_d_pandoc2.tex'
                     f'{i}_d_pandoc1.tex'
                     for i in CHAPTER_NUMS
                   ]
    }

def task_5_fix_tex():
    'Fix TEX formatting issues, creatign 1_e_good.tex'

    def fix_all_tex(dependencies, targets):
        fin = dependencies[0]
        fout = targets[0]
        s = open(fin,'r').read()
        s = fix_tex_smartquotes(s)
        s = fix_tex_newlines(s)
        s = fix_tex_final_one_off_problems(s)
        open(fout,'w').write(s)

    def fix_tex_smartquotes(s):
        # In theory, double-pandocing should've removed all normal
        # double-quotes, but it missed some. So let's make extra-sure.

        s = re.sub(r'([a-zA-Z0-9])', r'``\1', s)
        s = re.sub(r'([a-zA-Z0-9])"', r"\1''")
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
        s = re.sub(r"---''", r"\\\\===''", s)
        return s

    def fix_tex_final_one_off_problems(s):
        # Crappy line-breaking: your home---'' extends into the margin.
        # Force newline: your \\ home---''
        s = re.sub(r'pistols into your home', r'pistols into your \\ home', s)
        return s

    return {
        'file_dep': [f'{i}_d_pandoc2.tex' for i in CHAPTER_NUMS],
        'targets': [f'{i}_e_good.tex' for i in CHAPTER_NUMS],
        'actions': [fix_all_tex]
    }


def task_6_combine_tex():
    'Combine all *_e_good.tex files into final TEX file, mm.tex'
    'cat header.tex $(ls -tr files/*_e_good.tex) footer.tex > mm.tex'
    return {
        'file_dep': [f'files/{i}_e_good.tex' for i in CHAPTER_NUMS], # TODO: sort?
        'targets': ['mm.tex'],
        'actions': ['cat header.tex {dependencies} footer.tex > {targets}']
    }
def task_7_tex_to_pdf():
    'Pdflatex to create final PDF.'
    'Run twice to create TOC.'
    return {
        'file_dep': ['mm.tex'],
        'targets': ['mm.pdf'],
        'actions': 2*['pdflatex -interaction=batchmode -jobname={dependencies} {targets}']
    }

def task_test():
    'Verify that mm.tex is correct; certain fixed strings should appear in it.'
    def ok(dependencies):
        f = dependencies[0]
        strs_should_be_present = [
            "bringing pistols into"
          , "to explain how I got"
          , "goodness of humanity"
          , "he could actually"
          , "--- that he"
          , "bric.*brac"
          , "presumptions."
        ]
        # TODO: Doesn't seem like the right way to do it.
        # Will this actually abort doit? Should this task write smt to disk?
        # How store info that the whole build completed successfully?
        with open(f,'r') as f:
            txt = f.read()
            for s in strs_should_be_present:
                assert s in txt, f'UH OH: String "{s}" not found in final story "{f}"!'
        print(f'Great! All test-strings were present in final story "{f}"!')

    return {
        'file_dep': ['mm.tex'],
        'actions': [ok]
    }
