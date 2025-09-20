# file: sidebar.py
import sys, subprocess, os, signal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QThread, pyqtSignal, QTimer

def ask_phi(prompt: str) -> str:
    """Optimized LLaMA wrapper with better performance settings"""
    env = os.environ.copy()
    env["OLLAMA_NUM_THREADS"] = "6"  # Use 6 threads (leave 2 for system)
    env["OLLAMA_KEEP_ALIVE"] = "30m"  # Keep model loaded much longer
    
    # Don't limit response length - let the model respond fully
    # env["OLLAMA_NUM_PREDICT"] = "256"  # Removed this limit
    
    # Truncate very long prompts to avoid timeouts
    if len(prompt) > 1000:  # Increased limit since model is faster
        prompt = prompt[:1000] + "..."
    
    try:
        # Add debug info
        print(f"DEBUG: Sending prompt to llama3.2:1b: {prompt[:50]}...")
        
        process = subprocess.run(
            ["ollama", "run", "llama3.2:1b"],
            input=prompt.encode('utf-8'),
            capture_output=True,
            env=env,
            timeout=45  # Increased timeout slightly for safety
        )
        
        print(f"DEBUG: Process return code: {process.returncode}")
        
        if process.returncode == 0:
            response = process.stdout.decode('utf-8').strip()
            print(f"DEBUG: Raw response length: {len(response)}")
            print(f"DEBUG: Response preview: {response[:100]}...")
            
            if response:
                return response
            else:
                return "⚠️ Model returned empty response. Try rephrasing your question."
        else:
            # Check if stderr has useful info
            error_msg = process.stderr.decode('utf-8').strip() if process.stderr else "Unknown error"
            print(f"DEBUG: Error message: {error_msg}")
            return f"⚠️ Model error: {error_msg[:200]}..."
            
    except subprocess.TimeoutExpired:
        print("DEBUG: Process timed out")
        return "⚠️ Response took too long. The model might be loading - try again in a moment."
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return f"❌ Error connecting to Ollama: {str(e)[:200]}..."

class LlamaWorker(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
    
    def run(self):
        print(f"DEBUG: Worker thread starting for prompt: {self.prompt[:50]}...")
        response = ask_phi(self.prompt)
        print(f"DEBUG: Worker got response, emitting: {response[:50]}...")
        self.response_ready.emit(response)

class AssistantSidebar(QWidget):
    def __init__(self):
        super().__init__()
        
        # Window setup - simplified flags to allow proper focus
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Allow proper focus for typing
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()  # Modern Qt5 way
        sidebar_width = 380
        sidebar_height = screen.height() - 80
        
        # Start off-screen (left)
        self.setGeometry(-sidebar_width - 50, 40, sidebar_width, sidebar_height)
        
        # Styling - matching your wallpaper's blue mountain aesthetic
        self.setStyleSheet("""
                QWidget {
                background-color: #151a27;
                color: #e2e8f0;
                font-family: 'JetBrains Mono', 'SF Mono', monospace;
                font-size: 17px;
                border: 2px solid #44546f;
                border-radius: 14px;
            }

            QTextEdit {
                background-color: #1d2433;
                border: 1px solid #374259;
                border-radius: 10px;
                padding: 20px;
                font-size: 17px;
                color: #e2e8f0;
                line-height: 1.6;
                selection-background-color: #5f7e97;
            }

            QLineEdit {
                background-color: #222b3b;
                border: 2px solid #3e4c63;
                border-radius: 10px;
                padding: 14px 18px;
                font-size: 17px;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 2px solid #5f7e97;
                background-color: #1c2230;
            }

            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #6d8aa5, stop:1 #5f7e97);
                border: none;
                border-radius: 10px;
                padding: 14px 26px;
                font-size: 16px;
                font-weight: 600;
                color: #151a27;
            }
            QPushButton:hover {
                background: #7b97b2;
            }
            QPushButton:pressed {
                background: #4d6b80;
            }
            QPushButton:disabled {
                background: #3c475b;
                color: #7a8599;
            }

            QScrollBar:vertical {
                background: #1d2433;
                width: 10px;
                margin: 4px 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #5f7e97;
                border-radius: 5px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7a97b3;
            }

        """)
        
        # Layout - no header, just clean chat interface
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Just the chat area and input - no header
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setHtml("""
        <div style='text-align: center; padding: 20px 0; color: #5f7e97;'>
            <div style='font-weight: bold; font-size: 20px; margin-bottom: 10px;'>
                AI Assistant
            </div>
            <div style='color: #a0aec0; font-size: 15px;'>
                Ready to help with questions and analysis
            </div>
        </div>
        """)
        
        # Input section
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(0, 8, 0, 0)
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your question here...")
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(100)
        
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        
        # Assemble layout - no header
        layout.addWidget(self.chat_area, 1)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        # Connections
        self.send_btn.clicked.connect(self.handle_input)
        self.input_box.returnPressed.connect(self.handle_input)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(250)
        
        # State
        self.worker_thread = None
        self.processing = False  # Flag to prevent duplicate responses
        
        # Force overlay timer - reduced frequency for better performance
        self.overlay_timer = QTimer()
        self.overlay_timer.timeout.connect(self.force_on_top)
        self.overlay_timer.start(1000)  # Changed from 100ms to 1000ms (1 second)
        
        # Auto-slide in on startup
        QTimer.singleShot(100, self.slide_in)
    
    def force_on_top(self):
        """Force window to stay on top"""
        if self.isVisible():
            self.raise_()
            self.activateWindow()
    
    def slide_in(self):
        """Slide in from left edge"""
        screen = QApplication.primaryScreen().geometry()  # Modern Qt5 way
        sidebar_width = 380
        sidebar_height = screen.height() - 80
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        start_pos = QRect(-sidebar_width - 50, 40, sidebar_width, sidebar_height)
        end_pos = QRect(15, 40, sidebar_width, sidebar_height)
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()
        
        # Focus input after animation with more aggressive focus
        def focus_input():
            self.activateWindow()
            self.raise_()
            self.input_box.setFocus()
            self.input_box.grabKeyboard()  # Grab keyboard focus
        
        QTimer.singleShot(500, focus_input)
    
    def close_and_exit(self):
        """Close sidebar and exit application"""
        screen = QApplication.primaryScreen().geometry()  # Modern Qt5 way
        sidebar_width = 380
        sidebar_height = screen.height() - 80
        
        # Stop overlay timer
        self.overlay_timer.stop()
        
        # Slide out animation
        start_pos = QRect(15, 40, sidebar_width, sidebar_height)
        end_pos = QRect(-sidebar_width - 50, 40, sidebar_width, sidebar_height)
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(QApplication.quit)  # Exit after animation
        self.animation.start()
    
    def handle_input(self):
        query = self.input_box.text().strip()
        if not query:
            return
        
        # Prevent multiple requests
        if self.processing:
            return
        
        # Add user message with bigger fonts and mountain theme colors
        self.chat_area.append(f"""
        <div style='margin: 12px 0; padding: 12px; background-color: #2d3748; border-radius: 10px; border-left: 4px solid #5f7e97;'>
            <b style='color: #a0aec0; font-size: 15px;'>You:</b> 
            <span style='color: #d6deeb; font-size: 15px;'>{query}</span>
        </div>
        """)
        self.input_box.clear()
        
        # Show thinking with better styling
        self.chat_area.append("""
        <div style='margin: 12px 0; padding: 12px; background-color: #21283b; border: 1px solid #4a5568; border-radius: 10px;'>
            <i style='color: #a0aec0; font-size: 15px;'>🤔 Processing your request...</i>
        </div>
        """)
        
        self.send_btn.setEnabled(False)
        self.send_btn.setText("...")
        self.processing = True  # Set processing flag
        
        # Clean up previous thread if exists
        if self.worker_thread:
            try:
                self.worker_thread.response_ready.disconnect()
                self.worker_thread.deleteLater()
            except:
                pass
        
        # Process in background with single connection
        self.worker_thread = LlamaWorker(query)
        self.worker_thread.response_ready.connect(self.handle_response)
        self.worker_thread.start()
    
    def handle_response(self, response):
        """Simple response handling without duplicating history"""
        print(f"DEBUG: handle_response called with: {response[:100]}...")
        print(f"DEBUG: Processing flag is: {self.processing}")
        
        # Prevent duplicate responses - only process if we're currently processing
        if not self.processing:
            print("DEBUG: Not processing, returning early")
            return
            
        # Clear processing flag immediately to prevent duplicates
        self.processing = False
        print("DEBUG: Set processing to False")
        
        # Remove thinking indicator using cursor (simple and reliable)
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        
        print("DEBUG: Removed thinking indicator, adding response to chat")
        
        # Add response with simple append (no history duplication)
        self.chat_area.append(f"""
        <div style='margin: 12px 0; padding: 12px; background-color: #21283b; border: 1px solid #5f7e97; border-radius: 10px; border-left: 4px solid #a0aec0;'>
            <b style='color: #5f7e97; font-size: 15px;'>Assistant:</b><br/>
            <span style='color: #d6deeb; font-size: 15px; line-height: 1.5;'>{response}</span>
        </div>
        """)
        
        print("DEBUG: Response added to chat area")
        
        # Reset button and scroll
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        print("DEBUG: UI reset complete")
        
        # Clean up thread
        if self.worker_thread:
            try:
                self.worker_thread.response_ready.disconnect()
                self.worker_thread.deleteLater()
            except:
                pass
            self.worker_thread = None
        
        print("DEBUG: Thread cleanup complete")
    
    def keyPressEvent(self, event):
        """Handle ESC key to close"""
        if event.key() == Qt.Key_Escape:
            self.close_and_exit()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    pidfile = "/tmp/ai_assistant.pid"
    
    # Check if already running and kill it
    if os.path.exists(pidfile):
        try:
            with open(pidfile, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)  # Use proper signal
            print(f"Killed existing instance (PID: {old_pid})")
        except (OSError, ValueError):
            pass  # Process doesn't exist
        
        # Remove old pidfile
        try:
            os.remove(pidfile)
        except:
            pass
        
        # If we just killed an instance, exit (this creates the toggle effect)
        print("Toggle: Closed existing assistant")
        sys.exit(0)
    
    # No existing instance, start new one
    # Write our PID
    with open(pidfile, 'w') as f:
        f.write(str(os.getpid()))
    
    # Start fresh assistant
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)  # Exit when window closes
    
    sidebar = AssistantSidebar()
    
    # Clean up PID file on exit
    def cleanup():
        try:
            os.remove(pidfile)
        except:
            pass
    
    app.aboutToQuit.connect(cleanup)
    
    print("Started fresh assistant instance")
    sys.exit(app.exec_())