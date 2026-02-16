#imports
import polars as pl #i mostly use polars as it is faster than pandas and you can seamlessly switch back and forth when you need
import pandas as pd
from datetime import datetime
import datetime as dt
import requests
from bs4 import BeautifulSoup

#this is the api that i use to scrape jobs, the documentation of it can be found online by googling jobspy github
from jobspy import scrape_jobs

###Imports for pinging gpt4.1-mini
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

#imports for wordpress
from requests.auth import HTTPBasicAuth

#imports for google job ad
from datetime import timedelta
import json
import re



#KEYS and Passwords
#######################################################

#wordpress username
USERNAME = None #your wordpress username

#wordpress app password
APP_PASSWORD = None #to generate a api password start from the dashboard goto users -> profile -> scroll down to application passwords

#gpt 4.1-mini token from github models
token = None # you need to add your own token here
#you can generate your own token at: https://github.com/marketplace/models/azure-openai/gpt-4-1 and then click "use this model"


#############################################################


#####################################################
#prompt user
#####################################################
OCC_TITLE=input('Occupation title: ')
#get this format for the occupation title so we can output it in a nice format when we write our .csv file
occ_title_lower=str.lower(OCC_TITLE)
occ_title_lower=occ_title_lower.replace(' ','_')

DATE_POSTED=input('Earliest date posted (eg. 1/5/2026): ')
OCC_LOCATION=input('Location: ')
#also getting this for writing a file
location_lower=str.lower(OCC_LOCATION)
location_lower=location_lower.replace(' ','_')


#get the hours since job posting for the hours_old param
today=datetime.today()
try:
    date_posted_datetime=datetime.strptime(DATE_POSTED, "%m/%d/%Y")
except ValueError:
    print('Invalid Date')

#compute the delta of the days and then make it into hours, because jobspy hours_old expects hours
delta=today-date_posted_datetime
DELTA_HOURS=delta.total_seconds()/3600


################################################################################
#jobspy api (github)
################################################################################
print('LOADING')
print('\n')
print('Warnings and errors from jobspy search sites may appear, but the program is still running')


#returns a pd data frame
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google",'glassdoor'], # job sites 
    search_term=OCC_TITLE,
    google_search_term=f"{OCC_TITLE} jobs near {OCC_LOCATION} since {DATE_POSTED}", #google search as well
    location=OCC_LOCATION,
    results_wanted=20, #i dont know what this parameter is, perhaps google search results and not overall results

    hours_old=int(DELTA_HOURS),
    country_indeed='USA',
    
    linkedin_fetch_description=True, # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)

###############################################################################

#jobs polars df
#make the jobs df into polars
jobs_pl=pl.DataFrame(jobs)
jobs_potential=jobs_pl.filter(pl.col('job_url_direct').is_not_null())#filter to only have jobs with direct links

#Search the job HTML for these keywords

KEYWORDS = [
    "what you'll need",
    "qualifications",
    "what you'll bring",
    "experience and attributes",
    "basic qualifications",
    "years of",
    "what you have",
    "what you'll bring"
]

###Simple function to get keywords on page
#note this doesnot work if the website uses javascript or also blocks automated traffic
def page_contains_keywords(url, keywords, timeout=10):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Get visible text
        page_text = soup.get_text(separator=" ").lower()

        # Check if ANY keyword appears
        for kw in keywords:
            if kw.lower() in page_text:
                return 1, str(soup)

        return 0, None

    except Exception as e:
        print(f"Error with {url}: {e}")
        return 0, None

##########################################################################
#get the list of links that have the direct link
job_list=jobs_potential['job_url_direct'].to_list()
results = [] #init a list 
soup_list=[] #init a html list

#check if the keywords show up in the 
for url in job_list:
    flag,soup = page_contains_keywords(url, KEYWORDS)
    results.append(flag)
    soup_list.append(soup)

#make qual a column in the dataframe
#adding qual where qual is a col of 1's and 0's
qual_series=pl.Series(results)
jobs_potential=jobs_potential.with_columns((qual_series).alias('qualifications'))


#adding a soup series, where soup is the html of the pages that we had a direct url to
html_series=pl.Series(soup_list)
jobs_potential=jobs_potential.with_columns((html_series).alias('original_html'))

#finally filter down where we have qualifications
jobs_potential_final=jobs_potential.filter(pl.col('qualifications')==1)

##########################################################################

#final
print(f'Found {sum(results)} jobs with direct links and qualifications.')

#download the html or save it and then we can parse it and store it as a dataframe


print('GETTING HTML FOR THE JOBS')
print('\n')
print('Loading...')


####################################################################################
#use the dataframe in memory

endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"


#get lists of titles and descriptions to loop over
job_description_list=jobs_potential_final['description'].to_list()
title_list=jobs_potential_final['title'].to_list()
location_list=jobs_potential_final['location'].to_list()

#these two are for google job ad
company_list=jobs_potential_final['company'].to_list()
id_list=jobs_potential_final['id'].to_list()

#get direct link list for putting link in the post json
links_list=jobs_potential_final['job_url_direct'].to_list()


#############################################################################
#inference using GPT 4.1 mini

#initalize a list to store the html generated by chatgpt
html_responses=[]

#loop over all the viable jobs
for i in range(len(job_description_list)):
    job_desc=job_description_list[i]
    job_title=title_list[i]
    location=location_list[i]

    #init a client
    client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)
    #inference using chatgpt
    response = client.complete(
        messages=[
            SystemMessage("""
    You are a professional technical editor and formatter.

    Your task is to take a raw job description and return a clean, well-structured HTML version of it.

    Rules:
    - Output valid HTML only (no explanations or markdown)
    - Preserve the original meaning, structure, and content
    - Fix spelling, grammar, punctuation, and obvious formatting errors
    - Do NOT add new requirements, responsibilities, or benefits
    - Do NOT remove any information
    - Replace any company name with exactly: "the hiring company" (capitalize when needed)
    - Do NOT invent missing details
    - If the text contains lists, convert them to proper <ul><li> lists
    - If the text contains headings, use appropriate <h2> or <h3> tags
    - Use <p> tags for normal text
    - Make the title only include the job title, no need to include "the hiring company"
    - Include a header before the job description (<h2>) with the job title, in the header use the format 'job_title' - 'location', where location is the location provided (do not include 'US', just the state)
    - Assume all of this will be placed within a body tag, thus no need to include !DOCTYPE, html, or body tags

    If something is unclear or malformed, make the minimal correction needed to improve readability without changing intent.
                          
    Lastly, in the HTML you return, under the list of job qualifications (which will almost always be a list: <ul></ul>) that are being posted incldue the following HTML:
    
                
    <!-- Treatment text -->
    <p id="treat0"></p>

    <p id="treat1"><br>Don't meet every single requirement? If you're excited about this role but your past experience doesn't align perfectly with every qualification in the job description, we encourage you to apply anyways. You may be just the right candidate for this role.<br></p>

    <p id="treat2"><br>Don't meet every single requirement? Most companies routinely hire individuals who lack some of the stated required skills. If you're excited about this role but your past experience doesn't align perfectly with every qualification in the job description, we encourage you to apply anyways. You may be just the right candidate for this role.<br></p>

    <p id="treat3"><br>Don't meet every single requirement? Most companies routinely hire individuals who lack some of the stated required skills. Studies have shown that women are less likely to apply to jobs unless they meet every single qualification. If you're excited about this role but your past experience doesn't align perfectly with every qualification in the job description, we encourage you to apply anyways. You may be just the right candidate for this role.<br></p>

    <div id="treat4"><p style="font-size: 115%; margin-top: 0;"><b>Tip from the Job Connections Project:</b></p><p><b><i>Don't meet every single requirement?</i></b> Most companies routinely hire individuals who lack some of the stated required skills. Studies have shown that women are less likely to apply to jobs unless they meet every single qualification. If you're excited about this role but your past experience doesn't align perfectly with every qualification in the job description, we encourage you to apply anyways. You may be just the right candidate for this role.<br></p></div>

    <p>&nbsp;</p>
    </div>

    Also note the following:
        - sometimes companies label qualifications 'What you'll bring/need'
        - The qualifications may be followed by EEO or some other text (<p>), however make sure to put the treatment text directly under the list part (<ul>)
                          
    Return only the final HTML.
    """),
            UserMessage(f"Here is the job title: {job_title},the location is {location},and the job description is: {job_desc}"),
        ],
        model=model
    )


    html_responses.append(response.choices[0].message.content)
    # print(response.choices[0].message.content)


##################################################################################

#add the html for the job posting that chat made to the current dataframe
jcp_series=pl.Series(html_responses)
jobs_potential_final=jobs_potential_final.with_columns((jcp_series).alias('jcp_job_html'))



###############################################################################################
#MAKING GOOGLE JOB POSTING
###############################################################################################

#function for cleaning the description of a job ad from our data frame making it friend-lier to put in google job ad
def clean_description_hard(text: str) -> str:
    if not text:
        return ""
    # Remove long divider lines made of hyphens (3+ in a row)
    text = re.sub(r'-{3,}', ' ', text)
    # Replace newlines/tabs with spaces
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Remove non-alphanumeric junk except basic punctuation
    text = re.sub(r'[^\w\s.,;:()\-&/]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

#this is how long it will stay posted on google for
two_month=today+timedelta(days=60)

#init a list to store the ads
google_scripts=[]
for i in range(len(title_list)):

    raw = location_list[i] 
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    clean_desc = clean_description_hard(job_description_list[i])

    city = None
    region = None
    country = "US"   # hard-code country
    if len(parts) >= 2:
        city = parts[0]
        region = parts[1]

    address = {
    "@type": "PostalAddress",
    "addressCountry": "US"
    }
    #add in city and region if non-null
    if city is not None:
        address["addressLocality"] = city
    if region is not None:
        address["addressRegion"] = region

    
#JSON Structure
################################################33
    #    <script type="application/ld+json">
    #    {
    #
    google_job_context=f'''
    "@context" : "https://schema.org/",
    "@type" : "JobPosting",
    "title" : "{title_list[i]}",
    "description" : "{clean_desc}", 
    '''
    #+ "identifier": {
    google_job_id=f'''
    "@type": "PropertyValue",
    "name": "Job Connections Project",
    "value": "{id_list[i]}"
    '''
    #      },

    google_job_details=f'''
    "datePosted" : "{str(today.date())}",
    "validThrough" : "{str(two_month.date())}",
    "employmentType": "FULL_TIME",
    '''

    #      "hiringOrganization" : {

    google_org_details=f'''
            "@type" : "Organization",
            "name" : "{company_list[i]}"
    '''
    #      },

    #      "jobLocation": {
    #  "@type": "Place",

# put address here

    #   }
    # }
        # </script>


    google_script1='''
    <script type="application/ld+json">
    {
    '''
    google_script2='''
        "identifier": {
    '''
    google_script3='''
        },
    '''
    google_script7='''
        "hiringOrganization" : {
    '''
    google_script3='''
        },
    '''
    google_script5 = f'''
    "jobLocation": {{
    "@type": "Place",
    "address": {json.dumps(address)}
    }}
    '''

    google_script6='''
    }
    </script>
    '''
    #there is probably a much more efficent and robust way to do this, but this is what made sense in my brain
    full_google_ad=google_script1+google_job_context+google_script2+google_job_id+google_script3+google_job_details+google_script7+google_org_details+google_script3+google_script5+google_script6
    google_scripts.append(full_google_ad)
        

#####################
#adding the job scripts to the current data frame
google_ad_series=pl.Series(google_scripts)
data=jobs_potential_final.with_columns((google_ad_series).alias('google_ad_scripts'))

####################
#output the dataframe

print('\n')
#write to CSV
data.write_csv(f'{today.month}-{today.day}-{today.year}_{occ_title_lower}_{location_lower}_jobs.csv')
print(f'Output has been saved to {today.month}-{today.day}_{today.year}-{occ_title_lower}_{location_lower}_jobs.csv')
print('\n')



###############################################################################
#CREATE JOB POSTING
###############################################################################


print(f'POSTING THE {sum(results)} JOBS...')
print('\n')

for i in range(len(html_responses)):


#google job ad html

###NOTE: you need to add the <!-- wp:html --> opening and closing tags in order to have wordpress not freak out when you include scripts in your post

    google_html = f"""
<!-- wp:html -->

    {google_scripts[i]}
<!-- /wp:html -->

   
    """

#base html with the randomizer and the scripts
    base="""
<!-- wp:html -->
<script>
    function randomizeTreat() {

    console.log("randomizeTreat() ran");

    var surveyNumber = Math.floor(1000000000 + Math.random() * 9000000000);
    console.log("Survey Number:", surveyNumber);

    let randomNumber = Math.floor(Math.random() * 8);
    console.log("Raw random number:", randomNumber);

    let randomizeGroup;

    if (randomNumber <= 3) randomizeGroup = 0;
    else if (randomNumber === 4) randomizeGroup = 1;
    else if (randomNumber === 5) randomizeGroup = 2;
    else if (randomNumber === 6) randomizeGroup = 3;
    else randomizeGroup = 4;

    console.log("Assigned treatment group:", randomizeGroup);

    var adUrl = document.referrer;
    var jobUrl = window.location.href;

    console.log("Referrer:", adUrl);
    console.log("Job URL:", jobUrl);

    const el = document.getElementById('treat' + randomizeGroup);

    if (el) {
        el.style.display = 'block';
    } else {
        console.warn("Missing element:", 'treat' + randomizeGroup);
    }
}
</script>
<!-- /wp:html -->

    
    
<!-- Structured data -->
<style>
  #treat0 {
    display: none;
  }
  #treat1 {
    display: none;
  }
  #treat2 {
    display: none;
  }
  #treat3 {
    display: none;
  }
  #treat4 {
    display: none;
    position: relative; /* Use fixed positioning */
    background-color: #fff;
    border: 1px solid #ccc;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    transition: right 0.3s ease; /* Add transition for smooth animation */
    z-index: 9999; /* Ensure it's on top of other content */
    text-align: center;
    border-radius: 5px;
    font-size: 110%;
    margin-top: 1em;
    margin-bottom: 1em;
  }
</style>
<style>
body {
    font-family: Arial, sans-serif;
    font-size: 14px;
}
.button-link {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  text-decoration: none; /* Remove the default underline */
  font-size: 18px;
}
.close-btn {
    display: block;
    font-size: 24px;
    font-weight: bold;
    cursor: pointer;
    color: white;
    background-color: black;
    text-align: center;
    padding: 5px;
    width: 20px;
    height: 20px;
    line-height: 15px;
    border-radius: 5pt;
}
.close-btn-container {
    position: absolute;
    top: 5%;
    right: 5%;
    z-index: 1010;
}
.popup-container {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1000;
}
.popup {
    position: absolute;
    top: 10%;
    left: 10%;
    width: 80%;
    height: 80%;
    background-color: white;
    border-radius: 5px;
    overflow: auto;
    padding: 20px;
    box-sizing: border-box;
}
.popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.close-btn {
    font-size: 24px;
    font-weight: bold;
    cursor: pointer;
}
.popup-content {
    font-size: 16px;
    line-height: 1.5;
}
</style>

<!-- wp:html -->
<script>
document.addEventListener("DOMContentLoaded", randomizeTreat);
</script>
<!-- /wp:html -->


    The Job Connections Project is a non-profit company that advertises open positions for other companies. Please read the hiring company’s job ad below, then click ‘Continue’.
    """
    
    
    #this is the treatment and job posting from chat gpt
    treatment_and_posting = f"""

    {html_responses[i]}

   
    """

    #add the strings together to get the full html
    full_html=google_html+base+treatment_and_posting

    #wordpress base url
    URL = "https://jobconnectionsproject.org/wp-json/wp/v2/posts"

    #rest api access



    data={
    "title": f"{title_list[i]} - {location_list[i]}",
    "content": f"{full_html}",
    "status": "draft",
    "meta": {
        "footnotes": f"{links_list[i]}"
    }

    }


    r = requests.post(
        URL,
        json=data,
        auth=HTTPBasicAuth(USERNAME, APP_PASSWORD)
    )

print('\n')
print('COMPLETE!')