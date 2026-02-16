import requests
from requests.auth import HTTPBasicAuth
import polars as pl
from bs4 import BeautifulSoup
from time import sleep


#for gemini
import os
from google import genai
from google.genai import types

######################################################
#wordpress username
USERNAME = None #your wordpress username

#wordpress app password
APP_PASSWORD = None #to generate a api password start from the dashboard goto users -> profile -> scroll down to application passwords

os.environ["GEMINI_API_KEY"] = None #Gemeni API key, is free can go get it from googles gemeni api online

#what post type to look at and determine if it has expired, in production use publish, for testing use draft
POST_TYPE=None # publish, draft, private, etc.

######################################################


URL = "https://jobconnectionsproject.org/wp-json/wp/v2/posts"


params = {
    "per_page": 100,   # max is 100
    "page": 1,
    "status": f"{POST_TYPE}",   # publish, draft, private, etc.
}

r = requests.get(
    URL,
    params=params,
    auth=HTTPBasicAuth(USERNAME, APP_PASSWORD)
)

r.raise_for_status()
posts = r.json()

#get all the posts
post_id_list=[]
post_footnote_list=[]
for i in range(len(posts)):
    post_id_list.append(posts[i]['id'])
    post_footnote_list.append(posts[i]['meta']['footnotes']) #get the footnote, which will be a link

#make a dict so we can convert it to a df really easily
data_dict={
    'post_id': post_id_list,
    'footnote': post_footnote_list
}
#make it a polars df
df=pl.DataFrame(data_dict)

#make the non-text ones null
df=df.with_columns(
    pl.when(pl.col('footnote')=='')
    .then(None)
    .otherwise(pl.col('footnote'))
    .alias('footnote')
)

#########################################
#get html and response code from websites
#########################################
print('\n')
print('GETTING HTML FROM POST DIRECT LINKS...')
print('\n')


response_codes=[]
site_html_list=[]
footnote_list=df['footnote'].to_list()
for i in range(len(footnote_list)):
    #check if footnote list is not none at the i index
    if footnote_list[i]!=None:
        site=requests.get(footnote_list[i])
        response_codes.append(site.status_code)
        site_html=BeautifulSoup(site.text, "html.parser") #get the site html
        site_html_list.append(site_html)
    else:
        response_codes.append(None)
        site_html_list.append(None)

response_codes_series=pl.Series(response_codes)
site_html_series=pl.Series(site_html_list)
df=df.with_columns(response_codes_series.alias('response_code'))
df=df.with_columns(site_html_series.alias('direct_url_html'))


###############################################################################################
#USING GEMINI TO ASSIGN PROBABILITY OF SOFT 404 ERRORS
###############################################################################################
print('\n')
print('USING GEMINI TO ASSESS SOFT 404 PROBABILITY...')
print('\n')


#bad practice but for sake of my code being easy to follow


# -----------------------
# Init client
# -----------------------
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

model = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = """
You are a web content classifier.

Your task is to analyze raw HTML content and estimate the probability (from 0 to 1)
that the page represents a *soft 404 error page*.

Definition:
A soft 404 page is a page that returns an HTTP 200 (or other non-404 status) but whose
content indicates the requested resource does not exist, is unavailable, or should be
considered missing.

Instructions:
- Base your judgment ONLY on the provided HTML content.
- Do NOT assume access to HTTP headers, status codes, or external context.
- Do NOT explain your reasoning.
- Do NOT include text, labels, or formatting.

Output:
- Return a single floating-point number between 0 and 1 (inclusive).

Return ONLY the number.
"""

direct_url_html_list = df["direct_url_html"].to_list()
error404_probabilities = []

# -----------------------
# Loop over HTML pages
# -----------------------
for direct_html in direct_url_html_list:
    if direct_html is None:
        error404_probabilities.append(None)
        continue

    # Clean up the user prompt
    user_prompt = (
        "What is the probability the provided html is a soft 404 error page?\n\n"
        f"{direct_html}\n\n"
        "Return ONLY a single number between 0 and 1."
    )

    response = client.models.generate_content(
        model=model,
        contents=user_prompt, # You can pass a raw string for simple user prompts
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, # Set system prompt here instead
            thinking_config=types.ThinkingConfig(
                include_thoughts=True # Ensure you use valid thinking config params
            ),
            # Optional: ensure it only returns a number using a constrained response
            response_mime_type="text/plain", 
        ),
    )

    try:
        # If using Thinking models, the text is in response.text
        val = float(response.text.strip())
    except Exception:
        val = None

    error404_probabilities.append(val)


#######################################################################
#ADD the probs to the DF
#######################################################################

error404_series=pl.Series(error404_probabilities)
df = df.with_columns(pl.Series(error404_probabilities).alias("prob_soft_404"))

df=df.with_columns(
((pl.col("response_code") != 200) | (pl.col("prob_soft_404") > 0.5)).cast(pl.Int8).alias("is_invalid")
)


invalid_df=df.filter(pl.col('is_invalid')==1) # filter the df to get only the invalid ones
invalid_post_ids=invalid_df['post_id'].to_list() #get a list of the invalid post_ids


#for loop to go thru all the invalid post ids and then to set the json status item to private
for pid in invalid_post_ids:
    site = f"{URL}/{pid}"
    r = requests.post(site, json={"status": "private"}, auth=(USERNAME, APP_PASSWORD), timeout=30)

    if r.status_code == 200:
        print(f"{pid}: OK -> private")
    else:
        print(f"{pid}: FAIL {r.status_code} -> {r.text[:200]}")
    sleep(0.2)  # be nice to the server


print(invalid_df)

print('\n')
print('COMPLETE!')
