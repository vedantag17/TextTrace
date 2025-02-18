import streamlit as st
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import pipeline   
import torch
import nltk
from nltk.util import ngrams
from nltk.lm.preprocessing import pad_sequence
from nltk.probability import FreqDist
import plotly.express as px
from collections import Counter
from nltk.corpus import stopwords
import string

nltk.download('punckt')
nltk.download('stopwords')
# Load GPT-2 tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
pipe = pipeline("text-classification", model="textattack/bert-base-uncased-SST-2")

def calculate_perplexity(text):
    encoded_input = tokenizer.encode(text, add_special_tokens=False, return_tensors='pt')
    input_ids = encoded_input[0]

    with torch.no_grad():
        outputs = model(input_ids)
        logits = outputs.logits

    perplexity = torch.exp(torch.nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), input_ids.view(-1)))
    return perplexity.item()

def calculate_burstiness(text):
    tokens = nltk.word_tokenize(text.lower())
    word_freq = FreqDist(tokens)
    repeated_count = sum(count > 1 for count in word_freq.values())
    burstiness_score = repeated_count / len(word_freq)
    return burstiness_score

def plot_top_repeated_words(text):
    # Tokenize the text and remove stopwords and special characters
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    tokens = [token.lower() for token in tokens if token.lower() not in stop_words and token.lower() not in string.punctuation]

    # Count the occurrence of each word
    word_counts = Counter(tokens)

    # Get the top 10 most repeated words
    top_words = word_counts.most_common(10)

    # Extract the words and their counts for plotting
    words = [word for word, count in top_words]
    counts = [count for word, count in top_words]

    # Plot the bar chart using Plotly
    fig = px.bar(x=words, y=counts, labels={'x': 'Words', 'y': 'Counts'}, title='Top 10 Most Repeated Words')
    st.plotly_chart(fig, use_container_width=True)

def probability_score(text):
    scores = pipe(text)
    output = scores[0]
    output["score"] = int(100 * output["score"])
    if output["label"] == "LABEL_0":
        output["label"] = "Human written"
        output["human_score"] = output["score"]
        output["ai_score"] = 100 - output["score"]
    else:
        output["label"] = "AI-generated"
        output["ai_score"] = output["score"]
        output["human_score"] = 100 - output["score"]
    return output

st.set_page_config(layout="wide")

st.title("TextTrace: Your AI Detector🔍")
text_area = st.text_area("Enter text", "")

if text_area is not None:
    if st.button("Analyze"):
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            st.info("Your Input Text")
            st.success(text_area)
        
        with col2:
            st.info("Detection Score")
            perplexity = calculate_perplexity(text_area)
            burstiness_score = calculate_burstiness(text_area)

            st.write("Perplexity:", perplexity)
            st.write("Burstiness Score:", burstiness_score)

            score = probability_score(text_area)
            st.write(f'AI-generated: {score["ai_score"]}%')
            st.write(f'Human-written: {score["human_score"]}%')

            if perplexity > 25000 and burstiness_score < 0.3:
                st.error("Text Analysis Result: AI generated content")
            else:
                st.success("Text Analysis Result: Likely Human written content")
        
            
            
        with col3:
            st.info("Basic Details")
            plot_top_repeated_words(text_area)