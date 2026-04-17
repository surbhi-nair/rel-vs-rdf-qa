# Comparison of Relational and RDF data model for question answering

> Does the data model matter for structured question answering? We put Text2SQL and Text2SPARQL on equal footing - same data, same questions, two paradigms - to find out.

This repository contains the full benchmark setup, RDF conversion pipeline, evaluation scripts, and results for our comparison of [CHESS](https://github.com/ShayanTalaei/CHESS) (Text2SQL) against [GRASP](https://github.com/ad-freiburg/grasp) (Text2SPARQL) on the [BIRD-SQL Mini-dev](https://github.com/bird-bench/mini_dev) benchmark.

**Read the full write-up:** [Blog post](https://ad-blog.cs.uni-freiburg.de/) *(link to be added once the blog post is published)*

---

## Overview

We take 500 questions from the BIRD-SQL Mini-dev benchmark across 11 databases, convert each database into an RDF knowledge graph, and run two state-of-the-art agents:

| | Agent | Underlying data | Query language |
|---|---|---|---|
| Text2SQL | [CHESS](https://github.com/ShayanTalaei/CHESS) | SQLite databases | SQL |
| Text2SPARQL | [GRASP](https://github.com/ad-freiburg/grasp) | RDF knowledge graphs (QLever) | SPARQL |

**Key results:**

| Metric | CHESS (SQL) | GRASP (SPARQL) |
|---|---|---|
| Strict F1 | **65.33%** | 21.25% |
| Relaxed F1 | **71.90%** | 47.69% |
| LLM accuracy judge | **~66%** | ~51% |
| LLM preference judge | 31.4% | **64%** |
| Cost per 500 questions | ~$40 | **~$5** |

---

## Setup

### Prerequisites

- Python 3.12+
- [QLever](https://github.com/ad-freiburg/qlever) for serving RDF knowledge graphs
- [morph-kgc](https://morph-kgc.readthedocs.io/en/stable/) for RDF conversion
- Access to an OpenAI API key (GPT-5-mini used for both agents and evaluation)
- Download the BIRD-SQL Mini-dev dataset and place it in `data/BIRD/minidev/` (see documentation [here](https://github.com/bird-bench/mini_dev?tab=readme-ov-file#for-new-users))

### CHESS Setup

CHESS is included as a modified fork under `CHESS/`. See [`CHESS/README.md`](./CHESS/README.md) for its specific setup instructions.

### GRASP Setup

GRASP is used as-is. See the [GRASP repository](https://github.com/ad-freiburg/grasp) for installation and configuration. Each converted knowledge graph needs to be served via a dedicated QLever endpoint before running GRASP.

---

## Reproducing the RDF Conversion

Each of the 11 BIRD Mini-dev SQLite databases was converted to RDF using [morph-kgc](https://morph-kgc.readthedocs.io/en/stable/) and an RML mapping file per database. The conversion process can be reproduced by running the following command for the given database by modifying the [configuration file](./experiments/bird_minidev_basic/morphkgc_config.ini) accordingly:

```bash
python3 -m morph_kgc experiments/bird_minidev_basic/morphkgc_config.ini
```

---
## Repository Structure

```
.
├── CHESS/                        # Forked and modified CHESS agent (Text2SQL)
│   └── ...                       # See CHESS/README.md for setup
│
├── experiments/                  # Experiment runs: results, logs, outputs
│   └── bird_minidev/             # Main experiment on BIRD Mini-dev
│       └── ...                   # Results for SQL, SPARQL, and evaluation
│
├── src/                          # Python scripts for evaluation and analysis
│   └── ...
│
└── README.md
```

A detailed description of the folder and file structure is available in [`structure.md`](./STRUCTURE.md).

---
