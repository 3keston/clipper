
# Clipper

<img src="clipper.webp" alt="Clipper Image" width="250" height="250">

Clipper is designed to provide a seamless and intuitive chat experience, leveraging clipboard content to enhance the context and relevance of interactions with a local language model.

The application continuously monitors the system clipboard for new content, detecting both text and image data copied to the clipboard. Upon detecting an image, Clipper 0.1 then includes it in the chat query, enhancing the assistant's ability to provide relevant responses. For text content, it appends the clipboard text to the user's query for a comprehensive interaction.

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/3keston/clipper
   cd clipper
   ```

2. **Create and activate a virtual environment**:
   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

4. **Install Ollama and download the required model**:
   - Visit [Ollama's website](https://ollama.com/) and follow the instructions to install Ollama.
   - Pull the required model:
     ```sh
     ollama pull llava-phi3
     ```

## Usage

After completing the installation steps, you can start the application with the following command:

```sh
python src/main.py
```
