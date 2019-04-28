# Print "The Metropolitan Man" fanfic as a hard-copy book.

This repo offers code to download and typeset _The Metropolitan Man_, 
the rationalist Superman fanfic by [Alexander Wales](https://alexanderwales.com/).

Armed with the PDF `mm.pdf` and the cover art in `cover-art/`, 
you can print your own hard-copy of _The Metropolitan Man_ 
at online book-printing sites like http://www.lulu.com. 

![](/images/mm.jpg)

_The Metropolitan Man_ was originally hosted 
[here](http://www.fanfiction.net/s/10360716/1/The-Metropolitan-Man) on fanfiction.net.

The cover art comes from Mike Schwörer's GitHub repo 
[Metropolitan-Man-Lyx](https://github.com/Mikescher/Metropolitan-Man-Lyx), 
and was originally created by [Justin Maller](http://justinmaller.com/wallpaper/356/).


## How to use

1. **Install dependencies:** `pip install -r requirements.txt`

2. **Build the PDF:** Run the shell script `build.sh` at the terminal 
to download _The Metropolitan Man_ from fanfiction.net and 
typeset it into a PDF named `mm.pdf`:

        $ ./build.sh

    The script even embeds itself into the generated PDF, in case readers want to see how to programatically generate the PDF for themselves!

    Intermediate files are stored in `files/`, and are useful for exploring and debugging.

3. **Print the book at lulu.com:** At http://lulu.com, go through the
flow for printing a 6"x9" paperback. Upload the story `mm.pdf` and
use the cover-art designer to upload the front, back, and spine
cover art provided in `cover-art/`. The book costs less than $10 to print!

## How it works

1. The shell script `build.sh` uses `curl` to download each chapter of _The Metropolitan Man_ from fanfiction.net, saving the raw HTML to `i_a_orig.html`, where chapter `i` ranges from 1 to 13. 

2. The python script `prune_html.py` uses the excellent `BeautifulSoup` package to parse each chapter's HTML, selecting only the chapter name and the specific `<div>` that contains the actual story. It adds the chapter name as an `<h1>` tag inside the story's `<div>` because `h1` tags will be converted to Chapters in the HTML-to-Tex conversion. The resulting HTML is saved in `i_b_pruned.html`. 

    _Minor note:_ this file is a single long line. I would've preferred to use `BeautifulSoup`'s `prettify()` method to make it easier to read, but this has the unfortunate effect that `<em>` tags appear on their own line, which causes an extra space to be incorrectly inserted in certain cases. For example, `prettify()` converts the following HTML

        <p>"I read <em>The Daily Planet</em>."</p>

    to

        <p>
         "I read
         <em>
          The Daily Planet
         </em>
         ."
        </p>

    which causes pandoc to produce Tex code with an extra space before the period:

        ``I read \emph{The Daily Planet} .''   % incorrect space before period!

3. A series of `sed` commands fix a couple typos and correct the hyphenation. Probably due to shortcomings in the text-editing environment at fanfiction.net, the author used only hyphens (dashes), rather than en-dashes and em-dashes (longer dashes). The hyphenation rules are as follows:

    - "pages 10-20" : en-dash (number range)
    - "his well-being" : hyphen (letters)
    - "Uranium U-238" : hyphen (letter & number)
    - "I thought -" : em-dash for all other cases

    The resulting HTML is saved in `i_c_fix.html`.

4. The excellent document-conversion tool `pandoc` converts the HTML to Tex. We use the option `--top-level-division=chapter` to convert `h1` tags to Tex chapters, and the option `--smart` to convert double quotes `"` to Tex's left- and right-sided double quotes \`\` and `''`. The resulting Tex code is written to `i_d_pandoc1.tex`. Note that this is not a "standalone" Tex file because it does not begin with `\documentclass{}` or have any other preamble that Tex requires. This is added next.

    _Minor note:_ We then run pandoc again, to fix an issue where it doesn't detect smart quotes when `<em>` tags appear inside the quoted string. 

5. The `cat` utility concatenates these chapters together, prepending a tex file `header.tex` at the beginning and appending `footer.tex` to the end. The file `header.tex` contains the Tex preamble that sets the font size, table of contents, copyright, image attributions, and other front-matter. This final tex file is written to `mm.tex`.

6. The `pdflatex` utility converts the tex file `mm.tex` to the PDF `mm.pdf`. You need to run `pdflatex` twice: the first run generates the table of contents file `mm.toc`, which is used by `pdflatex` in the second run to generate the correct table of contents.


## Troubleshooting

To see if you have all the correct programs installed to run `build.sh`, run this command. The resulting PDF `tmp.pdf` illustrates the various typesetting pitfalls with hyphenation and smart-quotes. (I.e., if you leave out the `sed` commands, the hyphenation won't look right, and if you leave out the second `pandoc` run, the quote marks won't look right.)

    echo "
        <html>
        <head><title>The Metropolitan Man Chapter 8: My Chapter Name, a superman fanfic | FanFiction</title></head>
        <body>
        <div id=\"storytext\">
            <p>Start.</p>
            <p>\"I read <em>The Daily Planet</em> today,\" (Smart quotes ok?) </p>
            <p>See pages 10-20 (uses en-dash?)</p>
            <p>this-or-that (uses hyphens?)</p> 
            <p>I stole a piece of PU-356 from the lab. (uses hyphen?)</p>    
            <p>\"But I never thought -\" (uses em-dash?)</p>
            <p><em>\"Don't touch anyth- \"</em> (uses em-dash within emph tags?)</p>
            <p>He'd left the naiveté behind him. (correctly interprets unicode accented e?)</p>
            <p>End.</p>
        </div>
        </body>
        </html>
    " \
    | python3 prune_html.py                                                         \
    | sed "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                                    \
    | sed "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"                       \
    | sed "s/\(.\)-\(.\)/\1\&mdash;\2/g"                                            \
    | pandoc -f html  -t latex --standalone --top-level-division=chapter --smart    \
    | pandoc -f latex -t latex --standalone --top-level-division=chapter --smart    \
    | pdflatex -jobname=tmp


![](/images/typesetting-pitfalls.png)

