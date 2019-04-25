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
# pandoc: convert from html to tex. 
#         --top-level-division: converts <h1> HTML tags 
#         to \chapter latex commands. 
#         --smart: use smart-quotes ``like this.''
#         Also, re-pandoc it to get smart-quotes everywhere,
#         fixing a parsing bug where <em> tags in quotes cause 
#         pandoc to not smart-quote the quotes.

function chapter() {
    local i=$1
    curl --silent \
      "https://www.fanfiction.net/s/10360716/${i}/The-Metropolitan-Man" \
    | tee "files/${i}_a_orig.html"                                      \
    | python3 prune_html.py                                             \
    | tee "files/${i}_b_pruned.html"                                    \
    | sed "s/spaceship inside\.\./spaceship inside./"                   \
    | sed "s/I got opening portion/I got the opening portion/"          \
    | sed "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                        \
    | sed "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"           \
    | sed "s/\(.\)-\(.\)/\1\&mdash;\2/g"                                \
    | tee "files/${i}_c_fix.html"                                       \
    | pandoc -f html  -t latex --top-level-division=chapter --smart     \
    | tee "files/${i}_d_pandoc1.tex"                                    \
    | pandoc -f latex -t latex --top-level-division=chapter --smart
}

echo "Starting to download The Metropolitan Man from fanfiction.net..."
for i in {1..13} ; do 
    echo "Downloading and processing Chapter $i..."
    chapter $i > "files/${i}_e_good.tex"
done
cat header.tex `ls -tr files/*_e_good.tex` footer.tex > mm.tex

echo "Building final PDF..."
pdflatex -interaction=batchmode mm.tex ; pdflatex -interaction=batchmode mm.tex 

echo "Done. Final PDF: mm.pdf."
ls -l mm.pdf