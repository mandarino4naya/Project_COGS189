# Pls make sure to check all your imports make sense and compile, currently works on a Lab Windows system and M1 MacOS Sonoma 14+
from psychopy import visual, core, event
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from pylsl import StreamInfo, StreamOutlet
import random
import os
import csv
import glob, sys, time, serial
from serial import Serial

# Participant ID
participant_id = input("Enter participant ID: ")

# Create a folder for the participant
results_folder = f"results/{participant_id}"
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# Cyton board setup
sampling_rate = 250
CYTON_BOARD_ID = 0  # 0 if no daisy, 2 if using daisy board, 6 if using daisy + WiFi shield
SYNTHETIC_BOARD_ID = BoardIds.SYNTHETIC_BOARD.value
BAUD_RATE = 115200
ANALOGUE_MODE = '/2'  # Reads from analog pins A5(D11), A6(D12), and A7(D13) if no WiFi shield is present.

def find_openbci_port():
    """Finds the port to which the Cyton Dongle is connected to."""
    # Find serial port names per OS
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/ttyUSB*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/cu.usbserial*')
    else:
        raise EnvironmentError('Error finding ports on your operating system')
    openbci_port = ''
    for port in ports:
        try:
            s = Serial(port=port, baudrate=BAUD_RATE, timeout=None)
            s.write(b'v')
            line = ''
            time.sleep(2)
            if s.inWaiting():
                line = ''
                c = ''
                while '$$$' not in line:
                    c = s.read().decode('utf-8', errors='replace')
                    line += c
                if 'OpenBCI' in line:
                    openbci_port = port
            s.close()
        except (OSError, serial.SerialException):
            pass
    if openbci_port == '':
        print("OpenBCI port not found, proceeding with a synthetic board.")  # EDITED
        return None  # EDITED
    else:
        return openbci_port

# Initialize BrainFlow for OpenBCI or Synthetic board
params = BrainFlowInputParams()
detected_port = find_openbci_port()  # EDITED

if detected_port is None:  # EDITED
    board_id = SYNTHETIC_BOARD_ID  # EDITED
    print(BoardShim.get_board_descr(SYNTHETIC_BOARD_ID))
else:  # EDITED
    board_id = CYTON_BOARD_ID  # EDITED
    print(BoardShim.get_board_descr(CYTON_BOARD_ID))
    # If using WiFi shield or otherwise, set params accordingly
    if CYTON_BOARD_ID != 6:  # Keep your original logic
        params.serial_port = detected_port
    else:
        params.ip_port = 9000

board = BoardShim(board_id, params)  # EDITED

try:
    board.prepare_session()
    # Configure board only if it's the actual Cyton (not synthetic)
    if board_id == CYTON_BOARD_ID:  # EDITED
        res_query = board.config_board('/0')
        print(res_query)
        res_query = board.config_board('//')
        print(res_query)
        res_query = board.config_board(ANALOGUE_MODE)
        print(res_query)
except Exception as e:
    print(f"Error initializing OpenBCI: {e}")
    core.quit()

# Initialize LSL for markers
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'marker_stream')
outlet = StreamOutlet(info)

# PsychoPy setup
win = visual.Window(size=(800, 600), color='white', units='pix')
text_stim = visual.TextStim(win, color='black', height=40)
crosshair = visual.TextStim(win, text='+', color='black', height=60)

# Baseline EEG data collection
print("Starting 30-second baseline EEG data collection...")
outlet.push_sample([999])  # Marker for start of baseline
board.start_stream()  # Start the EEG stream
core.wait(30)  # Wait for 30 seconds to collect baseline data
baseline_eeg_data = board.get_board_data()  # Retrieve baseline EEG data
board.stop_stream()  # Stop the EEG stream after baseline collection
outlet.push_sample([1000])  # Marker for end of baseline

# Save baseline EEG data to a separate CSV file
baseline_eeg_data_file = os.path.join(results_folder, "baseline_eeg_data.csv")
with open(baseline_eeg_data_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write headers (e.g., channel names)
    writer.writerow(['Timestamp'] + [f'Channel_{i}' for i in range(baseline_eeg_data.shape[0])])
    # Write data
    for row in baseline_eeg_data.T:  # Transpose to write row-wise
        writer.writerow(row)

print("Baseline EEG data collection complete. Starting the main experiment...")

# Experiment parameters
n_trials = 30
colors = ['red', 'blue']
word_duration = 0.5
blank_duration = 0.5
iti = 1.5
words = ['apple', 'banana', 'carrot', 'dog', 'elephant', 'fish', 'grape', 'house', 'ice', 'jacket',
         'kite', 'lemon', 'mango', 'nest', 'orange', 'pear', 'queen', 'rabbit', 'snake', 'tiger',
         'umbrella', 'violin', 'whale', 'xylophone', 'yacht', 'zebra', 'sink', 'cap', 'drawer', 'tissue']

# Shuffle words
random.shuffle(words)

# Create a stimulus log file
stimulus_log_file = os.path.join(results_folder, "stimulus_log.csv")
with open(stimulus_log_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write headers
    writer.writerow(["Trial", "Word", "Color", "Timestamp", "Marker"])

    instructions = visual.TextStim(win, text="You will see words in different colors. Focus on both the word and the color.", color='black', height=30)
    instructions.draw()
    win.flip()
    core.wait(5)  # Show instructions for 5 seconds

    # Start EEG data collection for the main experiment
    board.start_stream()

    # Main experiment loop
    presented_words = []  # Store words and their colors for the memory test
    for trial in range(n_trials):
        word = words[trial]
        color = colors[trial % len(colors)]
        win.color = color
        presented_words.append((word, color))

        # Crosshair
        win.color = 'white'
        crosshair.draw()
        win.flip()
        core.wait(0.3)

        # Present word
        win.color = color
        text_stim.setText(word)
        text_stim.draw()
        win.flip()

        # Record timestamp and send marker
        timestamp = time.time()  # Get the current time
        marker = trial + 1  # Marker corresponds to trial number
        outlet.push_sample([marker])  # Send marker via LSL

        # Log stimulus presentation details
        writer.writerow([trial + 1, word, color, timestamp, marker])

        core.wait(word_duration)

        # Blank screen
        win.color = 'white'
        crosshair.draw()
        win.flip()
        core.wait(blank_duration)

        # Inter-trial interval
        crosshair.draw()
        win.flip()
        core.wait(iti)

    # Stop EEG data collection after the experiment
    eeg_data = board.get_board_data()  # Retrieve all collected EEG data
    board.stop_stream()
    board.release_session()

# Save EEG data to a CSV file
eeg_data_file = os.path.join(results_folder, "eeg_data.csv")
with open(eeg_data_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write headers (e.g., channel names)
    writer.writerow(['Timestamp'] + [f'Channel_{i}' for i in range(eeg_data.shape[0])])
    # Write data
    for row in eeg_data.T:  # Transpose to write row-wise
        writer.writerow(row)

# Memory test
win.color = 'white'  # Reset background to white for the memory test
memory_test_instructions = visual.TextStim(win, text="Now, you will be asked if you saw certain words in specific colors. Respond with 'Y' for Yes or 'N' for No.", color='black', height=30)
memory_test_instructions.draw()
win.flip()
core.wait(5)

# Generate memory test items
memory_test_items = []
for word, correct_color in random.sample(presented_words, 15):
    # Randomly decide whether to show the correct or incorrect color
    if random.choice([True, False]):  # 50% chance
        memory_test_items.append((word, correct_color))  # Correct color
    else:
        # Choose an incorrect color
        incorrect_color = random.choice([c for c in colors if c != correct_color])
        memory_test_items.append((word, incorrect_color))  # Incorrect color

# Add 5 non-presented words (foil words) with random colors
foil_words = [('cat', random.choice(colors)), ('boat', random.choice(colors)), 
              ('shoe', random.choice(colors)), ('belt', random.choice(colors)), 
              ('sock', random.choice(colors))]

# Combine presented words and foil words, then shuffle
memory_test_items += foil_words
random.shuffle(memory_test_items)

# Conduct memory test
correct_responses = 0
memory_test_results = []  # Store memory test results
for word, color in memory_test_items:
    question = visual.TextStim(win, text=f"Did you see the word '{word}' with a {color} background? (Y/N)", color='black', height=30)
    question.draw()
    win.flip()

    # Wait for response
    response = event.waitKeys(keyList=['y', 'n', 'escape'])
    if response[0] == 'escape':
        core.quit()
    elif (response[0] == 'y' and (word, color) in presented_words) or (response[0] == 'n' and (word, color) not in presented_words):
        correct_responses += 1
        memory_test_results.append((word, color, response[0], "Correct"))
    else:
        memory_test_results.append((word, color, response[0], "Incorrect"))

# Save memory test results to a CSV file
memory_test_file = os.path.join(results_folder, "memory_test_results.csv")
with open(memory_test_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Word", "Color", "Response", "Accuracy"])
    writer.writerows(memory_test_results)

# Display results
results = visual.TextStim(win, text=f"Memory test complete. You got {correct_responses} out of {len(memory_test_items)} correct.", color='black', height=30)
results.draw()
win.flip()
core.wait(5)

print("Experiment complete. Data saved.")

# Clean up
win.close()
core.quit()
