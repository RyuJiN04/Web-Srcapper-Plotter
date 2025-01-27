import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu

# Page Configuration for Streamlit
st.set_page_config(
    page_title="Web Scrapping and plotting tool",
    layout="wide",
    initial_sidebar_state="expanded"
    
)
# Custom CSS for gradient background and other styles
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://wallpapers.com/images/featured/keyboard-lpsw7sus4web2y8i.webp'); /* Replace with your image URL */
        background-size: cover; /* Ensures the image covers the entire page */
        background-position: center; /* Centers the image */
        background-repeat: no-repeat; /* Prevents the image from repeating */
        color: white;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Session State Setup
if 'scrape_count' not in st.session_state:
    st.session_state.scrape_count = 0
if 'last_scrape' not in st.session_state:
    st.session_state.last_scrape = None


# Navigation using soidebar
with st.sidebar:
    selected = option_menu(
        "Choose your desired tool :",
        ["Scrapper", "Data Cleaning", "Analysis", "Settings"],
        icons=['cloud-download', 'graph-down', 'graph-up', 'gear'],
        menu_icon="menu",
        default_index=0,
    )


# Utility Functions
def get_all_links(url):
    """Get all links from the given URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = re.sub(r'^(?!http)', f'{url.rstrip("/")}/', a_tag['href'])
        if link.startswith("http"):
            links.add(link)
    return links

def scrape_page(url):
    """Scrape the content of the given URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def scrape_data(url, options, progress_bar=None, status_text=None):
    """Main scraping function with progress tracking"""
    soup = scrape_page(url)
    data = {
        'tables': [],
        'headlines': [],
        'links': [],
        'images': [],
        'media_files': [],
        'metadata': {}
    }
    
    try:
        # Update progress
        if progress_bar: progress_bar.progress(20)
        if status_text: status_text.text("Scraping content...")
        
        # Scrape tables
        if options.get('scrape_tables'):
            tables = soup.find_all("table")
            for i, table in enumerate(tables, 1):
                if options['table_indices'] and i not in options['table_indices']:
                    continue
                rows = table.find_all("tr")
                if rows:
                    headers = [th.text.strip() for th in rows[0].find_all("th")]
                    if not headers:
                        headers = [f"Column {j+1}" for j in range(len(rows[0].find_all("td")))]
                    
                    table_data = []
                    for row in rows[1:]:
                        cols = row.find_all(["th", "td"])
                        cols = [col.text.strip() for col in cols]
                        while len(cols) < len(headers): cols.append("")
                        if len(cols) > len(headers): cols = cols[:len(headers)]
                        table_data.append(cols)
                    
                    data['tables'].append(pd.DataFrame(table_data, columns=headers))

        # Update progress
        if progress_bar: progress_bar.progress(40)
        if status_text: status_text.text("Scraping headlines...")
        
        # Scrape headlines
        if options.get('scrape_headlines'):
            for tag in options.get('headline_tags', []):
                headlines = soup.find_all(tag)
                data['headlines'].extend([h.text.strip() for h in headlines])

        # Update progress
        if progress_bar: progress_bar.progress(60)
        if status_text: status_text.text("Scraping links and media...")
        
        # Scrape links
        if options.get('scrape_links'):
            links = soup.find_all('a', href=True)
            data['links'].extend([l['href'] for l in links if l['href'].startswith('http')])
        
        # Scrape images
        if options.get('scrape_images'):
            images = soup.find_all('img', src=True)
            data['images'].extend([i['src'] for i in images if 'src' in i.attrs])
        
        # Scrape media files
        if options.get('scrape_media'):
            media = soup.find_all(['audio', 'video', 'source'])
            data['media_files'].extend([m['src'] for m in media if 'src' in m.attrs])
        
        # Get metadata
        data['metadata'] = {
            "title": soup.title.string if soup.title else "No title",
            "description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "No description",
            "keywords": soup.find("meta", {"name": "keywords"})["content"] if soup.find("meta", {"name": "keywords"}) else "No keywords"
        }
        
        # Final progress update
        if progress_bar: progress_bar.progress(100)
        if status_text: status_text.text("Scraping completed!")
        
        return data, None
        
    except Exception as e:
        return None, str(e)
    
    
 # Main UI Components
if selected == "Scrapper":
    st.title("Web Scrapper")
    st.write(" This here is a tool to scrape data from a webpage. You can scrape tables, headlines, links, images, and media files from a webpage.")
    url = st.text_input("Enter the webpage URL to scrape:")
    
    with st.expander("Scraping Options", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            scrape_tables = st.checkbox("Scrape Tables", True)
            table_indices = st.text_input(
                "Table indices (comma-separated):",
                placeholder="1,2,3"
            )
            table_indices = [int(i.strip()) for i in table_indices.split(",") if i.strip().isdigit()] if table_indices else []
            scrape_links = st.checkbox("Scrape Links") 
            
            
        
        with col2:
            
            scrape_headlines = st.checkbox("Scrape Headlines")
            headline_tags = st.multiselect(
                "Select headline tags:",
                ["h1", "h2", "h3", "h4", "h5", "h6"],
            )
            
           
    
    if st.button("Start Scraping"):
        if url:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            options = {
                'scrape_tables': scrape_tables,
                'table_indices': table_indices,
                'scrape_headlines': scrape_headlines,
                'headline_tags': headline_tags,
                'scrape_links': scrape_links,
            }
            
            data, error = scrape_data(url, options, progress_bar, status_text)
            
            if error:
                st.error(f"Error: {error}")
            else:
                st.session_state.last_scrape = data
                st.session_state.scrape_count += 1
                
                # Display results
                st.success("Scraping completed")
                
                # Display metadata
                st.write("### Metadata:")
                st.json(data['metadata'])
                
                # Display scraped content
                if data['tables']:
                    for i, df in enumerate(data['tables'], 1):
                        st.write(f"### Table {i}:")
                        st.dataframe(df)
                
                if data['headlines']:
                    st.write("### Headlines:")
                    st.write(data['headlines'])
                
                if data['links']:
                    st.write("### Links:")
                    st.write(data['links'])
                
                if data['images']:
                    st.write("### Images:")
                    for img_url in data['images']:
                        st.image(img_url, caption=img_url)
                
                if data['media_files']:
                    st.write("### Media Files:")
                    st.write(data['media_files'])
        else:
            st.warning("Please enter a URL to scrape.")

elif selected == "Data Cleaning":
    st.title("Data Cleaning")
    st.write("This tool allows you to clean the scraped data by removing duplicates, dropping missing values, and normalizing text.")
    if st.session_state.last_scrape:
        data = st.session_state.last_scrape
        
        # Clean tables
        if data['tables']:
            for i, df in enumerate(data['tables'], 1):
                st.write(f"### Table {i}:")
                st.dataframe(df)
                
                if st.checkbox(f"Remove duplicates from Table {i}"):
                    df = df.drop_duplicates()
                    st.write(f"### Table {i} after removing duplicates")
                    st.dataframe(df)
                
                if st.checkbox(f"Drop missing values from Table {i}"):
                    df = df.dropna()
                    st.write(f"### Table {i} after dropping missing values")
                    st.dataframe(df)
                
                if st.checkbox(f"Normalize text in Table {i}"):
                    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
                    st.write(f"### Table {i} after normalizing text")
                    st.dataframe(df)
        
        # Clean other data
        for key in ['headlines', 'links', 'images', 'media_files']:
            if data[key]:
                st.write(f"### {key.title()}:")
                df = pd.DataFrame(data[key], columns=[key.title()])
                st.dataframe(df)
                
                if st.checkbox(f"Remove duplicates from {key.title()}"):
                    df = df.drop_duplicates()
                    st.write(f"### {key.title()} after removing duplicates")
                    st.dataframe(df)
    else:
        st.info("No data available. Please scrape some data first.")

elif selected == "Analysis":
    st.title("Data Analysis")
    st.write("This tool allows you to analyze the scraped data by visualizing tables, headlines, and links.")
    if st.session_state.last_scrape:
        data = st.session_state.last_scrape
        
        analysis_type = st.selectbox(
            "Select data to analyze:",
            ["Tables", "Headlines", "Links"]
        )
        
        if analysis_type == "Tables" and data['tables']:
            table_index = st.selectbox(
                "Select table:",
                range(len(data['tables']))
            )
            
            df = data['tables'][table_index]
            st.write("### Selected Table:")
            st.dataframe(df)
            
            analysis_method = st.selectbox(
                "Select analysis method:",
                ["Distribution Plot","Line Chart","Bar Chart","Pie Chart","Box Plot","Scatter Plot",]
            )
            
            if analysis_method == "Distribution Plot":
                column = st.selectbox("Select column:", df.columns)
                fig, ax = plt.subplots()
                sns.histplot(data=df[column], kde=True, ax=ax)
                st.pyplot(fig)
                
            elif analysis_method == "Line Chart":
                column = st.selectbox("Select column:", df.columns)    
                plt.figure(figsize=(10, 5))
                plt.plot(df[column], marker='o', linestyle='-', color='green')
                plt.title(f'Line Chart of {column}')
                plt.xlabel('Index')
                plt.ylabel(column)
                st.pyplot(plt)
                st.line_chart(df[column])
                
            elif analysis_method == "Bar Chart":
                column = st.selectbox("Select column:", df.columns)
                fig, ax = plt.subplots()
                sns.countplot(data=df, x=column, ax=ax)
                st.pyplot(fig)    
                
            elif analysis_method == "Pie Chart":
                column = st.selectbox("Select column:", df.columns)
                fig, ax = plt.subplots()
                df[column].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
                st.pyplot(fig)
                
            elif analysis_method == "Box Plot":
                column = st.selectbox("Select column:", df.columns)
                fig, ax = plt.subplots()
                sns.boxplot(data=df, y=column, ax=ax)
                st.pyplot(fig)        
                
            elif analysis_method == "Scatter Plot":
                x = st.selectbox("Select x-axis:", df.columns)
                y = st.selectbox("Select y-axis:", df.columns)
                fig, ax = plt.subplots()
                sns.scatterplot(data=df, x=x, y=y, ax=ax)
                st.pyplot(fig)    
         
                         
        elif analysis_type == "Headlines" and data['headlines']:
            df = pd.DataFrame(data['headlines'], columns=['Headlines'])
            st.write("Word Frequency Analysis")
            words = ' '.join(df['Headlines']).lower().split()
            word_freq = pd.Series(words).value_counts()
            st.bar_chart(word_freq)
        
        elif analysis_type == "Links" and data['links']:
            df = pd.DataFrame(data['links'], columns=['Links'])
            st.write("Domain Analysis")
            domains = df['Links'].apply(lambda x: re.findall(r'https?://([^/]+)', x)[0])
            domain_freq = domains.value_counts()
            st.bar_chart(domain_freq)
    
    else:
        st.info("No data available for analysis. Run the scraper first.")

elif selected == "Settings":
    st.title("Settings")
    st.write("This tool allows you to clear the session data.")
    st.write("Total scrapes:", st.session_state.scrape_count)
    
    if st.button("Clear Session Data"):
        st.session_state.clear()
        st.success("Session data cleared!")
 
   