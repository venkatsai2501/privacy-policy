from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import TrackedSite
from .forms import URLForm
from django.shortcuts import render, get_object_or_404, redirect
import re
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import TrackedSite
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse
#from transformers import T5Tokenizer, T5ForConditionalGeneration

# # Initialize tokenizer and model
# tokenizer = T5Tokenizer.from_pretrained("t5-large")
# model = T5ForConditionalGeneration.from_pretrained("t5-large")

# Function to chunk text based on max token length
# def chunk_text(text, max_token_limit=512):
#     # Tokenize text
#     tokens = tokenizer.encode(text, truncation=False)
#     # Split into chunks
#     chunks = [tokens[i:i + max_token_limit] for i in range(0, len(tokens), max_token_limit)]
#     return chunks

# # Function to summarize text chunk
# def summarize_chunk(chunk):
#     inputs = tokenizer.decode(chunk)
#     inputs = tokenizer("summarize: " + inputs, return_tensors="pt", max_length=512, truncation=True)
#     summary_ids = model.generate(inputs["input_ids"], max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
#     summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
#     return summary

# # Main function to summarize long text
# def summarize_long_text(text):
#     # Step 1: Split into chunks
#     chunks = chunk_text(text, max_token_limit=512)
    
#     # Step 2: Summarize each chunk
#     chunk_summaries = [summarize_chunk(chunk) for chunk in chunks]

#     # # Step 3: Combine summaries and re-summarize if needed
#     combined_summary = " ".join(chunk_summaries)
#     # if len(tokenizer.encode(combined_summary)) > 512:  # Re-chunk if needed
#     #     final_summary = summarize_long_text(combined_summary)  # Recursive call if still long
#     # else:
#     #     final_summary = summarize_chunk(tokenizer.encode(combined_summary))
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

#     return combined_summary
def summary_gpt(text):

    # Construct the messages for the GPT-3.5 Turbo chat-based API
    messages = [
        {"role": "system", "content": "You are a helpful assistant who summarizes text."},
        {"role": "user", "content": f"The text given to you is a extracted text through web scraping using python.Its a privacy policy.Kindly summarize the privacy policy and give points.:\n\n{text}"}
    ]

    # Call the API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use "gpt-4" for even better results if available
        messages=messages,
        max_tokens=4000,  # Adjust max tokens for summary length
        temperature=0.7,
    )

    # Extract the summary
    summary = response['choices'][0]['message']['content']
    return summary

def landing_page(request):
    return render(request, 'landing.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def dashboard(request):
    sites = TrackedSite.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {'sites': sites})

def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def add_url_view(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            tracked_site = form.save(commit=False)  # Don't save to the database yet
            tracked_site.user = request.user       # Associate the logged-in user
            tracked_site.save()                    # Save to the database
            return redirect('dashboard')           # Redirect back to dashboard
    else:
        form = URLForm()
    return render(request, 'add_site.html', {'form': form})

def site_detail(request, site_id):
    site = get_object_or_404(TrackedSite, id=site_id)
    context = {
        'site': site,
        # Ensure these fields exist in your model
        'privacy_policy_last_updated': site.privacy_policy_last_updated,
        'privacy_policy_last_checked': site.last_checked,
        'terms_of_service_last_updated': site.terms_of_service_last_updated,
        'terms_of_service_last_checked': site.last_checked,
    }
    return render(request, 'site_detail.html', context)
last_updated_patterns = [
    re.compile(r"(Effective\s+)(\d{1,2}\s+[A-Za-z]+\s+\d{4})", re.IGNORECASE),
    # Common formats with "Last updated", "Last revised", "Effective date", and "Updated on"
    re.compile(r"(Last updated:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Last updated on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(updated:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(updated on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Last revised:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Effective date:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),

    # Variations with "Last modified"
    re.compile(r"(Last modified:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Last modified on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(modified:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(modified on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),

    # Numeric date formats (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
    re.compile(r"(Last updated:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(Last updated on:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(updated:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(updated on:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(Last revised:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(Effective date:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"(Last modified:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),

    # ISO date formats (YYYY-MM-DD, YYYY.MM.DD)
    re.compile(r"(Last updated:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(Last updated on:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(updated:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(updated on:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(Last revised:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(Effective date:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(Last modified:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(modified on:\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE),

    # Dot-separated date formats (DD.MM.YYYY, YYYY.MM.DD)
    re.compile(r"(Effective date:\s*)(\d{4}\.\d{2}\.\d{2})", re.IGNORECASE),
    re.compile(r"(Effective date:\s*)(\d{2}\.\d{2}\.\d{4})", re.IGNORECASE),
    re.compile(r"(Last modified:\s*)(\d{4}\.\d{2}\.\d{2})", re.IGNORECASE),
    re.compile(r"(Last modified on:\s*)(\d{2}\.\d{2}\.\d{4})", re.IGNORECASE),

    # Additional flexible phrasing
    re.compile(r"(Last update:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Effective on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Revised on:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
]

def parse_date_from_text(text):
    for pattern in last_updated_patterns:
        match = pattern.search(text)
        if match:
            date_str = match.group(2)
            try:
                # Attempt to parse the date string with different formats
                for fmt in ("%B %d, %Y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d" , "%d.%m.%Y","%m.%d.%Y","%d %B %Y"):
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        return parsed_date.strftime('%Y-%m-%d')  # Format to YYYY-MM-DD
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error parsing date: {e}")
    return None
def extract_body_text(driver):
    """
    Extracts the body text from the current page.
    """
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception as e:
        print(f"Error extracting body text: {e}")
        return ""
        
def find_link_by_keywords(driver, keywords):
    """
    Finds the first link on the page that matches the given keywords.
    :param driver: Selenium WebDriver instance
    :param keywords: List of keywords to search in the links
    :return: URL of the matching link or None if not found
    """
    links = driver.find_elements(By.TAG_NAME, "a")  # Get all anchor tags
    for link in links:
        href = link.get_attribute("href")
        text = link.text.lower()
        if href and any(keyword.lower() in text for keyword in keywords):
            return href
    return None
def navigate_and_extract(driver, base_url, keywords):
    """
    Navigates to a page containing keywords and extracts the body text.
    :param driver: Selenium WebDriver instance
    :param base_url: Base URL to start navigation
    :param keywords: Keywords to search for in the links
    :return: Extracted text from the target page or None if navigation fails
    """
    driver.get(base_url)  # Load the base URL
    time.sleep(5)  # Wait for the page to load

    # Find the link based on keywords
    target_link = find_link_by_keywords(driver, keywords)
    if target_link:
        driver.get(target_link)  # Navigate to the target page
        time.sleep(2)  # Wait for the target page to load
        return extract_body_text(driver)  # Extract the body text
    return None

def scan_url_view(request, site_id):
    # Fetch the TrackedSite instance based on site_id
    site = get_object_or_404(TrackedSite, id=site_id)

    # Get the URL from the selected TrackedSite instance
    url = site.url

    # Selenium Web scraping to extract text
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    try:
        # Extract Privacy Policy
        privacy_policy_keywords = ["privacy policy", "privacy notice","privacy","privacy note"]
        privacy_policy_text = navigate_and_extract(driver, url, privacy_policy_keywords)

        # Extract Terms of Service
        terms_of_service_keywords = ["terms of service", "terms and conditions", "terms of use","conditions of use","terms"]
        terms_of_service_text = navigate_and_extract(driver, url, terms_of_service_keywords)

        # Summarize Texts
        privacy_policy_summary = summary_gpt(privacy_policy_text) if privacy_policy_text else None
        terms_of_service_summary = summary_gpt(terms_of_service_text) if terms_of_service_text else None

        # Extract "Last updated" date from Privacy Policy (if found)
        privacy_policy_last_updated = parse_date_from_text(privacy_policy_text or "")
        terms_of_service_last_updated =  parse_date_from_text(terms_of_service_text or "")

        # Save extracted data to the database
        site.privacy_policy_extracted = privacy_policy_text
        site.privacy_policy_summary = privacy_policy_summary
        site.terms_of_service_extracted = terms_of_service_text
        site.terms_of_service_summary = terms_of_service_summary

        # Update timestamps
        site.last_checked = datetime.now()
        #last_updated = last_updated or site.last_checked  # Use extracted or fallback to now
        site.privacy_policy_last_updated = privacy_policy_last_updated
        site.terms_of_service_last_updated =  terms_of_service_last_updated
        # Save the site instance
        site.save()

    finally:
        # Close the WebDriver
        driver.quit()

    # Redirect to the dashboard (you can display the updated data in the dashboard)
    return redirect('dashboard')  # Assuming 'dashboard' is the name of your dashboard URL

def edit_url_view(request, pk):
    url_entry = get_object_or_404(TrackedSite, pk=pk)
    
    if request.method == 'POST':
        form = URLForm(request.POST, instance=url_entry)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirect to dashboard after saving
    else:
        form = URLForm(instance=url_entry)
    
    return render(request, 'edit_url.html', {'form': form})

def delete_url_view(request, pk):
    url_entry = get_object_or_404(TrackedSite, pk=pk)
    
    if request.method == 'POST':
        url_entry.delete()
        return redirect('dashboard')  # No success message needed if JavaScript confirms
    
    return render(request, 'delete_url.html', {'url_entry': url_entry})




