# SPEC.md

## Behavior description
This is step by step what the app does from the user's perspective:
- The app greets the user in a welcome screen  
- On the welcome screen, the user gets a choice to login, create an account or quit  
- Then there is an authentication flow for if the user is trying to login using a username and password or create an account. If the user quits, bring them back to the main welcome screen without them being logged in  
- Now users go to a main menu without the login screen, where they are asked to select quiz settings like number of questions they want and the difficulty level  
- The user then selects the options they want for the questions in settings  
- After the question types are chosen, the questions that fit the options are shown to the user  
- After the questions are chosen, the user answers the question  
- The answers are checked as each question is answered and the correct and incorrect options are shown  
- After each question, feedback is asked by the question whether to like or dislike the question  
- A final score is displayed at the end of the quiz in the form of a final score summary  
- The stats are recorded  
- Then the user can return to main menu to try again or exit the app  

## File structure 
- This SPEC.md file with project details 
- A file for the main programming logic
- A score history file that tracks performance and other useful statistics over time for each user. This file should not be human-readable and should be relatively secure. (This means someone could look at the file and perhaps find out usernames but not passwords or scores.)
- A JSON with the quiz questions

## Error handling 
- If JSON file is missing, print an error message and exit
- If user enters an invalid input, prompt again and ask them to give a valid input
- If a username already exist, prompt again and ask user to choose a different username

## Required Features
- A local login system that prompts users for a username and password (or allows them to enter a new username and password). The passwords should not be easily discoverable.
- A score history file that tracks performance and other useful statistics over time for each user. This file should not be human-readable and should be relatively secure. (This means someone could look at the file and perhaps find out usernames but not passwords or scores.)
- Users should be able to provide feedback on whether they like a question or not, and this should inform what questions they get next by allowing them to like or dislike the question. 
- The questions should exist in their own human-readable .json file so that they can be easily modified. (This lets you use the project for studying other subjects if you wish; all you have to do is generate the question bank.)
- Should allow users to choose difficulty levels of questions that affect scoring. Easy questions get +1 points, medium questions get +2 points and difficult questions get +3 points.

## Acceptance Criteria
- The app runs successfully without any crashes and bugs using .py
- Users can successfully login or create a new account 
- The app should load questions from the JSON file
- The score history file should track performance and stats of users but should be relatively secure and not human-readable
- The difficulty level chosen should determine which questions are asked to the user
- The errors are handled without the app crashing


## Data format

```json
{
  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics",
      "difficulty": "easy"
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures",
      "difficulty": "difficult"
    },
    {
      "question": "What built-in function returns the number of items in a list?",
      "type": "short_answer",
      "answer": "len",
      "category": "Python Basics",
      "difficulty": "medium"
    },
    {
      "question": "Which of these is not a core Python data type?",
      "type": "multiple_choice",
      "options": ["lists", "dictionary", "tuples", "class"],
      "answer": "class",
      "category": "Data Structures",
      "difficulty": "medium"
    },
    {
      "question": "What is a class in Object Oriented Programming?",
      "type": "multiple_choice",
      "options": ["function", "module", "code block", "blueprint for creating objects"],
      "answer": "blueprint for creating objects",
      "category": "Python Basics",
      "difficulty": "difficult"
    }
  ]
}

