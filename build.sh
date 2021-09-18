#!/bin/bash
#
# Note, Sep 2021: This file got too unwieldy, so I ported it to Python: build.py
#
# This bash script downloads The Metropolitan Man from fanfiction.net
# and typesets it to PDF. It uses these programs:
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
#         -f html+smart -t latex+smart: use smart-quotes ``like this.''
#
# Run it by typing "./build.sh" at your terminal (no quotes).
#
# It creates several intermediate files in files/ with names like 3_a_orig.html.
# To remove all the files it creates, run "./build.sh cleanall".
# To remove all the files it creates except for the saved-to-disk raw HTML
# files from fanfiction.net, run "./build.sh clean".

set -e  # bail if fail

function  remove_some_intermediate_files() {
    # Given a string s, deletes html and tex files
    # of the form \d_x_*.(html|tex), where \d is any digit
    # and x is a character in the given string s.
    # Also deletes annoying intermediate tex files aux, log, etc.

    local s="$1"
    rm -f mm.aux mm.log mm.out mm.toc  # ugh, don't bother wtih wildcards mm.{aux,log,out,toc} with zsh, it's weird: https://unix.stackexchange.com/questions/298548/matching-files-using-curly-brace-expansion-in-zsh#298625
    pushd files
        rm -f `ls | egrep "\d+_[${s}]_.*\.(html|tex)"`
    popd
}

if test "$1" = "clean" ; then
    echo "Removing generated files"
    remove_some_intermediate_files bcde
    exit 0
fi

if test "$1" = "cleanall" ; then
    echo "Removing ALL generated files, even cached raw html"
    remove_some_intermediate_files abcde
    exit 0
fi

if test "$1" = "test" ; then
    CHECK_THESE_STRINGS=(       \
        "bringing pistols into" \
        "to explain how I got"  \
        "goodness of humanity"  \
        "he could actually"     \
        "--- that he"           \
        "bric.*brac"            \
        "presumptions\."        \
        )
    for s in "${CHECK_THESE_STRINGS[@]}" ; do
        egrep -- "${s}" mm.tex
    done
    exit 0
fi


function get() {
    # Cache the raw HTML from fanfiction.net.
    local i=$1
    local f=$2
    if [ -f "$f" ]; then
        cat "$f"
    else
        curl --silent \
          "https://www.fanfiction.net/s/10360716/${i}/The-Metropolitan-Man" \
        | tee "$f"
    fi
}

function fix_html_typos() {
    sed                                                                 \
        -e "s/spaceship inside\.\./spaceship inside./g"                 \
        -e "s/I got opening portion/I got the opening portion/g"        \
        -e "s/as a mathematician\"/as a mathematician.\"/g"             \
        -e "s|December 19th, 1934</p>|December 19th, 1934:</p>|g"       \
        -e "s/as he stood\.\./as he stood./g"                           \
        -e "s/Genesis 18:23 /Genesis 18:23, /g"                         \
        -e "s/a hundreds of millions/hundreds of millions/g"
}

function fix_html_hyphens() {
    # Replace - with hyphen, en-dash, or em-dash as appropriate.
    # But first replace --- with em-dash and -- with en-dash.
    #
    # Note: each replacement needs to be run twice to deal with cases
    # like "bric-a-brac" where sed doesn't replace the 2nd "-" because
    # it resumed replacement after the 2nd matched group (the "a").
    #
    # WARNING: pandoc replaces hyphens not with the "-" character 
    # (ascii code 45, unicode name HYPHEN-MINUS)
    # but with the "‐" character ('ascii' code 8208, unicode name HYPHEN).
    sed                                                                 \
        -e "s/\([^-]\)---\([^-]\)/\1\&mdash;\2/g"                       \
        -e "s/\([^-]\)---\([^-]\)/\1\&mdash;\2/g"                       \
        -e "s/\([^-]\)--\([^-]\)/\1\&ndash;\2/g"                        \
        -e "s/\([^-]\)--\([^-]\)/\1\&ndash;\2/g"                        \
        -e "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                       \
        -e "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                       \
        -e "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"          \
        -e "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"          \
        -e "s/-/\&mdash;/g"
}

function fix_html_slashes() {
    # The phrase "reviews/comments/favorites/recommendations" needs to appear
    # as "reviews / comments / favorites / recommendations" otherwise
    # tex typesets it as a single huge word.
    #
    # Note: gotta run this pattern twice, because the first
    # pass continues parsing the line after the matching foo/bar,
    # resulting in "reviews / comments/favorites / recommendations".
    #
    # The regex is "3 or more letters, slash, 3 or more letters"
    # turns into "match group 1, space, slash, space, match group 2".
    # It's hard to read because the match groups and curlies have to be escaped.

    sed -e "s|\([a-zA-Z]\{3,\}\)/\([a-zA-Z]\{3,\}\)|\1 / \2|g"          \
        -e "s|\([a-zA-Z]\{3,\}\)/\([a-zA-Z]\{3,\}\)|\1 / \2|g"
}

function fix_html_ellipses() {
    # 1. Replace "..." with the unicode "…" for uniformity.
    # 2. Remove space before ellipsis, ie,
    #    convert "he said ..." into "he said..." .
    #    This looks better and also prevents linebreaks before "..." .

    sed -e 's/\.\.\./…/g'                                               \
        -e 's/\([a-zA-Z0-9]\) …/\1…/g'
}

function fix_tex_smartquotes() {
    # In theory, double-pandocing should've removed all normal
    # double-quotes, but it missed some. So let's make extra-sure.

    sed -e 's/"\([a-zA-Z0-9]\)/``\1/g'                                  \
        -e "s/\([a-zA-Z0-9]\)\"/\1''/g"
}

function fix_tex_newlines() {
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

    sed -e "s/\([a-zA-Z0-9]\) ---/\1~---/g"                             \
    | sed -e "s/---''/\\\\===''/g"
}

function fix_tex_final_one_off_problems() {
    # Crappy line-breaking: your home---'' extends into the margin.
    # Force newline: your \\ home---''
    sed -e 's/pistols into your home/pistols into your \\\\ home/'
}

function chapter() {
    local i=$1
    local ii=`printf '%02d' $i` # zero-pad
    local f="files/${ii}_a_orig.html"
    get "$i" "$f"                                                       \
    | python3 prune_html.py                                             \
    | tee "files/${ii}_b_pruned.html"                                   \
    | fix_html_typos                                                    \
    | fix_html_hyphens                                                  \
    | fix_html_slashes                                                  \
    | fix_html_ellipses                                                 \
    | tee "files/${ii}_c_fix.html"                                      \
    | pandoc -f html+smart  -t latex+smart --top-level-division=chapter \
    | tee "files/${ii}_d_pandoc1.tex"                                   \
    | fix_tex_smartquotes                                               \
    | fix_tex_newlines                                                  \
    | fix_tex_final_one_off_problems                                    \
    > "files/${ii}_e_good.tex"
}

echo "Starting to download The Metropolitan Man from fanfiction.net..."
for i in {1..13} ; do
    echo "Downloading and processing Chapter $i..."
    chapter $i
done
cat header.tex $(ls -tr files/*_e_good.tex) footer.tex > mm.tex

echo "Building final PDF..."
pdflatex -interaction=batchmode mm.tex
pdflatex -interaction=batchmode mm.tex

echo "Done. Final PDF: mm.pdf."
ls -l mm.pdf
