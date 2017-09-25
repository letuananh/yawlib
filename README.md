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

Extract the glosstag folder and sqlite-30.db to ~/wordnet. The directory should look like this:
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
Go to yawlib folder, execute the config script and then run wntk.sh to generate the glosstab DB file.
```
cd ~/workspace
git clone https://github.com/letuananh/yawlib
cd yawlib
bash config.sh
./wntk.sh -c
```
