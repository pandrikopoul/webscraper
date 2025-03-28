import uuid
import gradio as gr
import os  # Import os for file operations
import re
# ... (your existing imports) ...
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import asyncio
#test
from google import genai
import aiofiles
import numpy as np
prompt_prefix = """Extract the following comma separated product specifications from the text file :"""
prompt_suffix = """ The product description should be minimum 100 words describing the details of this product(if a product description already provided dont include also the provided one because we will have yours and we dont want duplicates) .
Give it to me organized in a tabular text structure not json etc in order to be able later to convert it in csv where collumn 1 will be the spec names and the second the values, where columns are separated by the pipe symbol ('|') and each row is separated by a newline character.
Dont include in your responce anithing like here they are the results.
I only need the content related to the responce in my request.The description also should be part of the table.I want everything to be translated in the greek language excepte things that if they are translated in Greek will not make sence like pixels, Lumens etc.Please do not miss anything about the given spec keywords.SO I need any information that exist in the text file about the given keywords specs.Dont miss anithing.But i need only info about the given keywords,nothing else, so the spesifications in the table should be only the given keywords and nothing else.:\n\n{file_content}"""
default_prompt = """Extract all product  specifications from this text file including product name, price, and every spec (dont miss any spec). Also generate a product description of at least 50 words for this product(if a product description already provided dont include also the provided one because we will have yours and we dont want duplicates) .Include all the relevant info, plus if you find any specific desctiopions.
Give it to me organized in a tabular text structure not json etc in order to be able later to convert it in csv where collumn 1 will be the spec names and the second the values, where columns are separated by the pipe symbol ('|') and each row is separated by a newline character.
I only need the content related to the responce in my request.The description also should be part of the table with name .Anso if you find any specific descriptions put them in the table as well with appropriate names.Please dont miss any information.Also i want everything to be translated properly in Greek language but in order to make sense, except things that, if they are translated in Greek, will not make sense like pixels, Lumens etc:\n\n{file_content}"""

# Predefined password
PASSWORD = os.getenv("SECRET_KEY")  # Replace with your desired password

# ✅ Async Function to Initialize Gemini Client
async def init_genai_client(api_key):
    return genai.Client(api_key=api_key)

# ✅ Login Function
def login(password, user_api_key):
    if not user_api_key.strip():
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="Please provide your Google Cloud API key. If you don't have one, create one [here](https://aistudio.google.com/u/1/apikey)."), user_api_key

    if password == PASSWORD:
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False, value=""), user_api_key
    else:
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="Wrong password. If you forgot the password please contact the administrator."), user_api_key

# ✅ Async Content Generation
async def generate_content_async(client, prompt):
    response = await asyncio.to_thread(client.models.generate_content, model="gemini-2.0-flash", contents=prompt)
    return response.text


async def scrape_and_extract(url, keywords, api_key):
    if not api_key:
        return "API key is missing. Please log in again."
    
    client = await init_genai_client(api_key)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    
    wait = WebDriverWait(driver, 10)
    await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.TAG_NAME, "body")))

    cookie_keywords = ["Allow all cookies", "Accept all", "Agree", "Accept"]
    for keyword in cookie_keywords:
        try:
            button = await asyncio.to_thread(wait.until, EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{keyword}')]")))
            await asyncio.to_thread(button.click)
            break
        except:
            continue
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight / 2);")
        await asyncio.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    page_source = driver.page_source
    driver.quit()
    
    file_path = "page_content.txt"
    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.write(page_source)
    
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        file_content = await file.read()
    
    prompt = default_prompt.format(file_content=file_content) if not keywords.strip() else f"{prompt_prefix}{keywords}{prompt_suffix}".format(file_content=file_content)
    response_text = await generate_content_async(client, prompt)
    
    output_path = "output.txt"
    async with aiofiles.open(output_path, "w", encoding="utf-8") as file:
        await file.write(response_text)
    
    async with aiofiles.open(output_path, "r", encoding="utf-8") as file:
        specs_text = await file.read()
    
    specs_text = re.sub(r"\|\-+\|\-+\|", "", specs_text)
    lines = [line.strip("|").strip() for line in specs_text.split("\n") if "|" in line]
    specs_list = [[parts[0].strip(), parts[1].strip()] if len(parts) == 2 else [parts[0].strip(), ""] for line in lines for parts in [line.split("|")]]
    df = pd.DataFrame(specs_list, columns=["Specification", "Value"])
    csv_path = "extracted_specs.csv"
    df.to_csv(csv_path, index=False)
    
    return df  # Return the dataframe instead of the CSV file path

from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
import time

class Seafoam(Base):
    pass

seafoam = Seafoam()
data = {
    "Column 1": [1, 2, 3, 4],
    "Column 2": ["A", "B", "C", "D"],
    "Column 3": [10.5, 20.5, 30.5, 40.5]
}
df = pd.DataFrame(data)

# 🎨 Gradio UI
footer_html = """
<footer id="my-custom-footer" style="text-align: center; padding: 10px; background-color: #f8f9fa; color: #6c757d; font-size: 14px;">
  <p>&copy; 2025. All rights reserved.</p>
  <p>
    <a href="#" style="color: #6c757d; text-decoration: none;">Privacy Policy</a> |
    <a href="#" style="color: #6c757d; text-decoration: none;">Terms of Service</a>
  </p>
</footer>
"""

# Gradio interface
with gr.Blocks(css=""" /* CSS here for UI customization */ """, title="Universal Eshop Ethical Web Scraper", theme=seafoam) as demo:

    with gr.Row():
        with gr.Column() as login_page:
            gr.Markdown("# 🌍 Universal Eshop Ethical Web Scraper")
            password_input = gr.Textbox(type="password", placeholder="Enter password", label="🔐 Password")
            api_key_input = gr.Textbox(type="password", placeholder="Enter API Key", label="🔑 API Key")
            login_button = gr.Button("Login", variant="primary")
            error_message = gr.Markdown("", elem_id="error_message", visible=False)
            api_key_state = gr.State("")  # Stores API Key

        with gr.Column(visible=False) as main_page:
            gr.Markdown("# 🌍 Universal Eshop Ethical Web Scraper")
            gr.Markdown("Enter a URL to scrape product data and download the extracted specifications as a CSV file.")
            url_input = gr.Textbox(lines=1, placeholder="Enter URL", label="🔗 URL")
            keywords_input = gr.Textbox(lines=1, placeholder="Enter keywords", label="🔎 Keywords")
            submit_button = gr.Button("Submit", variant="primary")
            output_file = gr.File(label="📂 Download Extracted Specs (CSV)", visible=True)
            data_table = gr.DataFrame(label="Customizable Extracted Data", visible=True)  # Added the data table for editing
            #output_dataframe = gr.DataFrame(value=df, interactive=True)

    # Login Button Action
    login_button.click(fn=login, 
                       inputs=[password_input, api_key_input], 
                       outputs=[login_page, main_page, error_message, api_key_state])

    # Scraping Button Action
    def process_scraped_data(df):
        # Replace empty strings or whitespace with NaN
        df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
        # Drop empty columns (those with all NaN or empty values)
        df_cleaned = df.dropna(axis=1, how='all')
        
        # Drop empty rows (those with all NaN or empty values)
        df_cleaned = df_cleaned.dropna(axis=0, how='all')
        
        # Save the customized table to CSV
        customized_csv_path = f"customized_specs_{uuid.uuid4()}.csv"
        df_cleaned.to_csv(customized_csv_path, index=False)
        
        return customized_csv_path  # Return the path for downloading and updated dataframe


    submit_button.click(scrape_and_extract, 
                        inputs=[url_input, keywords_input, api_key_state], 
                        outputs=[data_table])  # Display the dataframe after scraping

    # After customizing the data, allow the user to download it
    data_table.change(fn=process_scraped_data, inputs=[data_table], outputs=[output_file])

    # Inject Custom Footer
    gr.HTML(footer_html)
# This is the Gradio app you want to serve with Gunicorn
demo.launch(share=False, server_name="0.0.0.0", server_port=7860, debug=True)
