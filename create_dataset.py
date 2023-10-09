"""
Create a dataset consisting of healthcare messages for behavioral change.
Messages are generated by gpt-3.5-turbo-0613 model from the templatized prompt.

BCT labels/definitions/examples are taken from the BCT Taxonomy v1 available at
https://digitalwellbeing.org/wp-content/uploads/2016/11/BCTTv1_PDF_version.pdf

Processed table with corrected grammar and extra info is available at
https://docs.google.com/spreadsheets/d/1a4Ntiwa1DLkpfAGDDrKvyyB4QA4xkKhQpD9kKx-DRck
"""

import os
import re
import openai
import argparse
import pandas as pd

openai.api_key = os.environ['OPENAI_API_KEY']


def generate_response(system_prompt,
                      user_prompt,
                      model='gpt-3.5-turbo-0613',
                      temperature=0,
                      **kwargs):
    """Submit user prompt to GPT model and return the response."""
    messages = [{'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}]
    response = openai.ChatCompletion.create(messages=messages,
                                            model=model,
                                            temperature=temperature,
                                            **kwargs)
    return response

def format_response(content):
    """Format the model response as a list of strings."""
    # split on new line symbols
    messages = re.split('\n+', content)
    # only keep lines that start with a number
    messages = [message for message in messages if message[0].isdigit()]
    # strip message numbering
    messages = [message.lstrip('0123456789. ') for message in messages]
    return messages

def generate_dataset(prompts, num_messages):
    """Generate a dataset of messages from a given prompt."""
    # read the prompt
    with open(f'./prompts/{prompts}.txt') as prompt:
        system_prompt, user_prompt = prompt.read().splitlines()
    print(f'System prompt: {system_prompt}\n\nUser prompt: {user_prompt}\n')

    # read the BCT taxonomy
    BCT_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1NRUf8'\
              'ZMAowUBBqq69awHkuDY1ZQIQord5rbFlhHr8dcJUaQqQImEMJnhuwKtu'\
              'ASrU_cBtO7Omj9Q/pub?gid=970379036&single=true&output=csv'
    bcts = pd.read_csv(BCT_URL, dtype=str)

    # generate the dataset
    print(f'Generating dataset "{prompts}" with {num_messages} messages for each BCT...\n')
    os.makedirs(f'./data/{prompts}/', exist_ok=True)
    for ind in range(28, len(bcts)):

        # customize prompt for the current BCT
        bct_no = bcts.No[ind]
        bct_prompt = user_prompt.replace('{bct_label}', bcts.Label[ind])\
                                .replace('{bct_definition}', bcts.Definition[ind])\
                                .replace('{num_messages}', str(num_messages))

        # generate messages for the current BCT
        generate_bct_messages(bct_no, bct_prompt, system_prompt)

    print(f'\n\nDataset "{prompts}" is generated and saved to "./data/{prompts}/"')

def generate_bct_messages(bct_no, bct_prompt, system_prompt):
    """Generate a set of messages for a given BCT."""
    # generate and save messages
    print(f'\n[{bct_no}] {bct_prompt}')
    response = generate_response(system_prompt, bct_prompt)

    # interrupt if the generation did not run as expected
    if response.choices[0].finish_reason != 'stop':
        raise ValueError(f'\nCould not generate messages for BCT {bct_no}:\n{response}')
    else:
        # check if the length/format of the messages is correct
        bct_messages = format_response(response.choices[0].message.content)
        if len(bct_messages) != num_messages:
            raise ValueError(f'\nWrong format for BCT {bct_no} messages:\n{bct_messages}')
        else:
            # save generated messages and display the first 5
            bct_df = pd.DataFrame(bct_messages)
            bct_df.to_csv(f'./data/{prompts}/{bct_no}.csv', header=False, index=False)
            print(*[f'{i+1}. {m}' for i, m in enumerate(bct_messages[:5])], sep='\n')


if __name__ == '__main__':

    # parse the configs
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prompt',
                        default='baseline',
                        help='name of the prompt file in "./prompts/"')
    parser.add_argument('-n', '--num',
                        default=10,
                        help='number of messages to generate for each BCT')

    # read the inputs
    args = parser.parse_args()
    prompts = args.prompt
    num_messages = int(args.num)

    # generate the dataset
    generate_dataset(prompts, num_messages)

