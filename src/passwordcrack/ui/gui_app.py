"""
Main GUI application for PasswordCrack Suite.

Complete graphical interface with all features.
NOTE: REQUIRES EXPLICIT USER CONSENT - EDUCATIONAL USE ONLY
"""

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import our modules
from ..hash_utils import HashUtils, HashAlgorithm
from ..hash_identifier import HashIdentifier
from ..wordlist_manager import WordlistManager
from ..attack_engines import DictionaryEngine, BruteforceEngine, MaskEngine, HybridEngine, RuleEngine
from ..attack_engines.gpx_engine import GPXDictionaryEngine, GPXBruteforceEngine
from ..session_manager import SessionManager
from ..results_analyzer import ResultsAnalyzer
from ..performance.benchmark import PerformanceBenchmark
from ..security import SecurityManager
from ..simulator import DemoSimulator
from ..gpx_manager import GPXManager, DeviceType, DeviceTier
from ..hashcat_wrapper import HashcatWrapper, HashcatMode


class PasswordCrackGUI:
    """Main GUI application class."""
    
    def __init__(self):
        """Initialize the GUI application."""
        self.config_file = Path.cwd() / "config.json"
        self.config: Dict[str, Any] = self.load_config()
        self.consent_given = False
        self.current_session = None
        self.attack_thread: Optional[threading.Thread] = None
        self.attack_running = False
        self.attack_paused = False
        self.attack_result = None
        self.attack_stats = {'attempts': 0, 'speed': 0, 'start_time': None, 'current_candidate': ''}
        self.terminal_buffer = []
        
        # Initialize managers
        self.wordlist_manager = WordlistManager()
        self.session_manager = SessionManager()
        self.results_analyzer = ResultsAnalyzer()
        self.security_manager = SecurityManager()
        self.simulator = DemoSimulator()
        
        # Initialize GPX (GPU/CPU acceleration)
        self.gpx_manager = GPXManager()
        self.hashcat_wrapper: Optional[HashcatWrapper] = None
        self.gpx_enabled = False
        self.gpx_devices_detected = False
        
        # Try to initialize GPX
        try:
            self.gpx_manager.detect_devices()
            self.gpx_devices_detected = True
            
            # Always create hashcat wrapper (it won't raise error anymore)
            self.hashcat_wrapper = HashcatWrapper(self.gpx_manager)
            
            if self.hashcat_wrapper.hashcat_path:
                print(f"✅ Hashcat found: {self.hashcat_wrapper.hashcat_path}")
                if self.gpx_manager.is_gpu_available():
                    self.gpx_enabled = True  # Default to ON if GPU available
            else:
                print(f"⚠️ Hashcat not found - GPU acceleration disabled")
                
        except Exception as e:
            print(f"GPX initialization warning: {e}")
            import traceback
            traceback.print_exc()
        
        # Set theme
        sg.theme('DarkBlue3')
    
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self) -> None:
        """Save application configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def show_consent_screen(self) -> bool:
        """
        Show ethics and consent screen.
        
        Returns:
            True if user consents, False otherwise
        """
        layout = [
            [sg.Text("⚠️  ETHICAL USE AGREEMENT ⚠️", font=("Arial", 16, "bold"), justification='center')],
            [sg.HorizontalSeparator()],
            [sg.Multiline(
                "EDUCATIONAL USE ONLY - READ CAREFULLY\n\n"
                "This tool is designed EXCLUSIVELY for:\n"
                "• Learning about password security and hashing\n"
                "• Testing passwords on systems YOU OWN\n"
                "• Authorized security research and training\n"
                "• Educational demonstrations\n\n"
                "You MUST NOT use this tool to:\n"
                "• Attack systems you don't own or have permission to test\n"
                "• Violate any laws or regulations\n"
                "• Conduct unauthorized access attempts\n"
                "• Harm others or violate their privacy\n\n"
                "By checking the box below, you acknowledge that:\n"
                "• You will only use this tool ethically and legally\n"
                "• You have permission for any testing you perform\n"
                "• You accept full responsibility for your actions\n"
                "• The authors are not liable for misuse\n\n"
                "Violation of these terms may result in criminal prosecution.",
                size=(70, 20),
                disabled=True,
                font=("Arial", 10)
            )],
            [sg.Checkbox("I understand and agree to use this tool ethically and legally", 
                        key='-CONSENT-', font=("Arial", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Button("Accept & Continue", size=(20, 1), button_color=('white', 'green')),
             sg.Button("Decline & Exit", size=(20, 1), button_color=('white', 'red'))]
        ]
        
        window = sg.Window("Ethical Use Agreement - PasswordCrack Suite", 
                          layout, modal=True, finalize=True)
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, "Decline & Exit"):
                window.close()
                return False
            
            if event == "Accept & Continue":
                if values['-CONSENT-']:
                    window.close()
                    return True
                else:
                    sg.popup_error("You must check the consent box to continue.",
                                  title="Consent Required")
        
        window.close()
        return False
    
    def show_metadata_prompt(self) -> bool:
        """
        Show first-run metadata collection screen.
        
        Returns:
            True if completed, False if cancelled
        """
        if 'project_name' in self.config:
            return True  # Already configured
        
        layout = [
            [sg.Text("📝 Project Configuration", font=("Arial", 14, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text("Please provide some information about your use of this tool:")],
            [sg.Text("")],
            [sg.Text("Project/Repo Name:", size=(20, 1)), 
             sg.Input("PasswordCrack-Suite", key='-PROJECT-', size=(40, 1))],
            [sg.Text("GitHub Repository:", size=(20, 1)), 
             sg.Input("", key='-REPO-', size=(40, 1))],
            [sg.Text("Author Name:", size=(20, 1)), 
             sg.Input("", key='-AUTHOR-', size=(40, 1))],
            [sg.Text("Copyright Year:", size=(20, 1)), 
             sg.Input(str(datetime.now().year), key='-YEAR-', size=(40, 1))],
            [sg.Text("License:", size=(20, 1)), 
             sg.Combo(['Educational Use Only', 'MIT', 'Apache-2.0'], 
                     default_value='Educational Use Only', key='-LICENSE-', size=(38, 1))],
            [sg.Text("Description:", size=(20, 1)), 
             sg.Input("Educational password security research tool", key='-DESC-', size=(40, 1))],
            [sg.Text("")],
            [sg.Button("Save & Continue", size=(15, 1)), sg.Button("Skip", size=(15, 1))]
        ]
        
        window = sg.Window("First Run Configuration", layout, modal=True)
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, "Skip"):
                window.close()
                return True
            
            if event == "Save & Continue":
                self.config = {
                    'project_name': values['-PROJECT-'],
                    'repo_url': values['-REPO-'],
                    'author': values['-AUTHOR-'],
                    'copyright_year': values['-YEAR-'],
                    'license': values['-LICENSE-'],
                    'description': values['-DESC-'],
                    'first_run_completed': True
                }
                self.save_config()
                window.close()
                return True
        
        return False
    
    def create_main_window(self) -> sg.Window:
        """Create the main application window."""
        
        # Build GPX device summary
        gpx_device_text = self.gpx_manager.get_device_summary() if self.gpx_devices_detected else "Scanning devices..."
        gpx_enabled_default = self.gpx_enabled and self.gpx_manager.is_gpu_available()
        
        # Main layout with tabs
        tab_new_session = [
            [sg.Text("Create New Cracking Session", font=("Arial", 12, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text("Target Hash:", size=(15, 1)), 
             sg.Input(key='-HASH-', size=(60, 1))],
            [sg.Text("Hash Algorithm:", size=(15, 1)), 
             sg.Combo(['MD5', 'SHA1', 'SHA256', 'SHA512'], 
                     default_value='SHA256', key='-ALGO-', size=(20, 1)),
             sg.Button("Auto-Detect", key='-DETECT-'),
             sg.Button("Create Hash", key='-CREATE_HASH-')],
            [sg.HorizontalSeparator()],
            [sg.Text("GPU/CPU Acceleration (GPX):", font=("Arial", 10, "bold"))],
            [sg.Checkbox("Use GPU if available", key='-GPX_ENABLED-', default=gpx_enabled_default,
                        tooltip="GPX = Use GPU acceleration (OpenCL/CUDA). Falls back to CPU if no GPU found.",
                        disabled=not self.gpx_manager.is_gpu_available()),
             sg.Button("Benchmark", key='-BENCHMARK-', size=(12, 1),
                      tooltip="Run a short benchmark to measure GPU/CPU speed"),
             sg.Button("Rescan Devices", key='-RESCAN_DEVICES-', size=(12, 1),
                      tooltip="Re-detect available GPU/CPU devices"),
             sg.Button("Diagnostics", key='-GPX_DIAGNOSTICS-', size=(12, 1),
                      tooltip="Show detailed GPU/CPU detection diagnostics")],
            [sg.Text(gpx_device_text, key='-GPX_DEVICE_INFO-', size=(70, 1), 
                    text_color='black' if self.gpx_manager.is_gpu_available() else 'gray')],
            [sg.Text("Estimated Speed: N/A", key='-GPX_SPEED_EST-', size=(70, 1), visible=False)],
            [sg.Checkbox("Allow CPU + GPU mixed mode", key='-GPX_MIXED-', default=True,
                        tooltip="Use both CPU and GPU together (if supported by hash algorithm)")],
            [sg.HorizontalSeparator()],
            [sg.Text("Attack Type:", font=("Arial", 10, "bold"))],
            [sg.Radio("Dictionary Attack (Fast - tries common passwords)", "ATTACK", key='-DICT-', default=True)],
            [sg.Radio("Brute-Force Attack (Slow - tries all combinations)", "ATTACK", key='-BRUTE-')],
            [sg.HorizontalSeparator()],
            [sg.Text("Wordlist (for Dictionary):", size=(25, 1)), 
             sg.Combo([
                 '*** TRY ALL WORDLISTS ***',
                 'wordlists/common.txt',
                 'wordlists/rockyou-lite.txt',
                 'SecLists/Passwords/Common-Credentials/10k-most-common.txt',
                 'SecLists/Passwords/Common-Credentials/100k-most-used-passwords-NCSC.txt',
                 'SecLists/Passwords/Common-Credentials/best1050.txt',
                 'SecLists/Passwords/Common-Credentials/best110.txt',
                 'SecLists/Passwords/Common-Credentials/500-worst-passwords.txt',
                 'SecLists/Passwords/darkc0de.txt',
                 'SecLists/Passwords/Common-Credentials/darkweb2017_top-10000.txt'
             ], default_value='SecLists/Passwords/Common-Credentials/best110.txt', 
             key='-WORDLIST-', size=(60, 1))],
            [sg.HorizontalSeparator()],
            [sg.Button("Start Attack", size=(15, 1), button_color=('white', 'green')),
             sg.Button("Clear", size=(15, 1))]
        ]
        
        tab_progress = [
            [sg.Text("Session Progress", font=("Arial", 12, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text("Status:", size=(15, 1)), sg.Text("Ready", key='-STATUS-', size=(40, 1))],
            [sg.Text("Attempts:", size=(15, 1)), sg.Text("0", key='-ATTEMPTS-', size=(40, 1))],
            [sg.Text("Speed:", size=(15, 1)), sg.Text("0 H/s", key='-SPEED-', size=(40, 1))],
            [sg.Text("Estimated Time:", size=(15, 1)), sg.Text("N/A", key='-ETA-', size=(40, 1))],
            [sg.ProgressBar(100, orientation='h', size=(50, 20), key='-PROGRESS-')],
            [sg.HorizontalSeparator()],
            [sg.Multiline("", size=(70, 8), key='-LOG-', autoscroll=True, disabled=True)],
            [sg.HorizontalSeparator()],
            [sg.Text("Real-Time Cracking Terminal:", font=("Arial", 10, "bold"))],
            [sg.Multiline("", size=(70, 8), key='-TERMINAL-', autoscroll=True, disabled=True,
                         font=("Courier", 9), text_color='lime', background_color='black')],
            [sg.HorizontalSeparator()],
            [sg.Button("Pause", size=(12, 1), key='-PAUSE-'),
             sg.Button("Resume", size=(12, 1), key='-RESUME-', disabled=True),
             sg.Button("Stop", size=(12, 1), key='-STOP-', button_color=('white', 'red')),
             sg.Button("Clear Data", size=(12, 1), key='-CLEAR_DATA-', button_color=('white', 'orange'))]
        ]
        
        tab_results = [
            [sg.Text("Session Results", font=("Arial", 12, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text("Password Found:", size=(20, 1), font=("Arial", 10, "bold")), 
             sg.Text("N/A", key='-RESULT_PWD-', size=(40, 1), font=("Arial", 10))],
            [sg.Text("Total Attempts:", size=(20, 1)), sg.Text("0", key='-RESULT_ATTEMPTS-')],
            [sg.Text("Duration:", size=(20, 1)), sg.Text("0s", key='-RESULT_DURATION-')],
            [sg.Text("Success:", size=(20, 1)), sg.Text("No", key='-RESULT_SUCCESS-')],
            [sg.HorizontalSeparator()],
            [sg.Text("Generate Report:")],
            [sg.Button("JSON Report", size=(15, 1)),
             sg.Button("HTML Report", size=(15, 1)),
             sg.Button("TXT Report", size=(15, 1))],
            [sg.HorizontalSeparator()],
            [sg.Multiline("", size=(70, 12), key='-RESULT_DETAILS-', disabled=True)]
        ]
        
        layout = [
            [sg.Text("🔐 PasswordCrack Suite - Educational Password Security Tool", 
                    font=("Arial", 14, "bold"), justification='center', expand_x=True)],
            [sg.HorizontalSeparator()],
            [sg.TabGroup([
                [sg.Tab("New Session", tab_new_session),
                 sg.Tab("Progress", tab_progress),
                 sg.Tab("Results", tab_results)]
            ])],
            [sg.HorizontalSeparator()],
            [sg.Text("Ready", key='-STATUSBAR-', size=(60, 1)),
             sg.Text(f"Project: {self.config.get('project_name', 'PasswordCrack-Suite')}", 
                    justification='right', expand_x=True)]
        ]
        
        return sg.Window("PasswordCrack Suite", layout, size=(800, 700), finalize=True)
    
    def log_message(self, window: sg.Window, message: str) -> None:
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        window['-LOG-'].print(f"[{timestamp}] {message}")
    
    def run(self) -> None:
        """Run the main application."""
        # Show consent screen
        if not self.show_consent_screen():
            return
        
        self.consent_given = True
        
        # Show metadata prompt on first run
        if not self.show_metadata_prompt():
            return
        
        # Create main window
        window = self.create_main_window()
        
        # Event loop
        while True:
            event, values = window.read(timeout=100)
            
            if event in (sg.WIN_CLOSED, 'Exit'):
                if self.attack_running:
                    self.attack_running = False
                    if self.attack_thread:
                        self.attack_thread.join(timeout=2)
                break
            
            # Update progress if attack is running OR if there's a result to show
            if self.attack_running or self.attack_result:
                self.update_progress(window)
            
            # Handle events
            if event == '-DETECT-':
                self.handle_hash_detection(window, values)
            elif event == '-CREATE_HASH-':
                self.show_hash_generator()
            elif event == '-BENCHMARK-':
                self.handle_gpx_benchmark(window, values)
            elif event == '-RESCAN_DEVICES-':
                self.handle_gpx_rescan(window)
            elif event == '-GPX_DIAGNOSTICS-':
                self.handle_gpx_diagnostics(window)
            elif event == 'Start Attack':
                self.handle_start_attack(window, values)
            elif event == '-STOP-':
                self.handle_stop_attack(window)
            elif event == '-PAUSE-':
                self.handle_pause_attack(window)
            elif event == '-RESUME-':
                self.handle_resume_attack(window)
            elif event == '-CLEAR_DATA-':
                self.handle_clear_data(window)
            elif event == 'Clear':
                self.handle_clear_form(window)
            elif event == 'Hash Generator':
                self.show_hash_generator()
            elif event == 'Benchmark':
                self.show_benchmark()
            elif event == 'Quick Demo':
                self.run_quick_demo(window)
            elif event == 'About':
                self.show_about()
            elif event in ['JSON Report', 'HTML Report', 'TXT Report']:
                self.handle_generate_report(window, event)
        
        window.close()
    
    def handle_hash_detection(self, window: sg.Window, values: Dict) -> None:
        """Handle auto-detect hash type."""
        hash_value = values['-HASH-'].strip()
        if not hash_value:
            sg.popup_error("Please enter a hash first.")
            return
        
        detected = HashIdentifier.identify_with_details(hash_value)
        if detected:
            algo_name = detected[0]['name'].upper()
            window['-ALGO-'].update(algo_name)
            sg.popup(f"Detected: {detected[0]['description']}", title="Hash Detected")
        else:
            sg.popup_error("Could not detect hash type.")
    
    def _run_attack(self, hash_value: str, algorithm: HashAlgorithm, attack_type: str, values: Dict) -> None:
        """Run the attack in a background thread."""
        import time
        
        # ✅ VALIDATION: Check hash format before starting attack
        is_valid, error_msg = HashUtils.validate_hash(hash_value, algorithm)
        if not is_valid:
            self.terminal_buffer.append(f"❌ INVALID HASH: {error_msg}")
            self.terminal_buffer.append(f"Hash entered: {hash_value}")
            self.terminal_buffer.append(f"Example valid {algorithm.value.upper()} hash:")
            
            # Show example for the algorithm
            examples = {
                HashAlgorithm.MD5: "5f4dcc3b5aa765d61d8327deb882cf99 (password: 'password')",
                HashAlgorithm.SHA1: "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8 (password: 'password')",
                HashAlgorithm.SHA256: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8 (password: 'password')",
                HashAlgorithm.SHA512: "b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86 (password: 'password')",
                HashAlgorithm.NTLM: "8846f7eaee8fb117ad06bdd830b7586c (password: 'password')"
            }
            self.terminal_buffer.append(f"  {examples.get(algorithm, 'N/A')}")
            self.terminal_buffer.append("="*50)
            self.window['-OUTPUT-'].update('\n'.join(self.terminal_buffer[-100:]))
            self.window['-CRACK-'].update(disabled=False)
            return
        
        print(f"DEBUG: _run_attack started! Type: {attack_type}, Algorithm: {algorithm.value.upper()}, Hash: {hash_value[:16]}...")
        self.terminal_buffer.append(f">>> ATTACK STARTED: {attack_type.upper()} <<<")
        self.terminal_buffer.append(f"Algorithm: {algorithm.value.upper()}")
        self.terminal_buffer.append(f"Target Hash: {hash_value[:32]}...")
        self.terminal_buffer.append("="*50)
        
        # ✅ ROOT CAUSE FIX: Check if GPX is enabled
        gpx_enabled = values.get('-GPX_ENABLED-', False)
        gpx_mixed = values.get('-GPX_MIXED-', True)
        
        # Debug: Show what we detected
        print(f"DEBUG: GPX checkbox value: {gpx_enabled}")
        print(f"DEBUG: Hashcat wrapper exists: {self.hashcat_wrapper is not None}")
        if self.hashcat_wrapper:
            print(f"DEBUG: Hashcat path: {self.hashcat_wrapper.hashcat_path}")
        print(f"DEBUG: GPU available: {self.gpx_manager.is_gpu_available()}")
        
        # Determine execution mode
        use_gpx = (gpx_enabled and 
                   self.hashcat_wrapper is not None and 
                   self.hashcat_wrapper.hashcat_path is not None and 
                   self.gpx_manager.is_gpu_available())
        
        print(f"DEBUG: Final use_gpx decision: {use_gpx}")
        
        # Show hashcat warning if GPU enabled but hashcat missing
        if gpx_enabled and (not self.hashcat_wrapper or not self.hashcat_wrapper.hashcat_path):
            self.terminal_buffer.append("⚠️ GPU ACCELERATION REQUESTED BUT HASHCAT NOT FOUND")
            self.terminal_buffer.append("⚠️ Please install hashcat from: https://hashcat.net/hashcat/")
            self.terminal_buffer.append("⚠️ See HASHCAT_INSTALL_GUIDE.md for instructions")
            self.terminal_buffer.append("⚠️ Falling back to CPU mode...")
            self.terminal_buffer.append("="*50)
            # Note: Cannot show popup from thread, message shown in terminal instead
        
        if use_gpx:
            device_info = self.gpx_manager.get_device_summary()
            self.terminal_buffer.append(f"🚀 GPU ACCELERATION ENABLED")
            self.terminal_buffer.append(f"Device: {device_info}")
            self.terminal_buffer.append(f"Mixed Mode: {'ON' if gpx_mixed else 'OFF'}")
            self.terminal_buffer.append("="*50)
            print(f"DEBUG: Using GPU acceleration - {device_info}")
            
            # Route to GPU-accelerated attack
            self._run_gpx_attack(hash_value, algorithm, attack_type, values, gpx_mixed)
        else:
            # Use CPU-only mode
            if gpx_enabled and not self.gpx_manager.is_gpu_available():
                self.terminal_buffer.append(f"⚠️ GPU requested but not available")
            self.terminal_buffer.append(f"💻 CPU MODE")
            self.terminal_buffer.append("="*50)
            self._run_cpu_attack(hash_value, algorithm, attack_type, values)
            print(f"DEBUG: Using CPU-only mode")
            self._run_cpu_attack(hash_value, algorithm, attack_type, values)
    
    def _run_gpx_attack(self, hash_value: str, algorithm: HashAlgorithm, attack_type: str, values: Dict, mixed_mode: bool) -> None:
        """Run GPU-accelerated attack using GPX engines."""
        import time
        
        try:
            if attack_type == 'dictionary':
                print(f"DEBUG: Starting GPX dictionary attack")
                
                # Create GPX dictionary engine
                engine = GPXDictionaryEngine(
                    hash_value=hash_value,
                    algorithm=algorithm,
                    gpx_manager=self.gpx_manager,
                    hashcat_wrapper=self.hashcat_wrapper
                )
                
                # Get wordlist(s)
                if values['-WORDLIST-'] == '*** TRY ALL WORDLISTS ***':
                    wordlists = [
                        'wordlists/common.txt',
                        'wordlists/rockyou-lite.txt',
                        'SecLists/Passwords/Common-Credentials/best110.txt',
                        'SecLists/Passwords/Common-Credentials/best1050.txt',
                        'SecLists/Passwords/Common-Credentials/10k-most-common.txt',
                        'SecLists/Passwords/Common-Credentials/100k-most-used-passwords-NCSC.txt',
                        'SecLists/Passwords/darkc0de.txt'
                    ]
                    self.terminal_buffer.append(">>> TRYING ALL WORDLISTS (GPU MODE) <<<")
                else:
                    wordlists = [values['-WORDLIST-']]
                
                total_attempts = 0
                
                # Try each wordlist with GPU
                for wordlist_name in wordlists:
                    if not self.attack_running:
                        break
                    
                    self.terminal_buffer.append(f"\n=== GPU Processing: {wordlist_name.split('/')[-1]} ===")
                    print(f"DEBUG: GPU processing wordlist: {wordlist_name}")
                    
                    try:
                        # Run GPU-accelerated dictionary attack
                        result = engine.attack(
                            wordlist_file=wordlist_name,
                            wordlist_manager=self.wordlist_manager,
                            use_gpu=True,
                            mixed_mode=mixed_mode,
                            progress_callback=None  # Hashcat provides its own progress
                        )
                        
                        total_attempts += engine.attempts
                        self.attack_stats['attempts'] = total_attempts
                        
                        if result:
                            # PASSWORD FOUND!
                            print(f"DEBUG: GPX found password: {result}")
                            self.terminal_buffer.append("")
                            self.terminal_buffer.append("=" * 50)
                            self.terminal_buffer.append(f"🎉 PASSWORD FOUND (GPU): {result}")
                            self.terminal_buffer.append("=" * 50)
                            
                            self.attack_result = {
                                'success': True,
                                'password': result,
                                'attempts': total_attempts,
                                'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds()
                            }
                            self.attack_running = False
                            time.sleep(0.2)
                            return
                    
                    except Exception as e:
                        print(f"DEBUG: GPX wordlist failed: {e}")
                        self.terminal_buffer.append(f"⚠️ GPU error for {wordlist_name}: {e}")
                        continue
                
                # No match found
                self.attack_result = {
                    'success': False,
                    'password': None,
                    'attempts': total_attempts,
                    'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds(),
                    'error': f'❌ Password not found (GPU mode) - tried {total_attempts:,} passwords'
                }
            
            elif attack_type == 'bruteforce':
                print(f"DEBUG: Starting GPX brute-force attack")
                
                # Mark as GPU attack in stats for pause/stop handling
                self.attack_stats['use_gpu'] = True
                
                self.terminal_buffer.append(f"🔥 GPU BRUTE-FORCE ATTACK")
                self.terminal_buffer.append(f"Mode: Incremental (starts at length 1, continues until found)")
                self.terminal_buffer.append(f"Charset: All printable (a-zA-Z0-9 + symbols)")
                self.terminal_buffer.append(f"Max length: 16 characters (can take hours/days for long passwords!)")
                self.terminal_buffer.append(f"⚠️ This uses 100% GPU power - will run until password found")
                self.terminal_buffer.append("="*50)
                
                # Create GPX brute-force engine
                engine = GPXBruteforceEngine(
                    hash_value=hash_value,
                    algorithm=algorithm,
                    gpx_manager=self.gpx_manager,
                    hashcat_wrapper=self.hashcat_wrapper
                )
                
                # Progress callback to show real-time attempts
                last_update = [0]  # Use list to modify in nested function
                
                def progress_callback(update):
                    """Handle real-time hashcat progress updates"""
                    try:
                        if update['type'] == 'candidate':
                            # Show candidate range being tried
                            candidate_info = update['info']
                            self.terminal_buffer.append(f"🔍 Trying: {candidate_info}")
                            # Keep buffer size reasonable
                            if len(self.terminal_buffer) > 100:
                                self.terminal_buffer.pop(0)
                            # Update stats
                            self.attack_stats['current_candidate'] = candidate_info
                            print(f"DEBUG: Showing candidate: {candidate_info}")
                            import sys
                            sys.stdout.flush()
                        
                        elif update['type'] == 'progress':
                            # Show progress stats (every update)
                            attempts = update.get('attempts', 0)
                            total = update.get('total', 0)
                            speed = update.get('speed', 0)
                            
                            # Update attack stats ALWAYS
                            self.attack_stats['attempts'] = attempts
                            
                            # Update terminal more frequently (every 50k attempts)
                            if attempts - last_update[0] >= 50000 or attempts < 100000:
                                if speed >= 1000000:
                                    speed_str = f"{speed/1000000:.2f} MH/s"
                                elif speed >= 1000:
                                    speed_str = f"{speed/1000:.1f} kH/s"
                                else:
                                    speed_str = f"{speed:.0f} H/s"
                                
                                percent = (attempts / total * 100) if total > 0 else 0
                                self.terminal_buffer.append(f"⚡ Progress: {attempts:,}/{total:,} ({percent:.1f}%) @ {speed_str}")
                                if len(self.terminal_buffer) > 100:
                                    self.terminal_buffer.pop(0)
                                last_update[0] = attempts
                                print(f"DEBUG: Progress update: {attempts:,} attempts @ {speed_str}")
                                import sys
                                sys.stdout.flush()
                    except Exception as e:
                        print(f"DEBUG: Progress callback error: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Run GPU brute-force with incremental mode and real-time progress
                # Mask ?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a = 16 chars max, hashcat will try 1,2,3...16
                result = engine.attack(
                    mask='?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a',  # 16 positions, incremental tries 1-16
                    use_gpu=True,
                    mixed_mode=mixed_mode,
                    progress_callback=progress_callback  # NOW WITH REAL-TIME UPDATES!
                )
                
                if result:
                    # PASSWORD FOUND!
                    print(f"DEBUG: GPX brute-force found password: {result}")
                    self.terminal_buffer.append("")
                    self.terminal_buffer.append("=" * 50)
                    self.terminal_buffer.append(f"🎉 PASSWORD FOUND (GPU BRUTE-FORCE): {result}")
                    self.terminal_buffer.append(f"   Length: {len(result)} characters")
                    self.terminal_buffer.append("=" * 50)
                    
                    self.attack_result = {
                        'success': True,
                        'password': result,
                        'attempts': engine.attempts,
                        'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds()
                    }
                else:
                    # Password not found (exhausted search space)
                    attempts = engine.attempts  # Get actual attempts from hashcat stats
                    self.terminal_buffer.append("")
                    self.terminal_buffer.append("=" * 50)
                    self.terminal_buffer.append("❌ PASSWORD NOT FOUND")
                    self.terminal_buffer.append(f"Mode: Incremental brute-force (lengths 1-16)")
                    self.terminal_buffer.append(f"Charset: All printable characters (a-zA-Z0-9 + symbols)")
                    self.terminal_buffer.append(f"Total attempts: {attempts:,}")
                    self.terminal_buffer.append(f"Password is either:")
                    self.terminal_buffer.append(f"  • Longer than 16 characters")
                    self.terminal_buffer.append(f"  • Uses non-printable characters")
                    self.terminal_buffer.append(f"  • Different encoding (unicode, etc.)")
                    self.terminal_buffer.append("💡 Try: Use wordlist attack")
                    self.terminal_buffer.append("=" * 50)
                    
                    self.attack_result = {
                        'success': False,
                        'password': None,
                        'attempts': attempts,  # Use actual attempts
                        'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds(),
                        'error': f'❌ Password not found after {attempts:,} GPU attempts (incremental 1-8 chars)'
                    }
                
                self.attack_running = False
            
        except Exception as e:
            print(f"DEBUG: GPX attack exception: {e}")
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG: Full traceback:\n{error_details}")
            traceback.print_exc()
            
            # Show detailed error in terminal
            self.terminal_buffer.append("")
            self.terminal_buffer.append("=" * 50)
            self.terminal_buffer.append("❌ ATTACK ERROR")
            self.terminal_buffer.append(str(e))
            self.terminal_buffer.append("=" * 50)
            
            self.attack_result = {
                'success': False,
                'password': None,
                'attempts': self.attack_stats.get('attempts', 0),
                'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds(),
                'error': f'❌ GPU attack error: {str(e)}'
            }
            self.attack_running = False
    
    def _run_cpu_attack(self, hash_value: str, algorithm: HashAlgorithm, attack_type: str, values: Dict) -> None:
        """Run CPU-only attack (fallback mode)."""
        import time
        import itertools
        import string
        
        try:
            if attack_type == 'dictionary':
                print(f"DEBUG: Starting dictionary attack with {algorithm.value.upper()}")
                
                # Check if user wants to try all wordlists
                if values['-WORDLIST-'] == '*** TRY ALL WORDLISTS ***':
                    wordlists = [
                        'wordlists/common.txt',
                        'wordlists/rockyou-lite.txt',
                        'SecLists/Passwords/Common-Credentials/best110.txt',
                        'SecLists/Passwords/Common-Credentials/best1050.txt',
                        'SecLists/Passwords/Common-Credentials/10k-most-common.txt',
                        'SecLists/Passwords/Common-Credentials/100k-most-used-passwords-NCSC.txt',
                        'SecLists/Passwords/darkc0de.txt'
                    ]
                    self.terminal_buffer.append(">>> TRYING ALL WORDLISTS <<<")
                else:
                    wordlists = [values['-WORDLIST-']]
                
                total_attempts = 0
                for wordlist_name in wordlists:
                    if not self.attack_running:
                        break
                    
                    wordlist_path = Path("examples") / wordlist_name
                    if not wordlist_path.exists():
                        wordlist_path = Path.cwd() / "examples" / wordlist_name
                    
                    if not wordlist_path.exists():
                        self.terminal_buffer.append(f"SKIP: {wordlist_name} not found")
                        continue
                    
                    print(f"DEBUG: Trying wordlist: {wordlist_path}")
                    self.terminal_buffer.append(f"\n=== Trying: {wordlist_name.split('/')[-1]} ===")
                    
                    # Load wordlist
                    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    
                    print(f"DEBUG: Loaded {len(words)} words from {wordlist_name}")
                    self.terminal_buffer.append(f"Loaded {len(words)} passwords...")
                    
                    # Try each word from this wordlist
                    for i, candidate in enumerate(words, 1):
                        if not self.attack_running:
                            print("DEBUG: Attack stopped by user")
                            break
                        while self.attack_paused:
                            time.sleep(0.1)
                        
                        total_attempts += 1
                        
                        # Update stats EVERY attempt for real-time counter
                        self.attack_stats['attempts'] = total_attempts
                        self.attack_stats['current_candidate'] = candidate
                        
                        # Update terminal every 10 attempts for speed
                        if total_attempts % 10 == 0 or total_attempts == 1:
                            self.terminal_buffer.append(f"[{total_attempts:,}] Trying: {candidate}")
                            if len(self.terminal_buffer) > 100:
                                self.terminal_buffer.pop(0)
                        
                        if total_attempts == 1:
                            print(f"DEBUG: First attempt - trying: {candidate}")
                        
                        # NO DELAY - run at full speed
                        
                        # Try the candidate
                        candidate_hash = HashUtils.generate_hash(candidate, algorithm)
                        if candidate_hash == hash_value:
                            print(f"DEBUG: PASSWORD FOUND: {candidate}")
                            self.terminal_buffer.append("")
                            self.terminal_buffer.append("=" * 50)
                            self.terminal_buffer.append(f"🎉 PASSWORD FOUND: {candidate}")
                            self.terminal_buffer.append("=" * 50)
                            self.attack_result = {
                                'success': True,
                                'password': candidate,
                                'attempts': total_attempts,
                                'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds()
                            }
                            self.attack_running = False
                            time.sleep(0.2)  # Give UI time to pick up the result
                            return
                
                # No match found in any wordlist
                self.attack_result = {
                    'success': False,
                    'password': None,
                    'attempts': total_attempts,
                    'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds(),
                    'error': f'❌ Password not found in {len(wordlists)} wordlist(s) - tried {total_attempts:,} passwords'
                }
            
            elif attack_type == 'bruteforce':
                print(f"DEBUG: Starting brute-force attack with {algorithm.value.upper()}")
                # Brute-force attack - try all combinations
                max_len = 12  # Fixed max length
                # Expanded charset: lowercase, uppercase, digits, special chars
                charset = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*"
                
                print(f"DEBUG: Brute-force - max length: {max_len}, charset size: {len(charset)}")
                total_combinations = sum(len(charset)**i for i in range(1, max_len + 1))
                self.terminal_buffer.append(f"🔥 BRUTE-FORCE ATTACK STARTED")
                self.terminal_buffer.append(f"Charset: a-z A-Z 0-9 !@#$%^&* ({len(charset)} chars)")
                self.terminal_buffer.append(f"Max length: {max_len}")
                self.terminal_buffer.append(f"Total combinations: {total_combinations:,}")
                self.terminal_buffer.append("=" * 50)
                
                attempt = 0
                last_terminal_update = 0
                
                # Try lengths from 1 to max_len
                for length in range(1, max_len + 1):
                    print(f"DEBUG: Trying length {length}")
                    self.terminal_buffer.append(f"\n>>> Testing {len(charset)**length:,} combinations of length {length} <<<")
                    
                    for combo in itertools.product(charset, repeat=length):
                        if not self.attack_running:
                            print("DEBUG: Brute-force stopped by user")
                            break
                        while self.attack_paused:
                            time.sleep(0.1)
                        
                        attempt += 1
                        candidate = ''.join(combo)
                        
                        # Update stats EVERY attempt for real-time counter
                        self.attack_stats['attempts'] = attempt
                        self.attack_stats['current_candidate'] = candidate
                        
                        # Update terminal every 5 attempts for super fast scrolling
                        if attempt - last_terminal_update >= 5:
                            self.terminal_buffer.append(f"[{attempt:,}] Trying: {candidate}")
                            if len(self.terminal_buffer) > 100:
                                self.terminal_buffer.pop(0)
                            last_terminal_update = attempt
                        
                        if attempt == 1:
                            print(f"DEBUG: First brute-force attempt - trying: {candidate}")
                        
                        # Try the candidate - NO DELAY for maximum speed
                        candidate_hash = HashUtils.generate_hash(candidate, algorithm)
                        if candidate_hash == hash_value:
                            print(f"DEBUG: PASSWORD FOUND: {candidate}")
                            self.terminal_buffer.append("")
                            self.terminal_buffer.append("=" * 50)
                            self.terminal_buffer.append(f"🎉 PASSWORD FOUND: {candidate}")
                            self.terminal_buffer.append(f"Attempts: {attempt:,} | Length: {length}")
                            self.terminal_buffer.append("=" * 50)
                            self.attack_result = {
                                'success': True,
                                'password': candidate,
                                'attempts': attempt,
                                'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds()
                            }
                            self.attack_running = False
                            time.sleep(0.2)  # Give UI time to pick up the result
                            return
                        
                        # Remove safety limit - let it run through all combinations
                    
                    if not self.attack_running:
                        break
                
                # Exhausted all combinations
                self.terminal_buffer.append("")
                self.terminal_buffer.append("=" * 50)
                self.terminal_buffer.append(f"❌ Exhausted all {attempt:,} combinations")
                self.terminal_buffer.append("=" * 50)
                self.attack_result = {
                    'success': False,
                    'password': None,
                    'attempts': attempt,
                    'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds(),
                    'error': f'❌ Password not found after trying all {attempt:,} combinations up to length {max_len}'
                }
            
            else:
                self.attack_result = {
                    'success': False,
                    'password': None,
                    'attempts': 0,
                    'duration': 0,
                    'error': f"Attack type '{attack_type}' not implemented"
                }
        
        except Exception as e:
            # Log the error for debugging
            print(f"ERROR in _run_attack: {e}")
            import traceback
            traceback.print_exc()
            
            self.attack_result = {
                'success': False,
                'password': None,
                'attempts': self.attack_stats.get('attempts', 0),
                'duration': (datetime.now() - self.attack_stats['start_time']).total_seconds() if self.attack_stats.get('start_time') else 0,
                'error': str(e)
            }
            self.attack_running = False
        finally:
            self.attack_running = False
    
    def update_progress(self, window: sg.Window) -> None:
        """Update progress display during attack."""
        # Check if attack finished with result
        if self.attack_result:
            window['-STATUS-'].update("✅ COMPLETED")
            window['-STATUSBAR-'].update("Attack completed")
            self.attack_running = False
            
            if self.attack_result['success']:
                # PASSWORD FOUND - Show everywhere!
                password = self.attack_result['password']
                attempts = self.attack_result['attempts']
                duration = self.attack_result['duration']
                
                # Update status
                window['-STATUS-'].update(f"✅ PASSWORD FOUND: {password}")
                
                # Update terminal with success message
                self.terminal_buffer.append("")
                self.terminal_buffer.append("=" * 50)
                self.terminal_buffer.append(f"🎉 SUCCESS! PASSWORD FOUND: {password}")
                self.terminal_buffer.append(f"Attempts: {attempts:,} | Duration: {duration:.2f}s")
                self.terminal_buffer.append("=" * 50)
                terminal_text = '\n'.join(self.terminal_buffer[-25:])
                window['-TERMINAL-'].update(terminal_text)
                
                # Update log
                self.log_message(window, "=" * 60)
                self.log_message(window, f"🎉 PASSWORD FOUND: {password}")
                self.log_message(window, f"Attempts: {attempts:,} | Duration: {duration:.2f}s")
                self.log_message(window, "=" * 60)
                
                # Update results tab
                window['-RESULT_PWD-'].update(password)
                window['-RESULT_SUCCESS-'].update("✅ YES")
                window['-RESULT_ATTEMPTS-'].update(f"{attempts:,}")
                window['-RESULT_DURATION-'].update(f"{duration:.2f}s")
                window['-PROGRESS-'].update(100)
                
                # Create session data for report generation
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_session = {
                    'session_id': session_id,
                    'hash_value': self.attack_stats['hash_value'],
                    'algorithm': self.attack_stats['algorithm'].value,
                    'attack_type': self.attack_stats['attack_type'],
                    'password': password,
                    'found': True,
                    'attempts': attempts,
                    'duration': duration,
                    'created_at': self.attack_stats['start_time'].isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'speed': self.attack_stats['speed'],
                    'parameters': {
                        'hash_algorithm': self.attack_stats['algorithm'].value.upper(),
                        'attack_method': self.attack_stats['attack_type']
                    }
                }
                
                # Update results details area
                details_text = f"""SESSION DETAILS
{'='*60}

ATTACK INFORMATION:
  • Attack Type: {self.attack_stats['attack_type'].upper()}
  • Hash Algorithm: {self.attack_stats['algorithm'].value.upper()}
  • Target Hash: {self.attack_stats['hash_value']}

RESULTS:
  • Status: ✅ SUCCESS
  • Password Found: {password}
  • Total Attempts: {attempts:,}
  • Duration: {duration:.2f} seconds
  • Average Speed: {int(attempts/duration if duration > 0 else 0):,} H/s

TIMESTAMP:
  • Started: {self.attack_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
  • Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
Reports are now available for export!
Use the buttons above to generate JSON, HTML, or TXT reports.
"""
                window['-RESULT_DETAILS-'].update(details_text)
                
                # Show success popup
                sg.popup(f"🎉 PASSWORD FOUND!\n\nPassword: {password}\n\nAttempts: {attempts:,}\nDuration: {duration:.2f}s", 
                        title="Success", button_color=('white', 'green'), font=("Arial", 12))
            else:
                # Password NOT found
                error_msg = self.attack_result.get('error', 'Password not found')
                attempts = self.attack_result['attempts']
                duration = self.attack_result['duration']
                
                # Update status
                window['-STATUS-'].update(f"❌ FAILED - {error_msg}")
                
                # Update terminal with failure message
                self.terminal_buffer.append("")
                self.terminal_buffer.append("=" * 50)
                self.terminal_buffer.append(f"❌ ATTACK FAILED")
                self.terminal_buffer.append(error_msg)
                self.terminal_buffer.append(f"Attempts: {attempts:,} | Duration: {duration:.2f}s")
                self.terminal_buffer.append("=" * 50)
                terminal_text = '\n'.join(self.terminal_buffer[-25:])
                window['-TERMINAL-'].update(terminal_text)
                
                # Update log
                self.log_message(window, "=" * 60)
                self.log_message(window, f"❌ Attack Failed: {error_msg}")
                self.log_message(window, f"Attempts: {attempts:,} | Duration: {duration:.2f}s")
                self.log_message(window, "=" * 60)
                
                # Update results tab
                window['-RESULT_PWD-'].update("N/A")
                window['-RESULT_SUCCESS-'].update("❌ NO")
                window['-RESULT_ATTEMPTS-'].update(f"{attempts:,}")
                window['-RESULT_DURATION-'].update(f"{duration:.2f}s")
                window['-PROGRESS-'].update(100)
                
                # Create session data for report generation
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_session = {
                    'session_id': session_id,
                    'hash_value': self.attack_stats['hash_value'],
                    'algorithm': self.attack_stats['algorithm'].value,
                    'attack_type': self.attack_stats['attack_type'],
                    'password': None,
                    'found': False,
                    'attempts': attempts,
                    'duration': duration,
                    'created_at': self.attack_stats['start_time'].isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'speed': self.attack_stats['speed'],
                    'error': error_msg,
                    'parameters': {
                        'hash_algorithm': self.attack_stats['algorithm'].value.upper(),
                        'attack_method': self.attack_stats['attack_type']
                    }
                }
                
                # Update results details area
                details_text = f"""SESSION DETAILS
{'='*60}

ATTACK INFORMATION:
  • Attack Type: {self.attack_stats['attack_type'].upper()}
  • Hash Algorithm: {self.attack_stats['algorithm'].value.upper()}
  • Target Hash: {self.attack_stats['hash_value']}

RESULTS:
  • Status: ❌ FAILED
  • Password Found: No
  • Error: {error_msg}
  • Total Attempts: {attempts:,}
  • Duration: {duration:.2f} seconds
  • Average Speed: {int(attempts/duration if duration > 0 else 0):,} H/s

TIMESTAMP:
  • Started: {self.attack_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
  • Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
Reports are now available for export!
Use the buttons above to generate JSON, HTML, or TXT reports.
"""
                window['-RESULT_DETAILS-'].update(details_text)
                
                # Show error popup
                sg.popup_error(f"Password Not Found\n\n{error_msg}\n\nAttempts: {attempts:,}\nDuration: {duration:.2f}s", 
                              title="Attack Failed")
            
            self.attack_result = None  # Clear result
            return
        
        if not self.attack_running:
            return
        
        # Update terminal output
        if self.terminal_buffer:
            terminal_text = '\n'.join(self.terminal_buffer[-20:])
            window['-TERMINAL-'].update(terminal_text)
        
        # Update status with current candidate
        if self.attack_running:
            current = self.attack_stats.get('current_candidate', '')
            attack_type = self.attack_stats.get('attack_type', '')
            attempts = self.attack_stats['attempts']
            
            if attack_type == 'bruteforce' and attempts > 0:
                # Show brute-force progress with attempt count
                window['-STATUS-'].update(f"🔥 Brute-forcing... [{attempts:,} attempts] trying: {current}")
            elif current:
                window['-STATUS-'].update(f"⚡ Running... [{attempts:,}] trying: {current}")
        
        # Calculate speed
        elapsed = (datetime.now() - self.attack_stats['start_time']).total_seconds()
        if elapsed > 0:
            speed = self.attack_stats['attempts'] / elapsed
            self.attack_stats['speed'] = speed
            
            # Estimate time remaining for brute-force
            if self.attack_stats.get('attack_type') == 'bruteforce':
                # This is approximate - actual remaining depends on current length
                eta_text = "Calculating..."
                window['-ETA-'].update(eta_text)
        else:
            speed = 0
        
        # Update UI
        window['-ATTEMPTS-'].update(f"{self.attack_stats['attempts']:,}")
        window['-SPEED-'].update(f"{speed:,.0f} H/s")
        
        # Update progress bar (for dictionary attacks, estimate based on wordlist size)
        if self.attack_stats['attempts'] > 0:
            # Simple progress indication
            progress = min(self.attack_stats['attempts'] % 100, 100)
            window['-PROGRESS-'].update(progress)
    
    def handle_stop_attack(self, window: sg.Window) -> None:
        """Stop the running attack."""
        if self.attack_running:
            self.attack_running = False
            
            # Try to stop hashcat process if GPU attack is running
            if hasattr(self, 'hashcat_wrapper') and self.hashcat_wrapper:
                stopped = self.hashcat_wrapper.stop_attack()
                if stopped:
                    self.log_message(window, "GPU attack stopped - hashcat process terminated")
                    self.terminal_buffer.append(">>> HASHCAT PROCESS TERMINATED <<<")
            
            self.log_message(window, "Attack stopped by user")
            window['-STATUS-'].update("⏹ STOPPED")
            window['-STATUSBAR-'].update("Attack stopped")
            self.terminal_buffer.append(">>> ATTACK STOPPED BY USER <<<")
    
    def handle_pause_attack(self, window: sg.Window) -> None:
        """Pause the running attack."""
        if self.attack_running:
            # Check if GPU attack is running
            attack_type = self.attack_stats.get('attack_type', '')
            use_gpu = self.attack_stats.get('use_gpu', False)
            
            if use_gpu or (attack_type == 'bruteforce' and hasattr(self, 'hashcat_wrapper')):
                # GPU attacks cannot be paused (hashcat limitation)
                sg.popup_warning(
                    "GPU attacks cannot be paused!\n\n"
                    "Hashcat (GPU engine) doesn't support pause/resume.\n\n"
                    "You can only STOP the attack completely.\n\n"
                    "Use the STOP button to terminate the attack.",
                    title="Pause Not Supported"
                )
                return
            
            self.attack_paused = True
            self.log_message(window, "Attack paused")
            window['-STATUS-'].update("⏸ PAUSED")
            window['-PAUSE-'].update(disabled=True)
            window['-RESUME-'].update(disabled=False)
            self.terminal_buffer.append(">>> ATTACK PAUSED <<<")
    
    def handle_resume_attack(self, window: sg.Window) -> None:
        """Resume the paused attack."""
        if self.attack_running and self.attack_paused:
            self.attack_paused = False
            self.log_message(window, "Attack resumed")
            window['-STATUS-'].update("▶ RESUMED - Running...")
            window['-PAUSE-'].update(disabled=False)
            window['-RESUME-'].update(disabled=True)
            self.terminal_buffer.append(">>> ATTACK RESUMED <<<")
    
    def handle_clear_form(self, window: sg.Window) -> None:
        """Clear the new session form."""
        window['-HASH-'].update("")
        window['-ALGO-'].update("SHA256")
        window['-DICT-'].update(True)
        window['-WORDLIST-'].update("common.txt")
    
    def handle_clear_data(self, window: sg.Window) -> None:
        """Clear all progress and results data from current session."""
        # Reset attack state
        self.attack_result = None
        self.attack_stats = {'attempts': 0, 'speed': 0, 'start_time': None, 'current_candidate': ''}
        self.terminal_buffer = []
        self.current_session = None  # Clear session data
        
        # Clear progress tab
        window['-STATUS-'].update("Ready")
        window['-ATTEMPTS-'].update("0")
        window['-SPEED-'].update("0 H/s")
        window['-ETA-'].update("N/A")
        window['-PROGRESS-'].update(0)
        window['-LOG-'].update("")
        window['-TERMINAL-'].update("")
        window['-STATUSBAR-'].update("Data cleared - Ready for new session")
        
        # Clear results tab
        window['-RESULT_PWD-'].update("N/A")
        window['-RESULT_ATTEMPTS-'].update("0")
        window['-RESULT_DURATION-'].update("0s")
        window['-RESULT_SUCCESS-'].update("No")
        window['-RESULT_DETAILS-'].update("No session data available.\n\nComplete an attack to see detailed results here.")
        
        self.log_message(window, "Session data cleared")
    
    def handle_start_attack(self, window: sg.Window, values: Dict) -> None:
        """Handle starting an attack."""
        if self.attack_running:
            sg.popup_error("An attack is already running!")
            return
            
        # Validate inputs
        hash_value = values['-HASH-'].strip()
        if not hash_value:
            sg.popup_error("Please enter a target hash.")
            return
        
        algo_str = values['-ALGO-']
        try:
            algorithm = HashAlgorithm[algo_str.upper()]
        except KeyError:
            sg.popup_error(f"Invalid algorithm: {algo_str}")
            return
        
        # Determine attack type
        if values['-DICT-']:
            attack_type = 'dictionary'
            wordlist = values['-WORDLIST-']
        elif values['-BRUTE-']:
            attack_type = 'bruteforce'
        else:
            sg.popup_error("Please select an attack type.")
            return
        
        # Reset stats
        self.attack_stats = {
            'attempts': 0,
            'speed': 0,
            'start_time': datetime.now(),
            'hash_value': hash_value,
            'algorithm': algorithm,
            'attack_type': attack_type,
            'current_candidate': ''
        }
        self.attack_result = None
        self.attack_running = True
        self.attack_paused = False
        self.terminal_buffer = []  # Reset terminal buffer
        
        # Update UI
        window['-STATUS-'].update("Running...")
        window['-STATUSBAR-'].update("Attack in progress...")
        window['-ATTEMPTS-'].update("0")
        window['-SPEED-'].update("0 H/s")
        window['-ETA-'].update("Calculating...")
        window['-PROGRESS-'].update(0)
        window['-TERMINAL-'].update("")  # Clear terminal
        self.log_message(window, f"Starting {attack_type} attack...")
        self.log_message(window, f"Target: {hash_value[:16]}...")
        self.log_message(window, f"Algorithm: {algorithm.value}")
        
        # Start attack in background thread
        self.attack_thread = threading.Thread(
            target=self._run_attack,
            args=(hash_value, algorithm, attack_type, values),
            daemon=True
        )
        self.attack_thread.start()
    
    def handle_gpx_benchmark(self, window: sg.Window, values: Dict) -> None:
        """Handle GPX benchmark request."""
        if not self.gpx_manager.is_gpu_available():
            response = sg.popup_yes_no(
                "No GPU detected!\n\n"
                "Benchmark will only test CPU performance.\n\n"
                "Continue anyway?",
                title="No GPU Detected"
            )
            if response != "Yes":
                return
        
        # Get selected algorithm
        algo_name = values['-ALGO-']
        hash_mode = HashcatMode.from_algorithm(HashAlgorithm[algo_name])
        
        # Show progress
        sg.popup_quick_message("Running benchmark... This may take 5-10 seconds", 
                              auto_close_duration=2, background_color='blue')
        
        # Run benchmarks
        results = []
        errors = []
        
        # Benchmark GPU (if available)
        if self.gpx_manager.is_gpu_available():
            best_gpu = self.gpx_manager.get_best_device()
            print(f"DEBUG: Benchmarking GPU: {best_gpu.name}")
            gpu_speed = self.gpx_manager.benchmark_device(best_gpu, hash_mode, duration_seconds=5)
            if gpu_speed > 0:
                results.append(("GPU", best_gpu.name, gpu_speed))
            else:
                errors.append(f"GPU benchmark failed for {best_gpu.name}")
        
        # Benchmark CPU
        cpu_device = self.gpx_manager.get_cpu_device()
        if cpu_device:
            print(f"DEBUG: Benchmarking CPU: {cpu_device.name}")
            cpu_speed = self.gpx_manager.benchmark_device(cpu_device, hash_mode, duration_seconds=5)
            if cpu_speed > 0:
                results.append(("CPU", cpu_device.name, cpu_speed))
            else:
                errors.append(f"CPU benchmark failed")
        
        # Check if we got any results
        if not results:
            error_msg = "Benchmark failed!\n\n"
            error_msg += "\n".join(errors) if errors else "No devices could be benchmarked"
            error_msg += "\n\nCheck the terminal for detailed debug output."
            sg.popup_error(error_msg, title="Benchmark Failed")
            return
        
        # Calculate speedup
        speedup_text = ""
        if len(results) == 2:
            gpu_speed = results[0][2]
            cpu_speed = results[1][2]
            if cpu_speed > 0:
                speedup = gpu_speed / cpu_speed
                speedup_text = f"\n\n🚀 GPU Speedup: {speedup:.1f}× faster than CPU"
                if speedup >= 4:
                    speedup_text += "\n✅ GPX recommended - significant acceleration"
                elif speedup >= 2:
                    speedup_text += "\n✅ GPX recommended - moderate acceleration"
                else:
                    speedup_text += f"\n⚠️ Note: {algo_name} may be GPU-resistant (slow hashing)"
        
        # Format output
        output = f"BENCHMARK RESULTS - {algo_name}\n" + "=" * 60 + "\n\n"
        for device_type, device_name, speed in results:
            formatted_speed = self.gpx_manager.format_hash_rate(speed)
            output += f"{device_type}: {device_name}\n"
            output += f"  Speed: {formatted_speed}\n\n"
        
        output += speedup_text
        
        # Add errors if any
        if errors:
            output += "\n\n" + "=" * 60 + "\n⚠️ WARNINGS:\n"
            output += "\n".join(f"  • {err}" for err in errors)
        
        # Update UI with estimated speed
        if results:
            best_speed = max(r[2] for r in results)
            formatted = self.gpx_manager.format_hash_rate(best_speed)
            window['-GPX_SPEED_EST-'].update(f"Estimated Speed: {formatted} ({algo_name})")
            window['-GPX_SPEED_EST-'].update(visible=True)
        
        sg.popup_scrolled(output, title="GPX Benchmark Results", size=(70, 20))
    
    def handle_gpx_rescan(self, window: sg.Window) -> None:
        """Handle device rescan request."""
        sg.popup_quick_message("Scanning devices...", auto_close_duration=1, background_color='blue')
        
        try:
            self.gpx_manager.detect_devices(force_rescan=True)
            
            # Update UI
            device_summary = self.gpx_manager.get_device_summary()
            window['-GPX_DEVICE_INFO-'].update(device_summary)
            
            # Update color based on GPU availability (keep black if detected, gray if not)
            if self.gpx_manager.is_gpu_available():
                window['-GPX_DEVICE_INFO-'].update(text_color='black')
                window['-GPX_ENABLED-'].update(disabled=False)
                sg.popup_ok(f"✅ Devices detected:\n\n{device_summary}", title="GPX Device Scan")
            else:
                window['-GPX_DEVICE_INFO-'].update(text_color='gray')
                window['-GPX_ENABLED-'].update(disabled=True, value=False)
                sg.popup_ok("⚠️ No GPU detected. CPU mode will be used.", title="GPX Device Scan")
        
        except Exception as e:
            sg.popup_error(f"Device scan failed: {e}")
    
    def handle_gpx_diagnostics(self, window: sg.Window) -> None:
        """Show detailed GPU/CPU diagnostics."""
        try:
            # Get detailed diagnostic info
            diag_info = self.gpx_manager.get_detailed_device_info()
            
            # Create diagnostics window
            layout = [
                [sg.Text("GPU/CPU Detection Diagnostics", font=("Arial", 12, "bold"))],
                [sg.HorizontalSeparator()],
                [sg.Multiline(diag_info, size=(80, 30), font=("Courier New", 9), 
                             disabled=True, autoscroll=True)],
                [sg.HorizontalSeparator()],
                [sg.Button("Copy to Clipboard", size=(15, 1)), 
                 sg.Button("Rescan", size=(15, 1)),
                 sg.Button("Close", size=(15, 1))]
            ]
            
            diag_window = sg.Window("GPX Diagnostics", layout, modal=True, finalize=True)
            
            while True:
                event, values = diag_window.read()
                
                if event in (sg.WIN_CLOSED, "Close"):
                    break
                elif event == "Copy to Clipboard":
                    sg.clipboard_set(diag_info)
                    sg.popup_quick_message("✅ Copied to clipboard!", auto_close_duration=1)
                elif event == "Rescan":
                    sg.popup_quick_message("Rescanning...", auto_close_duration=1, background_color='blue')
                    self.gpx_manager.detect_devices(force_rescan=True)
                    new_diag_info = self.gpx_manager.get_detailed_device_info()
                    diag_window['-ML-'].update(new_diag_info) if '-ML-' in values else None
                    # Update the multiline text
                    for element in diag_window.element_list():
                        if isinstance(element, sg.Multiline):
                            element.update(new_diag_info)
                            break
            
            diag_window.close()
            
        except Exception as e:
            sg.popup_error(f"Failed to show diagnostics: {e}")
    
    def show_hash_generator(self) -> None:
        """Show hash generator window."""
        layout = [
            [sg.Text("Hash Generator", font=("Arial", 12, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text("Password:"), sg.Input(key='-GEN_PWD-', size=(40, 1))],
            [sg.Text("Algorithm:"), 
             sg.Combo(['MD5', 'SHA1', 'SHA256', 'SHA512'], 
                     default_value='SHA256', key='-GEN_ALGO-')],
            [sg.Button("Generate Hash")],
            [sg.HorizontalSeparator()],
            [sg.Text("Generated Hash:")],
            [sg.Multiline(size=(60, 10), key='-GEN_OUTPUT-', disabled=True)]
        ]
        
        win = sg.Window("Hash Generator", layout, modal=True)
        
        while True:
            event, values = win.read()
            if event in (sg.WIN_CLOSED,):
                break
            
            if event == "Generate Hash":
                pwd = values['-GEN_PWD-']
                algo = HashAlgorithm[values['-GEN_ALGO-']]
                hash_val = HashUtils.generate_hash(pwd, algo)
                win['-GEN_OUTPUT-'].update(f"Algorithm: {algo.value}\nHash: {hash_val}")
        
        win.close()
    
    def show_benchmark(self) -> None:
        """Show benchmark window."""
        sg.popup("Running benchmark...", auto_close=True, auto_close_duration=2)
        
        benchmark = PerformanceBenchmark(test_duration=1.0)
        results = benchmark.benchmark_all()
        
        # Format results
        output = "BENCHMARK RESULTS\n" + "=" * 50 + "\n\n"
        for algo, data in results.items():
            if 'error' in data:
                output += f"{algo}: ERROR\n"
            else:
                output += f"{algo}:\n"
                output += f"  {data['hashes_per_second']:,.0f} hashes/second\n"
                output += f"  {data['ms_per_hash']:.4f} ms/hash\n\n"
        
        sg.popup_scrolled(output, title="Benchmark Results", size=(60, 25))
    
    def run_quick_demo(self, window: sg.Window) -> None:
        """Run a quick demo."""
        demo = self.simulator.create_demo_scenario("easy")
        script = self.simulator.get_demo_script("easy")
        
        sg.popup_scrolled(script, title="Quick Demo Script", size=(70, 25))
    
    def show_about(self) -> None:
        """Show about dialog."""
        about_text = f"""
PasswordCrack Suite v1.0.0
Educational Password Security Research Tool

{self.config.get('description', '')}

Project: {self.config.get('project_name', 'PasswordCrack-Suite')}
Author: {self.config.get('author', 'Unknown')}
License: {self.config.get('license', 'Educational Use Only')}
Copyright © {self.config.get('copyright_year', '2025')}

⚠️ EDUCATIONAL USE ONLY ⚠️
This tool must only be used ethically and legally.
"""
        sg.popup(about_text, title="About PasswordCrack Suite")
    
    def handle_generate_report(self, window: sg.Window, report_type: str) -> None:
        """Handle report generation."""
        if not self.current_session:
            sg.popup_error("No session data available.")
            return
        
        # Generate appropriate report
        if "JSON" in report_type:
            path = self.results_analyzer.generate_report_json(self.current_session)
        elif "HTML" in report_type:
            path = self.results_analyzer.generate_report_html(self.current_session)
        else:
            path = self.results_analyzer.generate_report_txt(self.current_session)
        
        sg.popup(f"Report generated:\n{path}", title="Report Generated")


def main() -> None:
    """Main entry point for GUI application."""
    app = PasswordCrackGUI()
    app.run()


if __name__ == "__main__":
    main()
