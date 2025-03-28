# Use Python as base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y wget unzip \
    && wget -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./chrome.deb \
    && rm chrome.deb \
    && apt-get install -y fonts-liberation libasound2 libgbm-dev libu2f-udev libvulkan1 libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*  # Clean up

# Install ChromeDriver using webdriver-manager
RUN pip install webdriver-manager


# Run the app
EXPOSE 7861

# Set the command to run your Gradio app using Gunicorn
# Run the app
CMD ["python", "app.py"]

