'''
dodo.py: A build-script for pydoit, which downloads The Metropolitan Man
from fanfiction.net and typesets it to PDF.

Installation:

    pip3 install pydoit

Usage:

    List all tasks:  $ doit list
 
    Print info about a task:   $ doit info 1_download

    Run a task:   $ doit run 1_download

    Forget a task, so that 'doit run' will run it for sure:   $ doit forget 1_download ; doit run 1_download

    Run all tasks that need to be run:   $ doit


Notes:

    This file calls many of the library functions in lib.py.

    See build.py to see how to build & typeset the Metropolitan Man PDF without installing doit.


Justin Pearson
Sep 13, 2021
'''


# from doit.tools import run_once

from lib import url_for_chapter, download, prune_html, fix_html, html_to_tex, fix_tex, make_final_tex, tex_to_pdf

CHAPTER_NUMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

def task_1_download():
    'Download chapters 1 thru 13, creating 1_a_orig.html, ...'

    for i in CHAPTER_NUMS:
        fn = f'files/{i:02}_a_orig.html'
        yield {
              'name': i,
              'targets': [fn],
              'actions': [ (download, (url_for_chapter(i, cached=True),), {'saveas': fn}) ],
              'clean': True
              # 'uptodate': [run_once]
        }

def task_2_prune_html():
    'Discard non-story HTML from 1_a_orig.html, creating 1_b_pruned.html'

    for i in CHAPTER_NUMS:
        fin = f'files/{i:02}_a_orig.html'
        fout = f'files/{i:02}_b_pruned.html'
        yield {
            'name': i,
            'file_dep': [fin],
            'targets': [fout],
            'actions': [(lambda fin,fout: prune_html(html=open(fin).read(),saveas=fout),(fin,fout))],
            'clean': True
        }

def task_3_fix_html():
    'Fix HTML formatting issues in 1_b_pruned.html, creating 1_c_fix.html'
    for i in CHAPTER_NUMS:
        fin = f'files/{i:02}_b_pruned.html'
        fout = f'files/{i:02}_c_fix.html'
        yield {
            'name': i,
            'file_dep': [fin],
            'targets': [fout],
            'actions': [( lambda fin,fout: fix_html( html = open(fin).read(), saveas = fout ), (fin,fout) )],
            'clean': True
        }


def task_4_html_to_tex():
    'Use pandoc to convert HTML to TEX, creating 1_d_pandoc1.tex'

    for i in CHAPTER_NUMS:
        fin = f'files/{i:02}_c_fix.html'
        fout = f'files/{i:02}_d_pandoc1.tex'
        yield {
            'name': i,
            'file_dep': [fin],
            'targets': [fout],
            'actions': ['pandoc -f html+smart -t latex+smart --top-level-division=chapter --output %(targets)s %(dependencies)s'],
            'clean': True
        }

def task_5_fix_tex():
    'Fix TEX formatting issues in 1_d_pandoc1.tex, creating 1_e_good.tex'

    for i in CHAPTER_NUMS:
        fin = f'files/{i:02}_d_pandoc1.tex'
        fout = f'files/{i:02}_e_good.tex'
        yield {
            'name': i,
            'file_dep': [fin],
            'targets': [fout],
            'actions': [( lambda fin,fout: fix_tex( tex = open(fin).read(), saveas = fout ), (fin,fout) )],
            'clean': True
        }

def task_6_make_final_tex():
    'Combine all *_e_good.tex files into final TEX file, mm.tex'

    ch_deps = [f'files/{i:02}_e_good.tex' for i in CHAPTER_NUMS]
    deps = ['header.tex'] + ch_deps + ['footer.tex']
    fout = 'mm.tex'
    return {
        'file_dep': deps,
        'targets': [fout],
        'actions': [( lambda fins, fout: make_final_tex(texs=[open(f).read() for f in ch_deps], saveas=fout), (ch_deps, fout) )],
        'clean': True
    }

def task_7_tex_to_pdf():
    'Pdflatex to create final PDF.'
    'Run twice to create TOC.'

    n = 'mm'
    tex = n+'.tex'
    pdf = n+'.pdf'
    return {
        'file_dep': [tex],
        'targets': [pdf],
        'actions': 2*[f'pdflatex -interaction=batchmode {tex}'],
        'clean': True
    }

# Convenience tasks for development:

# def task_tmp_open_pdf():
#     return {
#         'file_dep': ['mm.pdf'],
#         'actions': ['open mm.pdf']
#     }

# def task_mypy():
#     return {
#         'file_dep': glob('*.py'),
#         'actions': ['mypy %(dependencies)s']
#     }

# def task_tmp_readme():
#     return {
#         'file_dep': ['README.md'],
#         'actions': ['pandoc --standalone -f markdown -t html --metadata title="foo" README.md > README.html ; open README.html']
#     }
