import openai
# AI bot interaction function
def ai_bot_interaction(prompt):
    try:
        print("Before AI API call")
        #prompt += "\nPlease be concise and polite in your response. Inform the user that I work from 8-17. Also be sure to tell him to use the word: schedule , if he wants to schedule an appointment and the word: cancel ,if he wants to delete his appointment.\n"
        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[' Human:', ' AI:']
        )
        print("After AI API call")
        text_response = response.choices[0].text.replace('"','')  # Extracting the text response
        
        return text_response
    except Exception as e:
        print('ERROR:', e)
        return None