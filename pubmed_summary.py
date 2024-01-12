#pip install requests openai streamlit
#pip install terminalgpt -U --user

import streamlit as st
import requests
import xml.etree.ElementTree as ET
import os
import datetime
import openai
from openai import OpenAI

def pubmed_search(query, max_results=20):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}"
    search_response = requests.get(search_url)
    search_ids = ET.fromstring(search_response.content).findall('.//IdList/Id')
    id_list = ','.join([id.text for id in search_ids])

    fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={id_list}&rettype=abstract"
    fetch_response = requests.get(fetch_url)
    return fetch_response.text

def extract_abstracts_with_references(xml_string):
    root = ET.fromstring(xml_string)
    abstracts_with_refs = []
    for article in root.findall('.//PubmedArticle'):
        pubmed_id = article.find('.//PMID').text
        first_author = article.find('.//AuthorList/Author[1]')
        pub_date = article.find('.//PubDate')
        journal = article.find('.//Journal/ISOAbbreviation')  # 或者使用 './/Journal/Title'

        # 尋找發表年份和月份
        pub_date = article.find('.//PubDate')
        year = pub_date.find('Year').text if pub_date is not None and pub_date.find('Year') is not None else 'Unknown Year'
        month = pub_date.find('Month').text if pub_date is not None and pub_date.find('Month') is not None else 'Unknown Month'
        journal_abbrev = journal.text if journal is not None else 'Unknown Journal'


        # Check if first_author and LastName exist
        if first_author is not None and first_author.find('LastName') is not None:
            author_name = first_author.find('LastName').text + ' et al.'
        else:
            author_name = 'Unknown Author'

        abstract_text = article.find('.//Abstract/AbstractText')
        if abstract_text is not None:
            abstract_with_ref = f"[{pubmed_id}] {author_name} {year}, {month}. {journal_abbrev}, {abstract_text.text}"
            abstracts_with_refs.append(abstract_with_ref)
    return abstracts_with_refs



def summarize_abstracts(abstracts_with_refs):
    system_prompt = f"You are an endocrinologist and are writing an abstract related to the topic {query}. Please think step by step and organize relevant content from each {abstracts_with_refs} into an insightful, coherent abstract, synthesizing information only from the {combined_abstracts} provided, ensuring the abstract is academic. Be specific, logically coherent and maintain a professional tone. The topic {query} should be thoroughly addressed based on these {combined_abstracts}."
    user_prompt = f"Based on the {combined_abstracts} provided, please develop a comprehensive summary. Explicitly reference the citation markers such as [1], [2], etc., as they appear in the original abstracts. Ensure the paper is logically structured, academically, and focused on the topic of '{query}'."
    messages = [
    { "role": "system", "content": system_prompt},
    { "role": "user", "content": user_prompt}
    ]
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        temperature=0,
    )
    return completion.choices[0].message.content

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.title('PubMed Abstracts Summarizer')
st.markdown("""
            Search from PubMed, then Summarize with GPT-4 Using Academic Writing Methods.  
            Writing by Doctor Tseng from Department of Endocrinology of Tungs' Taichung Metroharbor Hospital.
            """)


api_key = st.text_input("請輸入您的API金鑰: ", type="password", key="apikey")
if not api_key:
    st.write("API金鑰未輸入")
else:
    openai.api_key = api_key
    client = OpenAI(api_key=api_key)

# 设置时间范围和关键词
start_date = st.date_input("Start date", value=datetime.date(2023, 1, 1))
end_date = st.date_input("End date", value=datetime.date(2023, 12, 31))
date_range = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}"

# Input field for query
default_query = '("Artificial Intelligence") AND thyroid AND ultrasonography AND cytology'
query = st.text_input("Enter your query", key="query")
st.markdown(f"Example Query: `{default_query}`")

combined_query = f"{query} AND ({date_range}[PDAT])"

if st.button('Fetch and Summarize'):
    # Fetching abstracts from PubMed

    xml_response = pubmed_search(combined_query)
    abstracts_with_refs = extract_abstracts_with_references(xml_response)

    # Combine all abstracts into one long string, each preceded by its number
    combined_abstracts = "\n\n".join([f"Abstract {i}:\n{abstract}" for i, abstract in enumerate(abstracts_with_refs, 1)])

    # Display all abstracts in one scrollable text area
    st.text_area("All Abstracts", combined_abstracts, height=300)  # Adjust height as needed


    # Summarizing and displaying the overall summary
    overall_summary = summarize_abstracts(combined_abstracts)
    st.write("## Overall Summary")
    st.write(overall_summary)