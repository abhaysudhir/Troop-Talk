from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Configure Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Log in to Google
driver.get("https://accounts.google.com")
time.sleep(5)  # Wait for login page
# (You may need to manually log in or use tools like Selenium's `ActionChains` to automate login)

# Navigate to Google Group
group_url = "https://groups.google.com/g/<group-name>/topics"
driver.get(group_url)
time.sleep(5)

# Scrape Emails
emails = []
threads = driver.find_elements(By.CSS_SELECTOR, "a[role='link']")
for thread in threads:
    thread.click()
    time.sleep(2)  # Wait for email to load
    title = driver.find_element(By.CSS_SELECTOR, ".GHwOBb").text
    body = driver.find_element(By.CSS_SELECTOR, ".K8P89e").text
    emails.append({"title": title, "body": body})
    driver.back()
    time.sleep(2)

# Print or Save Data
for email in emails:
    print(f"Title: {email['title']}\nBody: {email['body']}\n")

driver.quit()
