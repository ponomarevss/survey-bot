from typing import Any, Dict, List


def compose_text(data: Dict[str, Any]) -> str:
    questions = data['questions']
    current_index = data['current_index']
    answers = data['answers']
    name = data['user_name']
    text = f'Candidate {name}\n\n'
    for i in range(current_index + 1):
        prev_index = i - 1  # index for answer to previous question
        if prev_index in range(len(questions)):
            text += f'your answer: {answers[prev_index]}\n\n'
        question_num = i + 1    # question number to show
        if i in range(len(questions)):
            text += f'{question_num}. {questions[i][0]}\n'
        else:
            text += calculate_result(data)
    return text


def update_answers(callback_str: str, data: Dict[str, Any]) -> List[str]:
    answers = data['answers']
    prev_ind = data['current_index'] - 1
    options = data['questions'][prev_ind][1]
    answers[prev_ind] = convert_callback_to_answer(callback_str, options)
    return answers


def convert_callback_to_answer(callback_str: str, options: List[str]) -> str:
    callback_hash = int(callback_str.split('_')[1])
    for option in options:
        if hash(option) == callback_hash:
            return option


def calculate_result(data: Dict[str, Any]) -> str:
    questions = data['questions']
    answers = data['answers']
    correct = 0
    size = len(answers)
    for i in range(size):
        if questions[i][2] == answers[i]:
            correct += 1
    return f'your result is {correct} out of {size} or {(correct / size) * 100}%'
