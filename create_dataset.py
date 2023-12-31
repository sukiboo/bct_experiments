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
from retry.api import retry_call

openai.api_key = os.environ['OPENAI_API_KEY']


class DatasetCreator:

    def __init__(self, prompt_file, num_messages):
        """Read BCT database and prompt, then generate and save the dataset."""
        self.prompt_file = prompt_file
        self.num_messages = num_messages
        self.read_bct_database()
        self.read_prompt()
        self.generate_dataset()
        self.merge_dataset()

    def read_bct_database(self):
        """Read the BCT taxonomy from the spreadsheet."""
        BCT_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS1NRUf8'\
                  'ZMAowUBBqq69awHkuDY1ZQIQord5rbFlhHr8dcJUaQqQImEMJnhuwKtu'\
                  'ASrU_cBtO7Omj9Q/pub?gid=970379036&single=true&output=csv'
        self.bcts = pd.read_csv(BCT_URL, dtype=str)

    def generate_dataset(self):
        """Generate a dataset of messages from a given prompt."""
        os.makedirs(f'./data/{self.prompt_file}/', exist_ok=True)
        print(f'Generating dataset "{self.prompt_file}" with '\
            + f'{self.num_messages} messages for each BCT...\n\n'\
            + f'System prompt: {self.system_prompt}\n\n'\
            + f'User prompt: {self.user_prompt}\n')
        for ind in range(len(self.bcts)):
            # customize prompts and generate messages for the current BCT
            bct_prompts = self.attribute_prompts(ind)
            #TODO: maybe move prompt printing here? so that retries do not reprint it
            #TODO: also remove retry from here
            retry_call(self.generate_bct_messages, fargs=(ind, *bct_prompts), tries=3)

    def read_prompt(self):
        """Read and parse the prompt from a given file."""
        with open(f'./prompts/{self.prompt_file}.txt') as prompt_file:
            try:
                try:
                    content = prompt_file.read()
                except:
                    raise OSError(f'Could not read the "./prompts/{self.prompt_file}.txt" file')
                # check if the prompt file contains the divider
                if '=====' in content:
                    self.system_prompt, self.user_prompt = content.split('\n=====\n')
                # otherwise assume that the prompt consists of two lines
                else:
                    self.system_prompt, self.user_prompt = content.splitlines()
            except:
                raise OSError(f'Could not parse the prompt from "./prompts/{self.prompt_file}.txt"')

    #TODO: verify that there are no unfilled attributes left
    def attribute_prompts(self, ind):
        """Attribute prompts for the current BCT by filling templatized fields."""
        attributes = {'{num_messages}': str(self.num_messages),
                      '{bct_label}': self.bcts.Label[ind],
                      '{bct_definition}': self.bcts.Definition[ind],
                      '{bct_examples}': self.bcts.Examples[ind],
                     }
        # attribute system and user prompts
        system_prompt, user_prompt = self.system_prompt, self.user_prompt
        for attribute, value in attributes.items():
            system_prompt = system_prompt.replace(attribute, value)
            user_prompt = user_prompt.replace(attribute, value)

        return system_prompt, user_prompt

    #TODO: add retry wrapper here
    def generate_bct_messages(self, ind, system_prompt, user_prompt):
        """Generate, format, and save a set of messages for a given BCT."""
        print(f'\n[{ind+1}/{len(self.bcts)}] {self.bcts.No[ind]}. {self.bcts.Label[ind]}'\
            + f'\nSystem prompt: {system_prompt}'\
            + f'\nUser prompt: {user_prompt}')
        content = self.generate_response(system_prompt, user_prompt)
        bct_messages = self.format_response(content)
        pd.DataFrame(bct_messages).to_csv(
            f'./data/{self.prompt_file}/{self.bcts.No[ind]}.csv', header=False, index=False)
        print('Sample messages:', *[f'{i+1}. {bct_messages[i]}' for i in range(5)], sep='\n')

    def generate_response(self, system_prompt, user_prompt,
                          model='gpt-3.5-turbo-0613', temperature=0):
        """Submit user prompt to GPT model and return the response."""
        messages = [{'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}]
        response = openai.ChatCompletion.create(
            messages=messages, model=model, temperature=temperature)

        # check if the generation is successful
        if response.choices[0].finish_reason != 'stop':
            raise ValueError(f'Could not generate messages:\n{response}')
        else:
            return response.choices[0].message.content

    def format_response(self, content):
        """Format the model response as a list of strings."""
        # split on new line symbols
        messages = re.split('\n+', content)
        try:
            # if more lines than required then only keep the ones that start with a number
            if len(messages) > self.num_messages:
                messages = [message for message in messages if message[0].isdigit()]
            # strip message numbering
            messages = [message.lstrip('0123456789. ') for message in messages]
            # check that the number of messages is correct
            if len(messages) != self.num_messages:
                raise ValueError(f'Wrong number of messages generated:\n{messages}')
            else:
                return messages
        except:
            raise ValueError(f'Wrong format for the generated messages:\n{content}')

    def merge_dataset(self):
        """Merge separate message files into a single dataframe."""
        dfs = []
        for bct in self.bcts.No.tolist():
            try:
                # read messages for the current BCT
                df = pd.read_csv(f'./data/{self.prompt_file}/{bct}.csv', names=['message'])
                df['bct'] = bct
                dfs.append(df)
            except FileNotFoundError:
                raise FileNotFoundError(f'The file "./data/{self.prompt_file}/{bct}.csv" is not found')
            except:
                raise OSError(f'Could not read the "./data/{self.prompt_file}/{bct}.csv" file')

        # merge all messages and save the dataframe
        self.df = pd.concat(dfs)
        self.df.reset_index(drop=True, inplace=True)
        self.df.to_csv(f'./data/{self.prompt_file}.csv')
        print(f'\n\nDataset "{self.prompt_file}" is generated'\
            + f' and saved to "./data/{self.prompt_file}.csv"')


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
    prompt_file = args.prompt
    num_messages = int(args.num)

    # generate the dataset
    env = DatasetCreator(prompt_file, num_messages)

