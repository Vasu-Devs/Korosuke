# Korosuke

A personal AI sidebar assistant built with **PyQt5** and [Ollama](https://ollama.ai).  
It provides a sliding sidebar interface, chat-like conversation, and lightweight integration with LLaMA models.

## Features
- Sliding sidebar UI with smooth animations
- Chat interface with styled messages
- Background worker thread for non-blocking AI responses
- Ollama LLaMA integration (`llama3.2:1b`)
- One-click toggle using PID system

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Vasu-Devs/Korosuke.git
cd Korosuke
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Run the sidebar assistant:

bash
Copy code
python sidebar.py
Usage
Type your question in the input box and hit Send or press Enter.

The assistant responds in the chat area.

Press ESC to close the sidebar.

Re-run the script to toggle the sidebar open/close.

Dependencies
Python 3.10+

PyQt5

Ollama installed and configured locally

Contributing
Contributions are welcome!

Fork the repo

Create a new branch (git checkout -b feature-name)

Commit your changes

Open a pull request

License
This project is licensed under the MIT License.