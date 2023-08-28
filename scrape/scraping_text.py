import requests
from bs4 import BeautifulSoup

# Specify the URL of the website you want to scrape
url = 'https://reptile.guide/category/crocodilians/'

# Send an HTTP request to the website and store the response
response = requests.get(url)

# Parse the HTML content of the website
soup = BeautifulSoup(response.text, 'html.parser')

# Find all the h1 tags on the page
h1_tags = soup.find_all('h2')

# Open a file for writing
with open('h2_tags_care_guide_crocodilians_page_1.txt', 'w') as file:
    # Write the text of each h1 tag to the file, one per line
    for h1 in h1_tags:
        file.write(h1.text + '\n')
