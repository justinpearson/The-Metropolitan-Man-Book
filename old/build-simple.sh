#!/bin/bash
#
# Note: As of Sep 2021, this script no longer works, because
# fanfiction.net has implemented a captcha which rejects web-scraping
# tools like curl.
#
# This bash script downloads The Metropolitan Man from fanfiction.net
# and typesets it to PDF.
#
# It uses these programs:
# 
# curl: download the raw HTML from fanfiction.net.
# prune_html.py: a python3 program that parses the HTML with BeautifulSoup.
# pandoc: convert from html to tex. 
#         --top-level-division: converts <h1> HTML tags 
#         to \chapter latex commands. 
#         -f html+smart -t latex+smart: use smart-quotes ``like this.''
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
    | pandoc -f html+smart  -t latex+smart --top-level-division=chapter
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