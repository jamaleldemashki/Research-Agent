import os
import streamlit as st 
from langchain.prompts import PromptTemplate
from duckduckgo_search import DDGS
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
import requests
from bs4 import BeautifulSoup


# Model
model_name = "llama2"


try:
    ollama_llm = ChatOllama(model=model_name, base_url="http://localhost:11434")

except Exception as e:
    print("Error loading model via Ollama:", e)
    ollama_llm = None



#URL scraping
def scrape_url(url: str):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        #Get Page title (citation)
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "Untitled"
        # Graph up to 2000 Chars of text
        paragraphs = soup.find_all('p')
        text_content = ' '.join([p.get_text() for p in paragraphs])
        return text_content, title
    except Exception as e:
        return f"[Error scraping {url}: {str(e)}]", "Error title"

#This is the Prompt template i use to generate the response
summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system", 
            "You are an academic helpful research assistant.",
        ),
        (
            "human",
            "Please summarize the article titled '{title}' from the URL: {url}. Provide a concise summary of the following text in 5 bullet points:\n\n{text}",
        ),
    ]
)

chain = summary_prompt | ollama_llm

def research_topic(topic: str):
    if chain is None:
        return ("[Error] Ollama model is not loaded properly. Please check your code/env.")

    # Run DuckDuckGo search
    results = DDGS().text(
        keywords=topic,
        region='wt-wt',
        safesearch='off',
        timelimit='7d',
        max_results=10
    )
    
    all_results = list(results)
    
    # Extract just the first three URLs
    urls = [result.get("href") for result in all_results[:3]]
    
    summaries = []
    for url in urls:
        article_text, article_title = scrape_url(url)
        # Summarize each article
        summary = chain.invoke(
            {
                "text":{article_text},
                "title":{article_title},
                "url":{url},
            }
        )
        print(summary)
        # Combine the article title and summary in final output
        summaries.append(f"**Title**: {article_title}\n**URL**: {url}\n**Summary**: {summary.content}\n")

    final_report = "\n---\n".join(summaries)
    return final_report
    


def main():
    st.title("Autonomous Research Agent Llama-Based 🦙🦜🔗") 
    st.write("Enter a topic and I'll search and summarize relevant articles.")
    
    topic = st.text_input("Topic:")
    
    if st.button("Go"):
        with st.spinner("Researching... Please wait."):
            report = research_topic(topic)
        st.markdown("## Final Research Summary")
        st.markdown(report)
        
if __name__ == "__main__":
    main()
        