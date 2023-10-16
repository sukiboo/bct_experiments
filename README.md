# BCT Experiments

This repo contains a collection of scripts to experiment with NLP understanding of behavioral messages.

Currently working with [BCT Taxonomy v1](https://digitalwellbeing.org/wp-content/uploads/2016/11/BCTTv1_PDF_version.pdf).


## Dataset Generation
A dataset of behavioral messages is generated from a prompt file in `./prompts/` directory.\
A prompt file either
- consists of two lines: system prompt and user prompt
- or contain `=====` line, in which case everything above this line is the system prompt and everything below is the user prompt

Use a prompt file `prompt_name.txt` to generate a dataset with `num` messages per BCT via the command
```
python -m create_dataset -p prompt_name -n num
```
The default values for the arguments are `prompt_name=baseline` and `num=10`.
A created dataset will be saved in `./data/prompt_name/` as a series of `.csv` files named after each of the BCT numbers.

