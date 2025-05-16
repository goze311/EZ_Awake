import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyautogui
import traceback # For printing full tracebacks

class ScreenAwakeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Awake")
        # self.root.geometry("430x310") # Commented out: let Tkinter try to autosize

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- State Variables ---
        self.program_state = "idle"
        self.is_running = False
        self.time_options = ["30 sec", "1 min", "5 min", "10 min", "15 min", "30 min", "60 min"]
        self.selected_time_str = tk.StringVar(value=self.time_options[0])
        self.selected_interval_seconds = 0
        self.countdown_seconds_remaining = 0
        self.worker_thread = None
        self.countdown_job_id = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.session_start_time_monotonic = None
        self.total_running_time_job_id = None

        # --- UI Setup ---
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(root, padding="15") # Reduced padding
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)

        current_row = 0

        self.title_label = ttk.Label(self.main_frame, text="Keep Screen Active", font=("Arial", 16, "bold"))
        self.title_label.grid(row=current_row, column=0, pady=(0, 10), sticky="ew")
        current_row += 1

        self.dropdown_label = ttk.Label(self.main_frame, text="Select Interval:")
        self.dropdown_label.grid(row=current_row, column=0, pady=(5,0), sticky="ew")
        current_row += 1

        self.time_dropdown = ttk.Combobox(
            self.main_frame,
            textvariable=self.selected_time_str,
            values=self.time_options,
            state="readonly",
        )
        self.time_dropdown.grid(row=current_row, column=0, pady=(0,10), sticky="ew")
        current_row += 1

        self.status_label = ttk.Label(self.main_frame, text="Status: Idle", wraplength=380)
        self.status_label.grid(row=current_row, column=0, pady=5, sticky="ew")
        current_row += 1

        self.countdown_label = ttk.Label(self.main_frame, text="", font=("Arial", 12))
        self.countdown_label.grid(row=current_row, column=0, pady=5, sticky="ew")
        current_row += 1

        self.total_running_time_label = ttk.Label(
            self.main_frame,
            text="Total Running Time: 00:00:00",
            font=("Arial", 9), # Reduced font
            wraplength=380
        )
        self.total_running_time_label.grid(row=current_row, column=0, pady=(5,10), sticky="ew")
        current_row += 1

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=current_row, column=0, pady=(5,0), sticky="ew") # Reduced pady

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=0)
        self.button_frame.columnconfigure(2, weight=0)
        self.button_frame.columnconfigure(3, weight=0)
        self.button_frame.columnconfigure(4, weight=1)

        button_ipadx = 5
        button_ipady = 3

        self.start_button = ttk.Button(self.button_frame, text="Start", command=self.start_action)
        self.start_button.grid(row=0, column=1, padx=5, ipadx=button_ipadx, ipady=button_ipady)

        self.pause_resume_button = ttk.Button(self.button_frame, text="Pause", command=self.pause_action, state=tk.DISABLED)
        self.pause_resume_button.grid(row=0, column=2, padx=5, ipadx=button_ipadx, ipady=button_ipady)

        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self.stop_action, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=5, ipadx=button_ipadx, ipady=button_ipady)

        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=0)
        self.main_frame.rowconfigure(2, weight=0)
        self.main_frame.rowconfigure(3, weight=0)
        self.main_frame.rowconfigure(4, weight=0)
        self.main_frame.rowconfigure(5, weight=0) # Total running time row
        self.main_frame.rowconfigure(6, weight=0) # Button frame row

        self.root.update_idletasks() # Force layout calculation
        # After Tkinter calculates sizes, you could uncomment self.root.geometry if needed,
        # or set a minsize based on calculated preferred sizes.
        # e.g., self.root.minsize(self.main_frame.winfo_reqwidth() + 30, self.main_frame.winfo_reqheight() + 30)


        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._update_ui_states()

    def _update_ui_states(self):
        self._update_countdown_label_text()

        if self.program_state == "idle":
            self.start_button.config(state=tk.NORMAL)
            self.pause_resume_button.config(text="Pause", command=self.pause_action, state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.time_dropdown.config(state="readonly")
            self.status_label.config(text="Status: Idle")
            self.total_running_time_label.config(text="Total Running Time: 00:00:00")
        elif self.program_state == "running":
            self.start_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(text="Pause", command=self.pause_action, state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.time_dropdown.config(state=tk.DISABLED)
        elif self.program_state == "paused":
            self.start_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(text="Resume", command=self.resume_action, state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.time_dropdown.config(state=tk.DISABLED)
            current_countdown_text = self.countdown_label.cget("text")
            self.status_label.config(text=f"Status: Paused ({current_countdown_text})")

    def get_interval_seconds(self):
        time_str = self.selected_time_str.get()
        parts = time_str.split(" ")
        value = int(parts[0])
        unit = parts[1].lower()
        return value if unit == "sec" else value * 60

    def _update_countdown_label_text(self):
        if self.program_state == "running" or self.program_state == "paused":
            if self.countdown_seconds_remaining > 0:
                mins, secs = divmod(self.countdown_seconds_remaining, 60)
                if self.selected_interval_seconds < 60:
                    self.countdown_label.config(text=f"Next action in: {self.countdown_seconds_remaining:02d} sec")
                else:
                    self.countdown_label.config(text=f"Next action in: {mins:02d}:{secs:02d}")
            elif self.countdown_seconds_remaining == 0 and self.program_state == "running":
                self.countdown_label.config(text="Performing action...")
            elif self.countdown_seconds_remaining <= 0 and self.program_state == "paused":
                self.countdown_label.config(text="Next action: Paused")
            elif self.countdown_seconds_remaining < 0 and self.program_state == "running":
                default_time_text = "Next action in: 00 sec" if self.selected_interval_seconds < 60 else "Next action in: 00:00"
                self.countdown_label.config(text=default_time_text)
            elif self.countdown_seconds_remaining == 0 and self.program_state != "running":
                default_time_text = "Next action in: 00 sec" if self.selected_interval_seconds < 60 else "Next action in: 00:00"
                self.countdown_label.config(text=default_time_text)
        elif self.program_state == "idle":
            self.countdown_label.config(text="")

    def update_countdown_display(self):
        if self.countdown_job_id:
            self.root.after_cancel(self.countdown_job_id)
            self.countdown_job_id = None
        self._update_countdown_label_text()
        if self.program_state == "running":
            if self.countdown_seconds_remaining > 0:
                self.countdown_seconds_remaining -= 1
            self.countdown_job_id = self.root.after(1000, self.update_countdown_display)
        elif self.program_state == "paused":
            self.countdown_job_id = self.root.after(500, self.update_countdown_display)

    def _update_total_running_time_display(self):
        if self.total_running_time_job_id:
            self.root.after_cancel(self.total_running_time_job_id)
            self.total_running_time_job_id = None

        if self.program_state == "running" or self.program_state == "paused":
            if self.session_start_time_monotonic is not None:
                elapsed_seconds = int(time.monotonic() - self.session_start_time_monotonic)
                hours, remainder = divmod(elapsed_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.total_running_time_label.config(text=f"Total Running Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.total_running_time_job_id = self.root.after(1000, self._update_total_running_time_display)
        elif self.program_state == "idle":
            self.total_running_time_label.config(text="Total Running Time: 00:00:00")

    def start_action(self):
        if self.program_state != "idle":
            return

        self.is_running = True
        self.program_state = "running"
        self.pause_event.set()

        self.selected_interval_seconds = self.get_interval_seconds()
        self.countdown_seconds_remaining = self.selected_interval_seconds
        self.session_start_time_monotonic = time.monotonic()

        self.status_label.config(text="Program started. Screen will be kept active.")
        self._update_ui_states()
        self.update_countdown_display()
        self._update_total_running_time_display()

        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self.keep_awake_loop, daemon=True)
            self.worker_thread.start()

    def pause_action(self):
        if self.program_state == "running":
            self.program_state = "paused"
            self.pause_event.clear()
            self._update_ui_states()

    def resume_action(self):
        if self.program_state == "paused":
            self.program_state = "running"
            self.pause_event.set()
            self.status_label.config(text="Program resumed. Screen will be kept active.")
            self._update_ui_states()
            self.update_countdown_display()

    def stop_action(self):
        if self.program_state == "idle":
            return

        self.is_running = False
        self.program_state = "idle"
        self.pause_event.set()

        if self.countdown_job_id:
            self.root.after_cancel(self.countdown_job_id)
            self.countdown_job_id = None

        if self.total_running_time_job_id:
            self.root.after_cancel(self.total_running_time_job_id)
            self.total_running_time_job_id = None

        self.session_start_time_monotonic = None

        self._update_ui_states()
        pyautogui.FAILSAFE = True

    def keep_awake_loop(self):
        print(f"[{time.ctime()}] WORKER: Thread started. FAILSAFE initially False.")
        pyautogui.FAILSAFE = False
        try:
            while self.is_running:
                print(f"[{time.ctime()}] WORKER: Top of main loop. is_running={self.is_running}, program_state={self.program_state}")

                if self.program_state == "running":
                    self.countdown_seconds_remaining = self.selected_interval_seconds
                    print(f"[{time.ctime()}] WORKER: Reset UI countdown to {self.countdown_seconds_remaining}s as program_state is 'running'.")
                else:
                    print(f"[{time.ctime()}] WORKER: program_state is '{self.program_state}', not 'running'. UI countdown not reset by worker this cycle.")

                try:
                    if hasattr(self.root, 'winfo_exists') and self.root.winfo_exists():
                        self.root.after(0, self._update_countdown_label_text)
                except tk.TclError as e:
                    print(f"[{time.ctime()}] WORKER: Mild TclError scheduling UI update (likely app closing): {e}")

                print(f"[{time.ctime()}] WORKER: Starting interval timing for {self.selected_interval_seconds}s.")
                current_interval_elapsed_worker = 0
                while current_interval_elapsed_worker < self.selected_interval_seconds:
                    if not self.is_running:
                        print(f"[{time.ctime()}] WORKER: Inner loop detected stop (is_running=False). Returning.")
                        return
                    self.pause_event.wait()
                    if not self.is_running:
                        print(f"[{time.ctime()}] WORKER: Inner loop detected stop after pause_event.wait(). Returning.")
                        return
                    time.sleep(1)
                    current_interval_elapsed_worker += 1

                print(f"[{time.ctime()}] WORKER: Interval time fully elapsed ({current_interval_elapsed_worker}s). is_running={self.is_running}")
                if not self.is_running:
                    print(f"[{time.ctime()}] WORKER: Detected stop immediately after interval elapsed. Returning.")
                    return

                print(f"[{time.ctime()}] WORKER: Checking final pause state before action. Pre-pause_event.wait()")
                self.pause_event.wait()
                print(f"[{time.ctime()}] WORKER: Post-final pause_event.wait()")
                if not self.is_running:
                    print(f"[{time.ctime()}] WORKER: Detected stop after final pause_event.wait(). Returning.")
                    return

                print(f"[{time.ctime()}] WORKER: About to perform action. program_state='{self.program_state}'")
                if self.program_state == "running":
                    try:
                        print(f"[{time.ctime()}] WORKER: Attempting mouse move...")
                        move_distance = 75
                        duration_move = 0.15
                        pyautogui.moveRel(move_distance, move_distance, duration=duration_move)
                        time.sleep(0.1)
                        pyautogui.moveRel(-move_distance, -move_distance, duration=duration_move)
                        print(f"[{time.ctime()}] WORKER: Mouse movement executed successfully.")
                    except pyautogui.FailSafeException as fse:
                        print(f"[{time.ctime()}] WORKER: PyAutoGUI FailSafeException during action: {fse}", flush=True)
                    except Exception as e_action:
                        print(f"[{time.ctime()}] WORKER: Exception during mouse move: {e_action}", flush=True)
                        traceback.print_exc()
                else:
                    print(f"[{time.ctime()}] WORKER: Skipped action because program_state is '{self.program_state}', not 'running'.")
                print(f"[{time.ctime()}] WORKER: End of action block. Looping back.")

            print(f"[{time.ctime()}] WORKER: self.is_running became False. Main worker loop terminating normally.")

        except Exception as e_outer:
            print(f"[{time.ctime()}] WORKER: !!! CRITICAL UNHANDLED EXCEPTION in keep_awake_loop: {e_outer} !!!", flush=True)
            traceback.print_exc()
        finally:
            pyautogui.FAILSAFE = True
            print(f"[{time.ctime()}] WORKER: Thread exiting. FAILSAFE re-enabled. is_running final state: {self.is_running}", flush=True)

    def on_closing(self):
        if self.program_state != "idle":
            self.stop_action()
        if hasattr(self.root, 'winfo_exists') and self.root.winfo_exists():
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenAwakeApp(root)
    root.mainloop()