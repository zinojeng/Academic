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
        # Extracting the PubMed ID
        pubmed_id = article.find('.//PMID').text

        # Extracting only the first author for APA reference
        first_author = article.find('.//AuthorList/Author')
        if first_author is not None:
            author_name = first_author.find('LastName').text + ' et al.'
        else:
            author_name = 'Anonymous'

        # Extracting other required information for APA reference
        year = article.find('.//PubDate/Year')
        article_title = article.find('.//ArticleTitle')
        journal = article.find('.//Journal/Title')
        doi = article.find(".//ArticleIdList/ArticleId[@IdType='doi']")

        # Constructing the APA reference
        apa_reference = f"{author_name} ({year.text if year is not None else 'n.d.'}). {article_title.text if article_title is not None else 'No title'}. {journal.text if journal is not None else 'No journal'}, {doi.text if doi is not None else 'No DOI'}."

        # Extracting the abstract
        abstract_text = article.find('.//Abstract/AbstractText')
        if abstract_text is not None:
            abstract_with_ref = f"{abstract_text.text} [{pubmed_id}]"
            abstracts_with_refs.append((abstract_with_ref, apa_reference))
    return abstracts_with_refs


def summarize_abstracts(abstracts_with_refs):
    system_prompt = f"You are an endocrinologist and writing a paper related to the topic '{query}'. Please think analytically and create a coherent academic article, synthesizing the information exclusively from the provided {combined_abstracts}, ensuring the summary is logically coherent and maintains a professional tone. The topic '{query}' should be thoroughly addressed based on these {combined_abstracts}."
    user_prompt = f"Based on the {combined_abstracts} provided, please develop a comprehensive academic paper. Explicitly reference the citation markers such as [1], [2], etc., as they appear in the original abstracts. Ensure the paper is logically structured, academically styled, and focused on the topic of '{query}'. After the summary, include a complete list of references in APA style, corresponding to the citation markers."
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

st.title('PubMed Abstracts Summarizer')


api_key = st.text_input("請輸入您的API金鑰: ", type="password", key="apikey")
if not api_key:
    st.error("API金鑰未輸入")
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
    abstracts_with_refs = ["\n".join(map(str, tup)) for tup in abstracts_with_refs]
    combined_abstracts = "\n".join(abstracts_with_refs)

    # Combine all abstracts into one long string
    combined_abstracts = "\n\n".join([f"Abstract {i}:\n{abstract}" for i, abstract in enumerate(abstracts_with_refs, 1)])

    # Display all abstracts in one scrollable text area
    st.text_area("All Abstracts", combined_abstracts, height=300)  # Adjust height as needed


    # Summarizing and displaying the overall summary
    overall_summary = summarize_abstracts(combined_abstracts)
    st.write("## Overall Summary")
    st.write(overall_summary)