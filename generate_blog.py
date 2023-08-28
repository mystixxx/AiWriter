import os
import random
import requests
import base64
import openai
import spacy
import openpyxl

from time import time, sleep
from pprint import pprint

nlp = spacy.load("en_core_web_sm")

ACCESS_KEY = ''
url = ""
user = ""
password = ""

credentials = user + ':' + password

token = base64.b64encode(credentials.encode())

header = {'Authorization': 'Basic ' + token.decode('utf-8')}

media_header = {
    'Content-Type': 'image/jpeg',
    'Authorization': 'Basic ' + token.decode('utf-8')
}

def search_unsplash(search_term):
    # Generate a random number between 2 and 4
    random_page = random.randint(2, 4)
    # Construct the API URL
    api_url = 'https://api.unsplash.com/search/photos?query={}&page={}&orientation=landscape&client_id={}'.format(search_term, random_page, ACCESS_KEY)

    response = requests.get(api_url)
    # Check the status code of the response
    if response.status_code == 200:
        # If the request is successful, return the list of images
        return response.json()['results']
    else:
        # If the request is unsuccessful, return an empty list
        return []


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def get_request_from_file(filepath):
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    for row in sheet.rows:
        yield row[0].value

def get_last_word(line):
    words = line.split()
    if len(words) > 0:
        return words[-1]
    else:
        return ""

openai.api_key = open_file('openaiapikey.txt')


def gpt3_completion(prompt, engine='text-davinci-003', temp=0.7, top_p=1.0, tokens=50, freq_pen=0.0, pres_pen=0.0, stop=['asdfasdf', 'asdasdf']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()  # force it to fix any unicode errors
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            #text = re.sub('\s+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def improve_outline(request, outline):
    prompt = open_file('prompt_improve_outline.txt').replace('<<REQUEST>>',request).replace('<<OUTLINE>>', outline)
    outline = '1. ' + gpt3_completion(prompt)
    return outline


def neural_recall(request, section):
    prompt = open_file('prompt_section_research.txt').replace('<<REQUEST>>',request).replace('<<SECTION>>',section)
    notes = gpt3_completion(prompt)
    return notes


def improve_prose(research, prose):
    prompt = open_file('prompt_improve_prose.txt').replace('<<RESEARCH>>',research).replace('<<PROSE>>', prose)
    prose = gpt3_completion(prompt)
    return prose

def add_featured_image(search_term, media_headers):
    # Search for an image on Unsplash using the search term
    images = search_unsplash(search_term)
    if len(images) > 0:
        # If there are any images, choose a random image from the list
        random_image = random.choice(images)
        # Get the URL of the image
        image_url = random_image['urls']['regular']
        # Download the image from the URL
        image_data = requests.get(image_url).content
        # Generate a random number from 1 to 100
        random_number = random.randint(1, 100)
        # Generate a filename for the image
        filename = '{}-{}.jpg'.format(search_term, random_number)
        # Set the Content-Disposition header to include the generated filename
        media_headers['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        # Upload the media object to the WordPress site
        media_response = requests.post(
            'https://reptileland.net/wp-json/wp/v2/media',
            headers=media_headers,
            data=image_data
        )
        media_id = media_response.json()['id']
        return media_id
    else:
        # If no images are found, return None
        return None

def capitalize_words(string):
  # Split the string into a list of words
  words = string.split()

  # Capitalize each word and join them back into a single string
  capitalized_string = " ".join([word.capitalize() for word in words])
  return capitalized_string

def get_most_important_subject(sentence):
  # Parse the sentence using spaCy
  doc = nlp(sentence)

  # Identify the nouns and proper nouns in the sentence
  nouns = []
  proper_nouns = []
  for token in doc:
    if token.pos_ == "NOUN":
      nouns.append(token.text)
    elif token.pos_ == "PROPN":
      proper_nouns.append(token.text)

  # Determine the most important noun based on context and domain knowledge
  if len(proper_nouns) > 0:
    return proper_nouns[0]
  elif len(nouns) > 0:
    return nouns[0]
  else:
    return None


def title_ask(keyword):
  # Set the model to use
  model_engine = "text-davinci-003"

  # Create the prompt for the question
  prompt = (f"Create an eye-catching and interesting title that incorporates the keyword '{keyword}'. The title should be attention-grabbing and memorable, and should effectively convey the topic of the content it is associated with.")

  # Set the parameters for the request
  completions = openai.Completion.create(
      engine=model_engine,
      prompt=prompt,
      max_tokens=50,
      n=1,
      stop=None,
      temperature=0.5,
  )

  # Get the response from the API
  response = completions.choices[0].text

  response = response.translate(str.maketrans('', '', string.punctuation))

  # Return the response
  return response

def get_keyword_from_excel(filepath):
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    for row in sheet.rows:
        yield row[1].value



if __name__ == "__main__":
    used_image_urls = []
    for request in get_request_from_file("keywords.xlsx"):
        for keyword in get_keyword_from_excel("keywords.xlsx"):
            pomocni_request = 'I want a professional blog on the following topic: ' + request
            prompt = open_file("prompt_outline.txt").replace("<<REQUEST>>", pomocni_request)
            #print("ovo je request: " + request)
            #print("ovo je keyword: " + keyword)
            outline = "1. " + gpt3_completion(prompt)
            print("\n\nOUTLINE:", outline)
            for i in list(range(0, 2)):
                outline = improve_outline(pomocni_request, outline)
                print("\n\nIMPROVED OUTLINE:", outline)
            outline = outline.replace("\n\n", "\n")
            sections = outline.splitlines()
            final_blog = list()
            for index, section in enumerate(sections):
                # research
                research = ""
                print("\n\nSECTION:", section)
                for i in list(range(0, 1)):
                    result = neural_recall(pomocni_request, section)
                    research = research + "\n%s" % result
                    print("\n\nRESEARCH:", research)
                research = research.strip()
                # first draft
                prompt = (
                    open_file("prompt_section_prose.txt")
                    .replace("<<REQUEST>>", pomocni_request)
                    .replace("<<SECTION>>", section)
                    .replace("<<RESEARCH>>", research)
                )
                prose = gpt3_completion(prompt)
                print("\n\nPROSE:", prose)
                # improve prose
                for i in list(range(0, 1)):
                    prose = improve_prose(research, prose)
                    print("\n\nIMPROVED PROSE:", prose)
                # MICE SVE BROJEVE ILI SLOVA PRIJE TOČKE U SECTIONU, TAKOĐER MICE WHITE SPACE
                section = section.split('.', 1)[1]
                section = section.strip()
                final_blog.append("<h2>%s</h2><p>%s</p>" % (section,prose))
                if index % 3 == 2:
                    outline_item = sections[index]
                    api_url = "https://api.unsplash.com/search/photos?query={}&client_id={}".format(
                        keyword, ACCESS_KEY
                    )
                    # Make the API request
                    response = requests.get(api_url)
                    # Check the status code of the response
                    if response.status_code == 200:
                        if len(response.json()["results"]) > 0:
                            # Choose a random image from the results
                            random_index = random.randint(0, len(response.json()["results"]) - 1)
                            image_url = response.json()["results"][random_index]["urls"]["regular"]
                            # Check if the image URL has already been used
                            while image_url in used_image_urls:
                                # If it has, choose a new random index and check again
                                random_index = random.randint(0, len(response.json()["results"]) - 1)
                                image_url = response.json()["results"][random_index]["urls"]["regular"]
                            # Add the image URL to the list of used image URLs
                            used_image_urls.append(image_url)
                            # Use the generated variation as the alt attribute
                            a_element = '<img src="{}" alt="{}" class="size-medium" style="display: block; margin: 0 auto;">'.format(image_url, outline_item)
                            # Add the a element to the final blog
                            print(a_element)
                            final_blog.append(a_element)
                        else:
                            print("No results found")
                    else:
                        # If the request is unsuccessful, print an error message
                        print("Error searching for images on Unsplash")
            final_blog = "\n".join(final_blog)
            capitalized_title = title_ask(request)
            media_id = add_featured_image(keyword, media_header)
            post = {
                'title': capitalized_title,
                'status': 'publish',
                'content': final_blog,
                'categories': 33,
                'permalink_template': request,
                'featured_media': media_id
            }
            #print("\n\nFINAL BLOG:", final_blog)
            output = final_blog
            #save_file("blog.txt", output)
            response = requests.post(url, headers=header, json=post)
            if response.status_code == 201:
                print('Success!')
            else:
                print('Error:', response.status_code)
