import json
import os
import openai
import random
import time
from datetime import datetime
import argparse
from tqdm import tqdm
from typing import Union
from prompts import math_prompt
from collections import OrderedDict, Counter
from tool import *
split_symbol = "XXXXX"

def simple_user_assistant_split(prompt: str):
    messages = []
    system_message = prompt.split('\n')[0]
    messages.append({"role": "system", "content": system_message})

    first_user_message = prompt[prompt.find("Let"):prompt.find("Now")] + "Now it's your turn. Here is another math problem:\n\n" + prompt.split(split_symbol)[1]
    first_user_message = first_user_message.replace(split_symbol, '')
    first_assistant_message = prompt.split(split_symbol)[6].strip()
    messages += [
        {"role": "user", "content": f"{first_user_message}"},
        {"role": "assistant", "content": f"{first_assistant_message}"},
    ]

    user_messages = []
    assistant_messages = []
    spliced = prompt.split(split_symbol)
    for i in range(5, len(spliced)-1):
        if i % 2 == 1:
            assistant_messages += [spliced[i].replace("\' ", '').replace(" \'", '').strip()]
        else:
            user_messages += [spliced[i]]

    for i in range(len(user_messages) - 2):
        messages += [
            {"role": "user", "content": f"{user_messages[i]}"},
            {"role": "assistant", "content": f"{assistant_messages[i]}"},
        ]
    messages += [
        {"role": "user", "content": f"{spliced[- 1]}"},
    ]

    return messages


def query_cot(data: dict, key: str, cot_temperature: float, sc_num: float, backbone: str, memory):
    '''
    This function is used to query OpenAI for CoT solutions.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        cot_temperature: the temperature used in CoT
        backbone: ChatGPT or GPT-4

    Returns:
        completions: a list containing the CoT solution
    '''
    query_message = simple_user_assistant_split(data['prompt'])

    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'

    start_time = time.time()
    completions = []
    while True:
        try:
            cot_solution = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=300,
                stop='\n\n\n',
                messages=query_message,
                temperature=cot_temperature,
                top_p=1.0,
                n=sc_num)
        except Exception as e:
            print(e)
            cot_solution = None

        if cot_solution is not None:
            completions.extend([choice['message']['content']
                                for choice in cot_solution['choices']])
            return completions
        else:
            sleep_time = 1
            time.sleep(sleep_time)

        if time.time() - start_time > 60:
            return None


def query_pal(data: dict, key: str, pal_temperature: float, backbone: str, memory):
    '''
    This function is used to query OpenAI for PAL solutions.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        pal_temperature: the temperature used in PAL
        backbone: ChatGPT or GPT-4

    Returns:
        completions: a list containing the PAL solution
    '''
    query_message = simple_user_assistant_split(data['pal_prompt'])
    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'
    start_time = time.time()
    completions = []
    while True:
        try:
            pal_solution = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=300,
                stop='\n\n\n',
                messages=query_message,
                temperature=pal_temperature,
                top_p=1.0,
                n=1)
        except Exception as e:
            pal_solution = None

        if pal_solution is not None:
            completions.extend([choice['message']['content']
                                for choice in pal_solution['choices']])
            return completions
        else:
            sleep_time = 1
            time.sleep(sleep_time)

        if time.time() - start_time > 60:
            return None


def query_cot2pal(data: dict, key: str, backbone: str, cot_answer: str):
    '''
    This function is used to query OpenAI for CoT-->PAL conversion.
    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        backbone: ChatGPT or GPT-4

    Returns:
        completions: a list containing the PAL solution
    '''
    query_message = get_cot2pal_prompt(data, cot_answer=cot_answer)
    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'

    start_time = time.time()
    completions = []
    while True:
        try:
            pal_solution = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=500,
                stop='\n\n\n',
                messages=query_message,
                temperature=0.2,
                top_p=0.95,
                n=1)
        except Exception as e:
            pal_solution = None

        if pal_solution is not None:
            completions.extend([choice['message']['content']
                                for choice in pal_solution['choices']])
            completions = completions[:1]
            return completions
        else:
            sleep_time = 1
            time.sleep(sleep_time)

        if time.time() - start_time > 60:
            return None


def query_validator(data, key, backbone, proposal):
    '''
    This function is used to query OpenAI for validating COT/PAL solutions.
    '''
    query_message = get_val_prompt(data, proposal=proposal)
    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'

    start_time = time.time()
    completions = []
    while True:
        try:
            validator_opinion = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=500,
                stop='\n\n\n',
                messages=query_message,
                temperature=0.8,
                top_p=0.95,
                n=5)
        except Exception as e:
            print(e)
            validator_opinion = None

        if validator_opinion is not None:
            completions.extend([choice['message']['content']
                                for choice in validator_opinion['choices']])
            # completions = completions[:1]
            return completions
        else:
            sleep_time = 1
            time.sleep(sleep_time)

        if time.time() - start_time > 60:
            return None


def query_dialogue(data: dict,
                   key: str,
                   backbone: str,
                   sc_num=1,
                   use_validators=False,
                   memory=[(None, None)]):
    cot_answers = []
    cot_solutions = []
    cot_solution = query_cot(data=data,
                             key=key,
                             cot_temperature=cot_temperature,
                             sc_num=sc_num,
                             backbone=backbone,
                             memory=memory)
    if cot_solution is None:
        print('Time out')
        return None
    else:
        for i in range(len(cot_solution)):
            cot_ans = extract_geom(cot_solution[i])
            if cot_ans != '':
                cot_answers.append(cot_ans)
                cot_solutions.append(cot_solution[i])

    if len(cot_answers) > 0:
        count = Counter(cot_answers)
        majority_ans = count.most_common(1)[0][0]
    else:
        return ''
    final_solution = None
    for a, s in zip(cot_answers, cot_solutions):
        if a == majority_ans:
            final_solution = s
            break
    # if use_validators:
    #     was_it_correct = []
    #     corrected_answers = []
    #     corrected_solutions = []
    #     cot_validation = query_validator(data=data,
    #                                      key=key,
    #                                      backbone=backbone,
    #                                      proposal=final_solution)
    #     if cot_validation is None:
    #         print('Time out')
    #         return None
    #     else:
    #         for i in range(len(cot_validation)):
    #             vcorrectness, vsolution, vanswer = extract_validity_turbo(cot_validation[i])
    #             was_it_correct.append(vcorrectness)
    #             corrected_answers.append(vanswer)
    #             corrected_solutions.append(vsolution)
    #
    #     count = Counter(corrected_solutions)
    #     cot_validation = count.most_common(1)[0][0]
    #     # Run Agreement
    #     # cot_agreement = query_agreement(data=data, key=key, mode='cot', backbone=backbone, proposal=cot_result,
    #     #                                 correction=cot_validation)
    # else:
    #     cot_validation = final_solution
    # # Run COT --> PAL
    # cot2pal_result = query_cot2pal(data=data,
    #                                key=key,
    #                                backbone=backbone,
    #                                cot_answer=cot_validation)
    # use_validators = False
    # if use_validators:
    #     was_it_correct = []
    #     corrected_answers = []
    #     corrected_solutions = []
    #     pal_validation = query_validator(data=data, key=key, backbone=backbone, proposal=cot2pal_result)
    #     if pal_validation is None:
    #         print('Time out')
    #         return None
    #     else:
    #         for i in range(len(pal_validation)):
    #             vcorrectness, vsolution, vanswer = extract_validity_turbo(pal_validation[i])
    #             was_it_correct.append(vcorrectness)
    #             corrected_answers.append(vanswer)
    #             corrected_solutions.append(vsolution)
    #
    #     count = Counter(corrected_solutions)
    #     pal_validation = count.most_common(1)[0][0]
    #     # Run Agreement
    #     # pal_agreement = query_agreement(data=data, key=key, mode='pal', backbone=backbone, proposal=cot2pal_result,
    #     #                                 correction=pal_validation)
    # else:
    #     pal_validation = cot2pal_result
    return majority_ans


def query_agents_memory(data: dict,
                        key: str,
                        sc_num: int,
                        backbone: str,
                        memory=[(None, None)],
                        use_validators=False
                        ):
    '''
    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        cot_temperature: the temperature used in CoT. 0 for greedy decoding. We set it to 0.5 for self-consistency samples.
        pal_temperature: the temperature used in PAL. 0 for greedy decoding. We set it to 0.8 for self-consistency samples.
        sc_num: the number of self-consistency samples
        backbone: ChatGPT or GPT-4
        memory: The memory
    '''
    agent_solution = query_dialogue(data=data,
                                    key=key,
                                    backbone=backbone,
                                    sc_num=sc_num,
                                    use_validators=use_validators,
                                    memory=memory)
    if agent_solution is None:
        print('Time out')
        return None
    ####################
    # === dump data ===
    to_dump_data = OrderedDict(
        {'index': data['index'], 'question': data['question'], 'answer': data['answer'],
         'majority_ans': agent_solution, 'final_answers': None,
         'cot_executed': None, 'pal_executed': None,
         'cot_generated': None, 'pal_generated': None, 'choice_solution': None}
    )

    return to_dump_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=400)
    parser.add_argument('--run_only', type=str, default=None)
    parser.add_argument('--dataset', type=str, choices=[
        'geometry'], default='geometry')
    parser.add_argument('--backbone', type=str,
                        choices=['chatgpt', 'gpt4'], default='chatgpt')
    parser.add_argument('--cot_temperature', type=float, default=0.5)
    parser.add_argument('--pal_temperature', type=float, default=0.8)
    parser.add_argument('--sc_num', type=int, default=5,
                        help='Self-consistency samples. 1 indicates greedy decoding')
    parser.add_argument('--output_dir', type=str, default='../output/')
    # TODO: REMOVE
    parser.add_argument(
        '--key', type=str, default='', required=False)

    args = parser.parse_args()

    start_index = args.start
    end_index = args.end
    dataset_name = args.dataset
    cot_temperature = args.cot_temperature
    pal_temperature = args.pal_temperature
    backbone = args.backbone
    run_only = args.run_only
    sc_num = args.sc_num
    output_dir = args.output_dir
    key = args.key

    start_time_0 = time.time()
    print('Current time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))

    dt_string = datetime.now().strftime("%m_%d_%H_%M")

    if dataset_name == 'geometry':
        dataset = jsonfolder_load('../dataset/test_geometry')
    else:
        raise ValueError('Only for use with Geometry / MATH split!')

    # === slice data based on start and end === #
    if run_only is None:
        total_num = len(dataset)
        print('total data: ', total_num)
        if end_index == -1:
            end_index = total_num

        if end_index > total_num:
            end_index = total_num

        tasks = dataset[start_index:end_index]
        task_num = len(tasks)
        total_num = task_num
        print('Current total tasks: ', task_num)
        run_only_list = [f for f in range(start_index, end_index)]
    else:
        with open(run_only, 'r') as fin:
            run_only_list = fin.read().strip()
            run_only_list = [int(i) for i in run_only_list.split(',')]
        total_num = len(run_only_list)
        print('total data: ', total_num)
        start_index = 0
        end_index = len(dataset)
        task_num = len(dataset)
        tasks = dataset[start_index:end_index]

    unfinished_tasks = []

    output_path = os.path.join(output_dir, f'{backbone}/')

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    save_path = os.path.join(output_path,
                             f'{dataset_name}_sc{sc_num}_s{start_index}_e{end_index}_{dt_string}.jsonl')

    # === run experiments ===
    progress_bar = tqdm(range(total_num))
    memory = [(None, None)]
    for i in range(len(dataset)):
        if i not in run_only_list:
            continue
        task = tasks[i]
        wait_time = min(sc_num * 300, 2000)
        start_time = time.time()
        while True:
            #try:
            ans, new_memory_entry = query_agents_memory(task,
                                                        key=key,
                                                        sc_num=sc_num,
                                                        backbone=backbone,
                                                        memory=memory,
                                                        use_validators=True)
                #memory.append(new_memory_entry)
            #except Exception as e:
                #ans = None

            if ans is not None:
                with open(save_path, "a+") as fout:
                    fout.write(json.dumps(ans) + '\n')
                progress_bar.update(1)
                break
            else:
                sleep_time = 1
                time.sleep(sleep_time)

            if time.time() - start_time > wait_time:
                print('Time out')
                print('Current Task: ', i)
                unfinished_tasks.append(task)
                break

        sleep_time = 1
        time.sleep(sleep_time)

    end_time_0 = time.time()
    print('Finish at time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))
    print(f'Time used: {end_time_0 - start_time_0} seconds')
    if len(unfinished_tasks) > 0:
        print('Unfinished tasks: ')
        for task in unfinished_tasks:
            print(task)

    print('Done')