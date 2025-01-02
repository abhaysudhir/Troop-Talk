import os
import email
from email.policy import default
from PyPDF2 import PdfReader
import docx
import openpyxl
from pinecone import Pinecone
from openai import OpenAI

# API keys and configurations
PC_API_KEY = "pcsk_5CwF7M_2c71gSS2ogeQnpVRd3TJWHrj69hJBVGn1uZxNqtbSkgeXXszh6Q2dDpvghvA6sF"  # Replace with your Pinecone API key
PC_ENVIRONMENT = "us-east-1"
OPENAI_API_KEY = "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"  # Replace with your OpenAI API key

# Initialize OpenAI and Pinecone
openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PC_API_KEY, environment=PC_ENVIRONMENT)

# Set up Pinecone index
INDEX_NAME = "boyscout-gpt-t125"
index = pinecone_client.Index(INDEX_NAME)

# Directories for processing
UNCLEANED_DIR = "Uncleaned_Emails"
CLEANED_DIR = "Cleaned_Emails"
os.makedirs(CLEANED_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


# Helper functions for content extraction
def extract_pdf_content(file_path):
    try:
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"


def extract_docx_content(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        return f"Error reading DOCX: {e}"


def extract_xlsx_content(file_path):
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        content = []
        for sheet in wb:
            content.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                content.append("\t".join(str(cell or "") for cell in row))
        return "\n".join(content)
    except Exception as e:
        return f"Error reading XLSX: {e}"


def remove_empty_lines(text):
    return "\n".join(line for line in text.split("\n") if line.strip() != "")


# Function to clean email
def clean_email(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        msg = email.message_from_file(file, policy=default)

    subject = msg.get("Subject", "No Subject")
    sender = msg.get("From", "Unknown Sender")
    date = msg.get("Date", "No Date")
    body = []
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get("Content-Disposition", None)

            if content_type == "text/plain" and (
                not disposition or "attachment" not in disposition
            ):
                try:
                    body.append(
                        part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8"
                        )
                    )
                except Exception as e:
                    body.append(f"Error decoding body part: {e}")
            elif disposition and "attachment" in disposition:
                filename = part.get_filename()
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ALLOWED_EXTENSIONS:
                        temp_path = os.path.join(CLEANED_DIR, filename)
                        with open(temp_path, "wb") as temp_file:
                            temp_file.write(part.get_payload(decode=True))
                        if ext == ".pdf":
                            attachments.append(extract_pdf_content(temp_path))
                        elif ext == ".docx":
                            attachments.append(extract_docx_content(temp_path))
                        elif ext == ".xlsx":
                            attachments.append(extract_xlsx_content(temp_path))
                        os.remove(temp_path)
    else:
        try:
            body.append(
                msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8"
                )
            )
        except Exception as e:
            body.append(f"Error decoding single-part email: {e}")

    cleaned_body = remove_empty_lines("\n".join(body))
    attachments_text = "\n\n".join(attachments)

    return (
        f"Subject: {subject}\nFrom: {sender}\nDate: {date}\n\n{cleaned_body}\n\n{attachments_text}",
        subject,
        sender,
        date,
    )


# Function to generate embeddings
def embed_text(text):
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002", input=text
    )
    return response.data[0].embedding


# Process and upload emails
for filename in os.listdir(UNCLEANED_DIR):
    if filename.endswith(".eml"):
        file_path = os.path.join(UNCLEANED_DIR, filename)
        cleaned_content, subject, sender, date = clean_email(file_path)

        cleaned_file_path = os.path.join(
            CLEANED_DIR, f"{os.path.splitext(filename)[0]}.txt"
        )
        with open(cleaned_file_path, "w", encoding="utf-8") as cleaned_file:
            cleaned_file.write(cleaned_content)

        # Read the cleaned file and upload its content
        with open(cleaned_file_path, "r", encoding="utf-8") as cleaned_file:
            text = cleaned_file.read()

        try:
            embedding = embed_text(text)
            metadata = {"subject": subject, "from": sender, "date": date, "body": text}
            index.upsert([(filename, embedding, metadata)])
            print(f"Uploaded {filename} to Pinecone with metadata.")
        except Exception as e:
            print(f"Error uploading {filename}: {e}")

print("Processing and uploading complete.")
