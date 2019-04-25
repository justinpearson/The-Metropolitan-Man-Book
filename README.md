# The-Metropolitan-Man-Book
Code to download, typeset, and print "The Metropolitan Man" by Alexander Wales.


# Troubleshooting

Here some error cases. In `build.sh`, replace the `curl` call with this.

    # echo "
    # <p>Start.</p>
    # <p>\"I read <em>The Daily Planet</em> today,\" (Smart quotes ok?) </p>
    # <p>this-or-that (uses hyphens?)</p> 
    # <p>I stole a piece of PU-356 from the lab. (uses hyphen?)</p>    
    # <p>\"But I never thought -\" (uses em-dash?)</p>
    # <p><em>\"Don't touch anyth- \"</em> (uses em-dash within emph tags?)</p>
    # <p>He'd left the naiveté behind him. (correctly interprets unicode accented e?)</p>
    # <p>End.</p>
    # "
