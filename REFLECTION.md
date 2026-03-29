# Reflection on AI's Review

## How far did the agent get? Did it fully implement your spec? What percentage of your acceptance criteria passed on the first try?

This was my acceptance criteria:
- The app runs successfully without any crashes and bugs using .py
- Users can successfully login or create a new account 
- The app should load questions from the JSON file
- The score history file should track performance and stats of users but should be relatively secure and not human-readable
- The difficulty level chosen should determine which questions are asked to the user
- The errors are handled without the app crashing

The agent got pretty far since acceptance criteria 1, 2 and 5 are fully met. 3 was barely met since the JSON file was not loaded correctly creating the biggest problems and leading to the app not working properly. 4 mostly worked except it failed to decrypt, which meant it could erase existing data for a user. 6 was hindered because of the JSON file bugging. Although sheerly by percentage, it fully passed only 50% of the acceptance criteria. 


## Where did you intervene? List each time you had to step in during Phase 2. Why was the intervention needed? Could a better spec have prevented it?

The agent failed to properly create or locate questions.json soI corrected the file name/location and ensured the JSON format was valid. A better spec possibly would not have prevented it since I was pretty specific about the requirements for the JSON file in the File Structure.


## How useful was the AI review? Did it catch real bugs? Did it miss anything important? Did it flag things that weren't actually problems?

I believe that it caught all real bugs and didn’t miss anything important that I didn’t catch. However, I think it underplayed the severity of the JSON file being incorrectly formatted since that led to the whole app not working. It flags some issues that weren’t real problems like point 17 in the REVIEW.md. 


## Spec quality → output quality: In hindsight, what would you change about your spec to get a better result from the agent?

I think I would make the logical flow in the behavior description much more specific. I would also add more detail about the JSON and the importance of the app to function without any bugs which would allow it to pass the 3 and 6 acceptance criteria. I would also add an acceptance criteria that ensured secure score storage and the importance of data integrity. 


## When would you use this workflow? Based on this experience, when do you think plan-delegate-review is better than conversational back-and-forth? When is it worse?
I think plan-delegate-review is better when the tasks are well-structured and not vague so that responses are faster, more efficient and more objective since output can be evaluated against a set criteria. This would perhaps also help catch bugs more methodologically. This approach is probably more unfavourable than conversational back-and-forth when the app you are creating is more creative and adaptable, wherein your constant personal and designer input is helpful instead of a straightforward prompt. Often with more exploratory tasks, it’s better to keep iterating based on what looks the best in terms of UIUX and what is the most personalised and authentic.
