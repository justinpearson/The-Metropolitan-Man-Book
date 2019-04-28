#!/bin/bash
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


set -e 

function  clean_by_prefix() {
    local s="$1"
    rm -f mm.{aux,log,out,toc}
    pushd files
        rm -f `ls | egrep "\d+_[${s}]_.*\.(html|tex)"`
    popd
}

if test "$1" = "clean" ; then
    echo "Removing generated files"
    clean_by_prefix bcde
    exit 0
fi

if test "$1" = "cleanall" ; then
    echo "Removing ALL generated files, even cached raw html"
    clean_by_prefix abcde
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
        -e "s/Genesis 18:23 /Genesis 18:23, /g"
}

function fix_html_hyphens() {
    sed                                                                 \
        -e "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                       \
        -e "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"          \
        -e "s/\(.\)-\(.\)/\1\&mdash;\2/g"
}

function fix_html_slashes() {
    # Fixes "reviews/comments/favorites/recommendations" need to appear
    # as "reviews / comments / favorites / recommendations" otherwise
    # tex typesets them as a single huge word.
    # 
    # Note: these must be two separate sed commands, because the first
    # one continues parsing the line after the matching foo/bar,
    # resulting in "reviews / comments/favorites / recommendations".
    #
    # The regex is "3 or more letters, slash, 3 or more letters" 
    # turns into "match group 1, space, slash, space, match group 2".
    # It's hard to read because slashes have to be escaped.

    sed -e "s|\([a-zA-Z]\{3,\}\)/\([a-zA-Z]\{3,\}\)|\1 / \2|g"        \
    | sed -e "s|\([a-zA-Z]\{3,\}\)/\([a-zA-Z]\{3,\}\)|\1 / \2|g"
}

function fix_html_ellipses() {
    sed -e 's/\([a-zA-Z0-9]\) …/\1…/g'
}

function fix_tex_smartquotes() {
    # In theory, double-pandocing should've removed all normal
    # double-quotes, but it missed some. So let's make extra-sure. 

    sed -e 's/"\([a-zA-Z0-9]\)/``\1/g'                                  \
        -e "s/\([a-zA-Z0-9]\)\"/\1''/g"
}

function fix_tex_newlines() {
    # Fix 3 problems with linebreaks near ellipses (...) and em-dashes.
    # (1) No space before ellipsis, ie, 
    #     convert "he said ..." into "he said..." .
    # (2) Don't linebreak ``he said ---'' into ``he said\n---'' .
    #     Use a non-breaking space ~ to acheive this.
    # (3) Don't linebreak ``You said ---'' texing to ``You said ---\n''
    #     To do this, replace --- with \=== which is a non-breaking em-dash
    #     provided by the extdash latex package (see header.tex).
    #     Note: Can't use nonbreaking em-dashes everywhere, because 
    #     for some reason they eat the spaces surrounding them.

    sed -e 's/\([a-zA-Z0-9]\) \\ldots{}/\1\\ldots{}/g'                    \
    | sed -e "s/\([a-zA-Z0-9]\) ---/\1~---/g"                             \
    | sed -e "s/---''/\\\\===''/g"
}

# TODO:
# writing. I deserve worse than what you said. I'm just trying to explain
# \ldots{} to explain how I got to where I am now.'' He took a breath. ``I


function fix_tex_final_one_off_problems() {
    # Crappy line-breaking: your home---'' extends into the margin.
    # Force newline: your \\ home---''
    # These two backslashes need to be escaped for bash, and then the 
    # resulting double-backslashes need to be escaped again for sed!
    sed -e 's/pistols into your home/pistols into your \\\\ home/'
}

function chapter() {
    local i=$1
    local f="files/${i}_a_orig.html"
    get "$i" "$f"                                                       \
    | python3 prune_html.py                                             \
    | tee "files/${i}_b_pruned.html"                                    \
    | fix_html_typos                                                    \
    | fix_html_hyphens                                                  \
    | fix_html_slashes                                                  \
    | fix_html_ellipses                                                 \
    | tee "files/${i}_c_fix.html"                                       \
    | pandoc -f html  -t latex --top-level-division=chapter --smart     \
    | tee "files/${i}_d_pandoc1.tex"                                    \
    | pandoc -f latex -t latex --top-level-division=chapter --smart     \
    | fix_tex_smartquotes                                               \
    | fix_tex_newlines                                                  \
    | fix_tex_final_one_off_problems                                    \
    > "files/${i}_e_good.tex"
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
