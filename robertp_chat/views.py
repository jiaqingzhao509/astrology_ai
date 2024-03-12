from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from openai import OpenAI
from . import prompts,charts
import requests
import datetime
import anthropic


#open ai

# openai_api_key = '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'
# client = OpenAI(
#     # This is the default and can be omitted
#     api_key=openai_api_key,
# )

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="",
)



# Create your views here.

def get_timezone(lat, lng):
    api_key = 'YOUR_OPEN_CAGE_API_KEY'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={lat}+{lng}&key=1e660713cb444c40ae916eaa55feaf58'
    response = requests.get(url)
    data = response.json()

    # Assuming the request is successful and data is returned
    if data['results']:
        # Extract timezone information from the first result
        timezone = data['results'][0]['annotations']['timezone']['name']
        return timezone
    else:
        return "Timezone information not available."

@csrf_exempt
def start_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        city = data.get('city')
        birth_date = data.get('date')
        birth_time = data.get('time')
        lat = data.get('lat')
        lng = data.get('lng')
        tz = get_timezone(lat,lng)
        
        while True:
            try:
                #natal houses
                natal_info, natal_ascmc = charts.astro_charts(charts.to_jd_ut(birth_date, birth_time, tz), lat, lng)
                #yearly info
                solar_return, years_dict = charts.get_yearly_info(datetime.date.today().year, tz, lat, lng, natal_info, birth_date, birth_time)
                break
            except:
                return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
                
        response_data = "The following info are always in the order of Planet:[house number, sign, degree]. The natal chart is " + str(natal_info) + ". The natal asc is " + str(natal_ascmc) + ". The yearly info follows: " + str(years_dict) + ". Once you see those reply 'ok'"
        request.session['system_context'] = prompts.initializing_prompt + prompts.response_requirements + response_data
        #request.session['system_context'] = {"role": "system", "content": prompts.initializing_prompt + prompts.response_requirements + response_data} # + prompts.response_requirements
        return JsonResponse({'status': 'success', 'data': response_data})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# def ask_openai(message, message_history, system_context=None):
#     messages_payload = message_history.copy()
#     if system_context:
#         # Prepend system context to the message history for the initial call
#         messages_payload = [system_context] + messages_payload


#     messages_payload.append({"role": "user", "content": message})
#     print(messages_payload)
#     response = client.chat.completions.create(
#         messages=messages_payload,
#         model='gpt-3.5-turbo-0125',
#         n=1,
#         temperature=0.7,
#         max_tokens = 256
#     )
    
#     answer = response.choices[0].message.content.strip()
#     return answer

def ask_claude(message, message_history, system_context):
    # if message_history == []: 
    #     system_content = system_context
    # else:
    #     system_context = ''

    messages_payload = message_history.copy()
    messages_payload.append({"role": "user", "content": message})
    #print(messages_payload)
    response = client.messages.create(
    model="claude-3-sonnet-20240229",
    system= system_context,
    max_tokens=512,
    messages=messages_payload
    )
    print(response.content[0].text)
    answer = response.content[0].text.strip()
    return answer


def chatbot(request):
    if request.method == 'POST':
        message = request.POST.get('message')

        # Check if we need to initialize the conversation
        if 'conversation_history' not in request.session:
            # # Define your initial system context here
            # system_context = {"role": "system", "content": prompts.initializing_prompt + prompts.response_requirements}

            # # Store the initial system context in the session
            # request.session['system_context'] = system_context
            system_context = request.session.get('system_context')
            conversation_history = []
        else:
            # Retrieve the conversation history and system context from the session
            conversation_history = request.session.get('conversation_history', [])
            system_context = request.session.get('system_context')

        # Call OpenAI with the current message, history, and system context (only for the first message)
        # system_context if not conversation_history else None
        #response = ask_openai(message, conversation_history, system_context)
        response = ask_claude(message, conversation_history, system_context)

        # Update and store the conversation history in the session, excluding the system context after the first use
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response})
        request.session['conversation_history'] = conversation_history

        return JsonResponse({'message': message, 'response': response})

    # If not a POST request, clear the session or do nothing
    request.session.pop('conversation_history', None)
    request.session.pop('system_context', None)
    return render(request, 'chatbot.html')



# def ask_openai(message):
#     response = client.chat.completions.create(
#             messages=[
#         {
#             "role": "user",
#             "content":message,
#         }
#     ],
#         model = 'gpt-3.5-turbo-0125',
#         #prompt = message,
#         #max_token = 150,
#         n=1,
#         stop=None,
#         temperature=0.6,
#     )

#     answer= response.choices[0].message.content.strip()
#     return answer

# def chatbot (request):
#     if request.method == 'POST':
#         message = request.POST.get('message')
#         response = ask_openai(message)
#         return JsonResponse({'message':message, 'response':response})

#     return render(request, 'chatbot.html')
