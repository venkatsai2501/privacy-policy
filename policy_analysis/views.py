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
from .models import Notification
from django.http import JsonResponse
import os
import openai
from django.utils.timezone import now
from django.db import transaction
import os
from selenium import webdriver

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

import markdown
#     return combined_summary

def summary_gpt(text):

    # Construct the messages for the GPT-3.5 Turbo chat-based API
    messages = [
        {"role": "system", "content": """You are a language model that specializes in summarizing privacy policies clearly and concisely. Your task is to summarize the provided text using the following standardized template:

    ### Summary:
    1. Last Updated: mm/dd/yyyy Start with the "Last Updated" or "Effective From" date prominently displayed.Make sure that you only give date here with the format mm/dd/yyyy. for example, Last Updated Date: 01/25/1996.Donot give subheading or anyother text beacuse im using python regular expression on this to store date.
    2. **Purpose of the Policy**: Summarize the overall purpose of the privacy policy in one or two sentences.
    3. **Key Points**: Divide the summary into these subsections:
        - **Collection Practices**: Describe how user data is collected (e.g., cookies, forms, devices).
        - **Usage Practices**: Explain how the data is used (e.g., analytics, advertising, improving services).
        - **Third-Party Sharing**: Detail any sharing of data with external entities (e.g., marketing partners, law enforcement).
    4. **Legal & Ethical Terms**: Highlight key legal and ethical terms extracted using Named Entity Recognition (NER). Include terms like "Data Controller," "Data Processor," and "Consent" with brief definitions or context.
    5. **Your Rights**: Summarize user rights, such as accessing, correcting, or deleting their data.
    6. **Contact Information**: Provide instructions for how users can reach out with questions, disputes, or requests.
    7. **Additional Notes**: Add any other specific provisions or unique details found in the policy.

    - Use concise and clear language suitable for a general audience.
    - Maintain a consistent format across all summaries.
    - Highlight important terms and concepts while avoiding unnecessary details.

    """},
        {"role": "user", "content": f"Summarize the following privacy policy using the provided template::\n\n{text}"}
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
    html_summary = markdown.markdown(summary)
    return html_summary

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
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Detect new notifications
    new_notification = notifications.filter(is_read=False, created_at__gte=timezone.now() - timezone.timedelta(seconds=10)).first()
    new_notification_message = new_notification.message if new_notification else None

    # Auto scan status and countdown logic
    for site in sites:
        if site.auto_scan_enabled and site.last_auto_scan_time:
            site.next_scan_in_seconds = max(
                0, (site.last_auto_scan_time + timezone.timedelta(hours=24) - timezone.now()).total_seconds()
            )
        else:
            site.next_scan_in_seconds = 0  # Default to 0 if not enabled

    context = {
        'sites': sites,
        'notifications': notifications,
        'new_notification_message': new_notification_message,  # Pass message once
    }
    return render(request, 'dashboard.html', context)


@login_required
def toggle_auto_scan(request, site_id):
    site = get_object_or_404(TrackedSite, id=site_id, user=request.user)
    if request.method == 'POST':
        site.auto_scan_enabled = not site.auto_scan_enabled
        site.last_auto_scan_time = timezone.now() if site.auto_scan_enabled else None
        site.save()
        return JsonResponse({'status': 'success', 'auto_scan_enabled': site.auto_scan_enabled})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
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
            
            # Create a notification for the user
            Notification.objects.create(
                user=request.user,
                message=f"URL '{tracked_site.title}' was successfully added."
            )
            
            return redirect('dashboard')  # Redirect back to dashboard
    else:
        form = URLForm()
    return render(request, 'add_site.html', {'form': form})

from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def site_detail(request, site_id):
    site = get_object_or_404(TrackedSite, id=site_id)

    # Ensure history is sorted and deduplicated
    privacy_policy_history = site.privacy_policy_history or []
    seen_dates = set()
    filtered_history = []

    # Sort and deduplicate history
    for entry in sorted(privacy_policy_history, key=lambda x: x.get('date', ''), reverse=True):
        if entry.get("date") and entry["date"] not in seen_dates:
            seen_dates.add(entry["date"])
            filtered_history.append(entry)

    # Auto Scan Countdown Logic
    remaining_seconds = 0
    if site.auto_scan_enabled and site.last_auto_scan_time:
        next_scan_time = site.last_auto_scan_time + timezone.timedelta(hours=24)
        remaining_seconds = max(0, (next_scan_time - timezone.now()).total_seconds())

    context = {
        'site': site,
        'filtered_history': filtered_history,
        'remaining_seconds': int(remaining_seconds),
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
    re.compile(r"(Effective date\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),

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

    re.compile(r"(Effective:\s*)([A-Za-z]+\s\d{1,2},\s\d{4})", re.IGNORECASE),
    re.compile(r"(Last updated:\s*)([A-Za-z],\s\d{4})", re.IGNORECASE),
    # Last Updated: 01/24/2024
    re.compile(r"(Last Updated:\s*)(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE),
    re.compile(r"Updated:\s*(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE),
]


def parse_date_from_text(text):
    """
    Searches for 'Last Updated' or 'Updated' date in the provided text and returns it as a datetime.date object.
    """
    text = text.strip()
    print("Text being parsed for date:\n", repr(text))  # Debugging step

    for line in text.splitlines():
        line = line.strip()
        print("Checking line:", repr(line))  # Debug each line

        for pattern in last_updated_patterns:
            match = pattern.search(line)
            if match:
                date_str = match.group(1)  # Extract only the date part
                print(f"Match found: {date_str}")  # Debugging step

                # Parse the date string
                try:
                    parsed_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                    print(f"Parsed Date: {parsed_date}")
                    return parsed_date
                except ValueError as e:
                    print(f"Error parsing date: {e}")

    print("No date found.")
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
    Finds the most relevant link on the page matching the given keywords.
    :param driver: Selenium WebDriver instance
    :param keywords: List of keywords to search in the links
    :return: URL of the matching link or None if not found
    """
    links = driver.find_elements(By.TAG_NAME, "a")  # Get all anchor tags
    candidate_links = []

    for link in links:
        href = link.get_attribute("href")
        text = link.text.lower()
        if href:
            # Check if any keyword matches the visible link text
            if any(keyword.lower() in text for keyword in keywords):
                candidate_links.append((text, href))

            # Check if any keyword matches the URL itself
            elif any(keyword.lower() in href.lower() for keyword in keywords):
                candidate_links.append((text, href))

    # Sort links by relevance (e.g., prefer "terms and conditions" over "executive terms")
    candidate_links.sort(key=lambda x: sum(keyword.lower() in x[0] for keyword in keywords), reverse=True)

    # Return the most relevant link
    return candidate_links[0][1] if candidate_links else None


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

@login_required
def scan_url_view(request, site_id):
    # Fetch the TrackedSite instance based on site_id
    site = get_object_or_404(TrackedSite, id=site_id)

    # Get the URL from the selected TrackedSite instance
    url = site.url

    service = Service('/usr/bin/chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Extract Privacy Policy
        privacy_policy_keywords = ["privacy policy", "privacy notice", "privacy", "privacy note"]
        privacy_policy_text = navigate_and_extract(driver, url, privacy_policy_keywords)

        # Extract Terms of Service
        terms_of_service_keywords = ["terms of service", "terms and conditions", "terms of use", "conditions of use", "terms"]
        terms_of_service_text = navigate_and_extract(driver, url, terms_of_service_keywords)

        # Summarize Texts
        privacy_policy_summary = summary_gpt(privacy_policy_text) if privacy_policy_text else "No summary available."
        terms_of_service_summary = summary_gpt(terms_of_service_text) if terms_of_service_text else "No summary available."

        # Extract "Last updated" date from Privacy Policy
        privacy_policy_last_updated = parse_date_from_text(privacy_policy_summary or "")
        terms_of_service_last_updated = parse_date_from_text(terms_of_service_summary or "")

        # Check and add policy to history if there's a change
        if privacy_policy_text and (privacy_policy_text != site.privacy_policy_extracted or 
                                    (privacy_policy_last_updated and 
                                    privacy_policy_last_updated != site.privacy_policy_last_updated)):

            site.add_policy_to_history(
                new_policy=privacy_policy_text,
                new_summary=privacy_policy_summary,
                new_date=privacy_policy_last_updated or timezone.now().date()
            )

        # Update model fields
        site.privacy_policy_extracted = privacy_policy_text
        site.privacy_policy_summary = privacy_policy_summary
        site.terms_of_service_extracted = terms_of_service_text
        site.terms_of_service_summary = terms_of_service_summary

        # Update timestamps
        site.last_checked = timezone.now()
        site.privacy_policy_last_updated = privacy_policy_last_updated or site.privacy_policy_last_updated
        site.terms_of_service_last_updated = terms_of_service_last_updated or site.terms_of_service_last_updated

        site.save()

    except Exception as e:
        print(f"Error during Selenium operation: {e}")
        Notification.objects.create(
            user=request.user,
            message=f"Failed to complete the scan for {site.title} due to an error.",
        )
    finally:
        driver.quit()

    # Determine message for notification
    if (privacy_policy_text == site.privacy_policy_extracted and 
        (not privacy_policy_last_updated or privacy_policy_last_updated == site.privacy_policy_last_updated)) and \
        (terms_of_service_text == site.terms_of_service_extracted and 
        (not terms_of_service_last_updated or terms_of_service_last_updated == site.terms_of_service_last_updated)):
        notification_message = f"No updates detected for the site: {site.title}."
    else:
        notification_message = f"Updates detected for the site: {site.title}."

    # Add a notification for the user
    Notification.objects.create(
        user=request.user,
        message=notification_message,
    )

    return redirect('dashboard')  # Assuming 'dashboard' is the name of your dashboard URL


def add_policy_to_history(self, new_policy, new_summary, new_date):
    self.refresh_from_db()

    # Ensure new_date is a date object
    if isinstance(new_date, str):
        new_date = datetime.strptime(new_date, "%Y-%m-%d").date()

    if not self.privacy_policy_history:
        self.privacy_policy_history = []

    last_entry = self.privacy_policy_history[-1] if self.privacy_policy_history else {}
    last_date = last_entry.get("date")
    last_policy = last_entry.get("privacy_policy_extracted")

    if new_date.strftime('%Y-%m-%d') != last_date or new_policy.strip() != (last_policy or "").strip():
        history_entry = {
            "date": new_date.strftime('%Y-%m-%d'),
            "privacy_policy_extracted": new_policy.strip(),
            "privacy_policy_summary": new_summary.strip(),
        }
        with transaction.atomic():
            self.privacy_policy_history.append(history_entry)
            self.save()



@login_required
def mark_notification_as_read(request, notification_id):
    if request.method == "POST":
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True  # Update is_read field
            notification.save()
            return JsonResponse({"status": "success"})
        except Notification.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Notification not found"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

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




