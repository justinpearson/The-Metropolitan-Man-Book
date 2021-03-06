#!/bin/bash
#
# build.sh

# This bash script downloads The Metropolitan Man from fanfiction.net
# and typesets it to PDF. Run it by typing "./build.sh" at your terminal.
# It uses these programs:
# 
# curl: download the raw HTML from fanfiction.net.
# prune_html.py: a python3 program that parses the HTML with BeautifulSoup.
# pandoc: convert from html to tex. 
#         --top-level-division: converts <h1> HTML tags 
#         to \chapter latex commands. 
#         --smart: use smart-quotes ``like this.''
#         Also, re-pandoc it to get smart-quotes everywhere,
#         fixing a parsing bug where <em> tags in quotes cause 
#         pandoc to not smart-quote the quotes.
# pdflatex: convert the .tex file to a PDF using the TeX document-
#           typesetting program created by Donald Knuth.
#           You have to run it twice: once to gather page information
#           for the table of contents, and again to build the final
#           doc with a correct table of contents.

function chapter() {
    local i=$1
    curl --silent \
      "https://www.fanfiction.net/s/10360716/${i}/The-Metropolitan-Man" \
    | python3 prune_html.py                                             \
    | pandoc -f html  -t latex --top-level-division=chapter --smart     \
    | pandoc -f latex -t latex --top-level-division=chapter --smart     
}

echo "Starting to download The Metropolitan Man from fanfiction.net..."
for i in {1..13} ; do 
    echo "Downloading and processing Chapter $i..."
    chapter $i > "files/${i}.tex"
done
cat header.tex `ls -tr files/*.tex` footer.tex > mm.tex

echo "Building final PDF..."
pdflatex -interaction=batchmode mm.tex
pdflatex -interaction=batchmode mm.tex 

echo "Done. Final PDF: mm.pdf."
ls -l mm.pdf