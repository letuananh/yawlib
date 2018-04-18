YAWlib - Yet Another WordNet library for Python
===============

This library provides interfaces to all major WordNet releases (e.g. Gloss WordNet, Open Multilingual WordNet, WordNetSQL, etc.)

# Data files:

WordNet 3.0 SQLite: https://sourceforge.net/projects/wnsql/files/wnsql3/sqlite/3.0/

WordNet glosstag: http://wordnet.princeton.edu/glosstag.shtml

## Google Drive links

WordNet-3.0-SQLite.zip   : https://drive.google.com/open?id=0Bwko6IfQbRUJMlN1NmdHcWNCWUk

WordNet glosstag         : https://drive.google.com/open?id=0Bwko6IfQbRUJVUlkNEswMldJS2s

# Installation

Yawlib is available on PyPI
```bash
pip install yawlib
# or
python3 -m pip install yawlib

# Download wordnet data and extract them to ~/wordnet

# Show yawlib information
python3 -m yawlib info
```

Search synsets by the lemma `research`, use `python3 -m yawlib lemma research`

```
wn lemma research
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

Note: Extract the glosstag folder and sqlite-30.db to ~/wordnet. The directory should look like this:

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

```

# Development

Go to yawlib folder, execute the config script and then run wntk.sh to generate the glosstab DB file.
```
cd ~/workspace
git clone https://github.com/letuananh/yawlib
cd yawlib
bash config.sh
./wntk.sh -c
```
