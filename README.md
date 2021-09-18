# Print "The Metropolitan Man" fanfic as a hard-copy book.

- [Intro](#intro)
- [Quick Start](#quick-start)
- [How it works](#how-it-works)
- [Other ways to build the PDF](#other-ways-to-build-the-pdf)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Intro

This repo offers code to download and typeset _The Metropolitan Man_,
the rationalist Superman fanfic by [Alexander Wales](https://alexanderwales.com/).

Armed with the PDF `mm.pdf` and the cover art in `cover-art/`,
you can print your own hard-copy book of _The Metropolitan Man_
at online book-printing sites like http://www.lulu.com:

![](/images/mm.jpg)

_The Metropolitan Man_ was originally hosted
[here](http://www.fanfiction.net/s/10360716/1/The-Metropolitan-Man) on fanfiction.net.

The cover art comes from Mike Schwörer's GitHub repo
[Metropolitan-Man-Lyx](https://github.com/Mikescher/Metropolitan-Man-Lyx),
and was originally created by [Justin Maller](http://justinmaller.com/wallpaper/356/).


## Quick Start

**Overview:** We use the [`doit`](https://pydoit.org/) build system to run tasks defined in `dodo.py`.
(Alternatively, if you don't want to install `doit`, you can run `build.py`, which performs the same steps, and has the same dependencies.)
The first task uses the [`selenium`](https://selenium-python.readthedocs.io/) automated web-browser library to download the story from fanfiction.net as HTML.
The next task uses the HTML-parsing Python library [`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/) to extract the story.
The next task uses the document converter utility [`pandoc`](https://pandoc.org/) to convert the text from HTML into TeX.
The final task uses [`pdflatex`](http://tug.org/mactex/) to build the final PDF `mm.pdf` from the TeX file.

1. **Install dependencies (MacOS)**

    - For `BeautifulSoup`, `pydoit`, and `selenium` Python libraries, run

        ```bash
        python3 -m pip install -r requirements.txt
        ```

    - For the `pandoc` command-line utility, run

        ```bash
        brew install pandoc
        ```

    - For the `pdflatex` command-line utility, install [MacTeX](http://tug.org/mactex/):

        ```bash
        brew install --cask basictex
        ```

2. **Build the PDF**

    Ensure the `doit` build system is set up correctly by asking it to list the processing tasks in `dodo.py`:

        $ doit list

        1_download         Download chapters 1 thru 13, creating 1_a_orig.html, ...
        2_prune_html       Discard non-story HTML from 1_a_orig.html, creating 1_b_pruned.html
        3_fix_html         Fix HTML formatting issues in 1_b_pruned.html, creating 1_c_fix.html
        4_html_to_tex      Use pandoc to convert HTML to TEX, creating 1_d_pandoc1.tex
        5_fix_tex          Fix TEX formatting issues in 1_d_pandoc1.tex, creating 1_e_good.tex
        6_make_final_tex   Combine all *_e_good.tex files into final TEX file, mm.tex
        7_tex_to_pdf       Pdflatex to create final PDF.

    These tasks download _The Metropolitan Man_ from fanfiction.net and typeset it into a PDF named `mm.pdf`.
    Next, run the `doit` build system at the terminal, which executes the tasks:

        $ doit

    Re-running `doit` is safe: It only re-runs a step if its dependencies have changed.
    If you are editing or debugging, you can have `doit` automatically watch the files and re-run itself with

        $ doit auto

    The build script even embeds itself into the generated PDF, in case readers want to see how to programatically generate the PDF for themselves!

    Intermediate files are stored in `files/`, and are useful for exploring and debugging.

3. **Print the book at lulu.com:** At http://lulu.com, go through the
flow for printing a 6"x9" paperback. Upload the story `mm.pdf` and
use the cover-art designer to upload the front, back, and spine
cover art provided in `cover-art/`. The book costs less than $10 to print!



## How it works

Both `doit` and `build.py` use `lib.py` to perform the following steps to download and process _The Metropolitan Man_. *(Note: `build.py` does not produce intermediate files like `1_a_orig.html`; it keeps everything in memory.)*

1. We use the `selenium` web-browser automation tool to download each chapter of _The Metropolitan Man_ from fanfiction.net, saving the raw HTML to `i_a_orig.html`, where chapter `i` ranges from 1 to 13.

2. We use the excellent `BeautifulSoup` Python library to parse each chapter's HTML, selecting only the chapter name and the specific `<div>` that contains the actual story. We add the chapter name as an `<h1>` tag inside the story's `<div>` because `h1` tags will be converted to Chapters in the HTML-to-TeX conversion. The resulting HTML is saved in `i_b_pruned.html`.

    _Minor note:_ the HTML files `*_b_pruned.html` and `*_c_fix.html` are each a single long line.
    It would be easier to read and debug if I had used `BeautifulSoup`'s `prettify()` method to line-break it,
    but this has the unfortunate effect that `<em>` tags appear on their own
    line, which causes an extra space to be incorrectly inserted in certain
    cases. For example, `prettify()` converts the following HTML

    ```html
    <p>"I read <em>The Daily Planet</em>."</p>
    ```

    to

    ```html
    <p>
     "I read
     <em>
      The Daily Planet
     </em>
     ."
    </p>
    ```

    which causes pandoc to produce TeX code with an extra space before the period:

    ```latex
    ``I read \emph{The Daily Planet} .''   % incorrect space before period!
    ```

    To see this, run

    ```bash
    echo '<p>"I read <em>The Daily Planet</em>."</p>' | \
    python3 -c 'import sys, bs4; \
        print(bs4.BeautifulSoup(sys.stdin,"html.parser").prettify())' | \
    pandoc -f html+smart -t latex+smart
    ```

3. We fix a couple typos and correct the hyphenation.
Probably due to shortcomings in the text-editing environment at fanfiction.net,
the author used only hyphens (dashes), rather than en-dashes and em-dashes
(longer dashes). The hyphenation rules are as follows:

    - "pages 10-20" : en-dash (number range)
    - "his well-being" : hyphen (letters)
    - "Uranium U-238" : hyphen (letter & number)
    - "I thought -" : em-dash for all other cases

    The resulting HTML is saved in `i_c_fix.html`.

4. We convert the HTML to TeX using the excellent document-conversion tool `pandoc`.
We use the option `--top-level-division=chapter` to convert `h1` tags to TeX chapters,
and the extensions `html+smart` and `latex+smart` to convert double quotes `"` to TeX's left- and right-sided
double quotes \`\` and `''`. The resulting TeX code is written
to `i_d_pandoc1.tex`. Note that this is not a "standalone" TeX file
because it does not begin with `\documentclass{}` or have any other
preamble that TeX requires. This is added next.

5. We concatenate these chapters (`*_d_pandoc1.tex`) together, prepending a tex
file `header.tex` at the beginning and appending `footer.tex` to the end.
The file `header.tex` contains the TeX preamble that sets the font size,
table of contents, copyright, image attributions, and other front-matter.
This final tex file is written to `mm.tex`.

6. We converts the tex file `mm.tex` to the PDF `mm.pdf` using the `pdflatex` utility.
You need to run `pdflatex` twice: the first run generates the table of
contents file `mm.toc`, which is used by `pdflatex` in the second run to
generate the correct table of contents.


## Other ways to build the PDF

This repo offers a few different ways to create a PDF of _The Metropolitan Man_.

### Option 1: The `doit` build system

This option was described in the Quick Start.
The `doit` build system is like `make`, but simpler and Python-based.
Running `doit` at the command line will cause `doit` to build the PDF of _The Metropolitan Man_ from tasks defined
in `dodo.py`. Running `doit auto` will cause `doit` to continuously watch all the files for changes, and re-build
them as necessary.

The tasks in the task file `dodo.py` rely heavily on Python functions that do the actual downloading and text processing of
_The Metropolitan Man_, which are defined in `lib.py`.

Using `doit` was nice for development of this project, but for folks who don't want to install a whole build-system,
it is easier to simply run `build.py`:

### Option 2: `build.py`

This Python script uses `lib.py` to perform the same steps as `dodo.py`, but it does not save the intermediate files to disk.

### Option 3: `build-simple.py`

This one-page Python script downloads the story and builds the PDF using the same tools as `build.py`, but without using `lib.py`. This makes it nice and readable.
It does not perform the fiddly steps of fixing the typos and hyphenation, so the final PDF `mm.pdf` looks a bit sub-par. Also, it does not save intermediate files.
I wrote this for educational purposes, to highlight the core steps of downloading and building the PDF, without the distracting details.

### Option 4: `old/build.sh`, `old/build-simple.sh` (broken)

These shell scripts were how I started this project. As the project grew, it became easier to maintain by porting them to Python.

They both use a long unix pipeline to download and build the PDF, using `tee` to dump to file various stages of the pipeline, which is kind of cool.

These scripts stopped working sometime between 2019 and 2021, when fanfiction.net implemented some sort of
anti-scraping captcha logic from Cloudflare
(see [here](https://stackoverflow.com/questions/54320269/how-to-fix-please-enable-cookies-cloudflare-error-using-php-curl)),
which breaks the CURL command in these shell scripts.

So these are nice scripts for learning, but they no longer function correctly.

*(Actually, `build.sh` still works, because it uses the cached HTML files `*_a_orig.html` .)*




## Testing

The processing functions in `lib.py` contain assertions that verify the intermediate files (`1_a_orig.html, 1_b_pruned.html`, ...)
look right.

To check the final PDF `mm.pdf`, you should search for these troublesome spots and verify the line-breaks and dashes look ok:

- bringing pistols into
- to explain how I got
- goodness of humanity
- he could actually
- --- that he

If something looks weird in the final PDF `mm.pdf`, a good debugging step is to examine the final TeX file `mm.tex`.
The following command will search for these troublesome spots in the final tex file `mm.tex`. It should look like this:

    $ egrep \
    "bringing pistols into|\
    to explain how I got|\
    goodness of humanity|\
    he could actually|\
    --- that he \
    " mm.tex

    ``Ma'am, if you don't want me bringing pistols into your \\ home\==='' Floyd
    explain\ldots{} to explain how I got to where I am now.'' He took a
    in the goodness of humanity~--- that was the story of Clark's time in
    depths, but those depths weren't nearly so deep that he could actually
    be~--- that he could have~---


## Troubleshooting

To see if you have all the correct programs installed to run `build.py` (except for the `selenium` library),
run this command. The resulting PDF `tmp.pdf` illustrates the various
typesetting pitfalls with hyphenation and smart-quotes. (I.e., if you
leave out the `sed` commands, the hyphenation won't look right, and if
you leave out the `+smart` in the `pandoc` command, the quote marks won't look right.)

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
    | python3 old/prune_html.py                                                      \
    | sed "s/\([0-9]\)-\([0-9]\)/\1\&ndash;\2/g"                                     \
    | sed "s/\([a-zA-Z0-9]\)-\([a-zA-Z0-9]\)/\1\&hyphen;\2/g"                        \
    | sed "s/\(.\)-\(.\)/\1\&mdash;\2/g"                                             \
    | pandoc -f html+smart  -t latex+smart --standalone --top-level-division=chapter \
    | pdflatex -jobname=tmp

![](/images/typesetting-pitfalls.png)

