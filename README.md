YAWlib - Yet Another WordNet library for Python
===============

A Python library for accessing major WordNet releases using relational databases for high performance batch processing.

Supporting Wordnets:

- Princeton Wordnet 3.0
- NTU Open Multilingual WordNet
- Gloss WordNet

# Installation

Yawlib is available on [PyPI](https://pypi.org/project/yawlib/)

```bash
pip install yawlib
```

Download prebuilt database files are available on the author's [Open Science Framework project page: https://osf.io/9udjk/](https://osf.io/9udjk/) and extract them to your home folder at `~/wordnet/`.
On Linux it should look something like

```
/home/username/wordnet/
    - glosstag.db
    - sqlite-30.db
    - wn-ntumc.db

# or on Mac OS
/Users/username/wordnet/
    - glosstag.db
    - sqlite-30.db
    - wn-ntumc.db
```

On Windows

```
C:\Users\<username>\wordnet\
    - glosstag.db
    - sqlite-30.db
    - wn-ntumc.db
```

To verify that yawlib is working properly, you can use the `info` command.

```bash
# Show yawlib information
python3 -m yawlib info
```

# Command-line tools

`yawlib` includes a command-line tool for querying wordnets directly from terminal.

For example, to search synsets by the lemma `research` one may use `python3 -m yawlib lemma research`

```
python3 -m yawlib lemma research

Looking for synsets by term (Provided: research | pos = None)

〔Synset〕00636921-n 〔Lemmas〕research 〔Keys〕research%1:04:00::
------------------------------------------------------------
(def) “systematic investigation to establish facts;”


〔Synset〕05797597-n 〔Lemmas〕inquiry; enquiry; research 〔Keys〕inquiry%1:09:01:: enquiry%1:09:00:: research%1:09:00::
------------------------------------------------------------
(def) “a search for knowledge;”
(ex) their pottery deserves more research than it has received;


〔Synset〕00648224-v 〔Lemmas〕research; search; explore 〔Keys〕research%2:31:00:: search%2:31:00:: explore%2:31:00::
------------------------------------------------------------
(def) “inquire into;”
(ex) the students had to research the history of the Second World War for their history project;
(ex) He searched for information on his relatives on the web;
(ex) Scientists are exploring the nature of consciousness;


〔Synset〕00877327-v 〔Lemmas〕research 〔Keys〕research%2:32:00::
------------------------------------------------------------
(def) “attempt to find out in a systematically and scientific manner;”
(ex) The student researched the history of that word;

Found 4 synset(s)
```

# Development

Go to yawlib folder, execute the config script and then run wntk.sh to generate the glosstab DB file.
```
git clone https://github.com/letuananh/yawlib
cd yawlib

# create virtual environment
python3 -m venv yawlib_py3
. yawlib_py3/bin/activate

# install required packages
pip install -r requirements.txt
pip install -r requirements-optional.txt

# to show information
python -m yawlib info
```

## Compiling glosstag.db from source

Make sure that `glosstag` source folder and `sqlite-30.db` are available in `~/wordnet`.
The directory should look like this:

```
/home/user/wordnet
├── glosstag
│   ├── dtd
│   │   └── glosstag.dtd
│   ├── LICENSE.txt
│   ├── merged
│   │   ├── adj.xml
│   │   ├── adv.xml
│   │   ├── noun.xml
│   │   └── verb.xml
│   ├── README.txt
│   ├── standoff
│   │   ├── 00
│   │   ├── 01
│   │   ├── 02
│   │   ├── ....
│   │   ├── index.byid.tab
│   │   ├── index.bylem.adj.tab
│   │   ├── index.bylem.adv.tab
│   │   ├── index.bylem.noun.tab
│   │   ├── index.bylem.tab
│   │   ├── index.bylem.verb.tab
│   │   └── index.bysk.tab
│   └── statistics.tab
├── glosstag.db
├── sqlite-30.db
├── wn-ntumc.db
```

The run the `create` command to generate the database

```bash
python -m yawlib create
```

# Original sources

- WordNet 3.0 SQLite: https://sourceforge.net/projects/wnsql/files/wnsql3/sqlite/3.0/
- WordNet glosstag (XML): http://wordnet.princeton.edu/glosstag.shtml
- NTU Open Multilingual Wordnet: http://compling.hss.ntu.edu.sg/omw/
