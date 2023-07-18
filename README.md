# BCT Experiments

This repo contains a collection of scripts to experiment with NLP understanding of behavioral messages.

Currently working with [BCT Taxonomy v1](https://digitalwellbeing.org/wp-content/uploads/2016/11/BCTTv1_PDF_version.pdf).


## Dataset Generation
A dataset of behavioral messages is generated from a prompt file in `./inputs/` directory.

Currently a prompt file consists of two lines: system prompt and user prompt.

A dataset created from a prompt file `prompt_name.txt` will be saved in `./data/prompt_name/` as a series of `.csv` files named after each of the BCT numbers.

