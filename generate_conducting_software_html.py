import json
import math

# --- Re-using your existing calculation functions (these won't be used by this script anymore for JSON generation) ---
# Keeping them here just in case you ever decide to re-integrate or for reference.
# You can technically remove them if you're certain they won't be used by this script.

def calculate_bell_ringing_timeline(
    num_ringers=6,
    initial_time_per_ring=0.5,
    total_rows=40,
    final_time_per_ring=10.0,
    curve_type="linear",
    ignore_first_n_rows=0,
    ignore_last_n_rows=0,
    method_data=None
):
    timeline = []
    current_time_absolute = 0.0

    if method_data:
        total_rows = len(method_data)
        if total_rows > 0:
            num_ringers = len(method_data[0])
        else:
            num_ringers = 0
    elif total_rows == 0:
        num_ringers = 0

    if total_rows == 0 or num_ringers == 0:
        return {
            "timeline": [],
            "total_duration": 0.0,
            "method_data": method_data if method_data else []
        }

    if ignore_first_n_rows < 0: ignore_first_n_rows = 0
    if ignore_last_n_rows < 0: ignore_last_n_rows = 0
    if ignore_first_n_rows + ignore_last_n_rows >= total_rows and total_rows > 0:
        ignore_first_n_rows = total_rows
        ignore_last_n_rows = 0
        active_rows = 0
    else:
        active_rows = total_rows - ignore_first_n_rows - ignore_last_n_rows

    time_range = final_time_per_ring - initial_time_per_ring


    for row_idx in range(total_rows):
        row_number = row_idx + 1
        current_row_time_per_ring = 0.0

        if row_number <= ignore_first_n_rows:
            current_row_time_per_ring = initial_time_per_ring
        elif row_number > (total_rows - ignore_last_n_rows):
            current_row_time_per_ring = final_time_per_ring
        else:
            progress_in_active_rows = (row_idx) - ignore_first_n_rows

            normalized_progress = progress_in_active_rows / (active_rows - 1) if active_rows > 1 else 0

            progress_on_curve = 0.0
            if curve_type == "ease_out_expo":
                progress_on_curve = 1 - math.pow(2, -10 * normalized_progress)
            elif curve_type == "ease_in_quad":
                progress_on_curve = normalized_progress * normalized_progress
            elif curve_type == "ease_in_out_sine":
                progress_on_curve = -0.5 * (math.cos(math.pi * normalized_progress) - 1)
            else:
                progress_on_curve = normalized_progress

            current_row_time_per_ring = initial_time_per_ring + (time_range * progress_on_curve)

        current_row_ringers = method_data[row_idx] if method_data and row_idx < len(method_data) else list(range(1, num_ringers + 1))

        for position_in_row, ringer_num_in_method in enumerate(current_row_ringers, 1):
            ring_event = {
                "row": row_number,
                "ringer": ringer_num_in_method,
                "position_in_row": position_in_row,
                "time_between_rings_in_row": current_row_time_per_ring,
                "absolute_time_start": current_time_absolute
            }
            timeline.append(ring_event)
            current_time_absolute += current_row_time_per_ring

    if not timeline:
        total_duration = 0.0
    else:
        total_duration = current_time_absolute - timeline[-1]["time_between_rings_in_row"]


    return {
        "timeline": timeline,
        "total_duration": total_duration,
        "method_data": method_data if method_data else []
    }

# --- Main HTML Generation Function ---
def generate_conducting_software_html(filename="bell_conducting_software.html"):
    """
    Generates the HTML file for the bell conducting software.
    """
    # Default offsets for the input fields
    default_offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # Default to 0 for 6 bells

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bell Conducting Software - Singing Hollow</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Inter', sans-serif;
                background-color: #333; /* Dark grey background */
                color: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                width: 100vw;
                transition: background-color 0.1s ease-in-out; /* Smooth color changes */
            }}

            /* Startup Screen */
            #startup-screen {{
                display: flex;
                flex-direction: column;
                justify-content: center; /* Center content vertically initially */
                align-items: center;
                text-align: center;
                padding: 20px;
                max-width: 800px;
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 15px;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
                box-sizing: border-box; /* Include padding in width/height */
                margin: 20px; /* Add some margin to prevent sticking to edges */
                flex-shrink: 0; /* Prevent shrinking too much */
            }}
            #startup-screen h1 {{
                font-size: 2.5em;
                margin-bottom: 20px;
            }}
            #startup-screen p {{
                font-size: 1.1em;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            #start-button {{
                padding: 20px 40px;
                font-size: 2em;
                font-weight: bold;
                background-color: #4CAF50; /* Green */
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                transition: background-color 0.3s, transform 0.1s;
            }}
            #start-button:hover {{
                background-color: #45a049;
                transform: translateY(-2px);
            }}
            #start-button:active {{
                transform: translateY(0);
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }}

            /* JSON Selection & Offsets */
            .control-group {{
                margin-top: 30px; /* Spacing between control groups */
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                width: calc(100% - 30px); /* Fill parent, account for padding */
                max-width: 500px; /* Keep consistent with content width */
                box-sizing: border-box; /* Include padding in width */
            }}
            .control-group label {{
                display: block;
                margin-bottom: 10px;
                font-size: 1.1em;
            }}
            .control-group select, .control-group input[type="file"] {{
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #444;
                color: white;
                font-size: 1em;
                width: 100%; /* Fill the container */
                max-width: 100%; /* Ensure it doesn't break out */
                margin-bottom: 10px;
                box-sizing: border-box; /* Include padding in width */
            }}
            .control-group input[type="file"]::-webkit-file-upload-button {{
                background-color: #007BFF;
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                border: none;
                cursor: pointer;
            }}
            .control-group input[type="file"]::-webkit-file-upload-button:hover {{
                background-color: #0056b3;
            }}
            .offset-inputs {{
                display: flex;
                flex-wrap: wrap; /* Allow items to wrap to next line */
                gap: 10px;
                justify-content: center;
                margin-top: 15px;
            }}
            .offset-input-item {{
                display: flex;
                flex-direction: column;
                align-items: center;
                flex: 1 1 auto; /* Allow items to grow and shrink */
                min-width: 80px; /* Minimum width for each item to prevent too much squishing */
            }}
            .offset-input-item label {{
                font-size: 0.9em;
                margin-bottom: 3px;
                color: #ccc;
                text-align: center;
            }}
            .offset-input-item input[type="number"] {{
                width: 60px; /* Smaller input for offsets */
                padding: 5px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #444;
                color: white;
                font-size: 0.9em;
                box-sizing: border-box; /* Include padding in width */
            }}


            /* Playback Screen */
            #playback-screen {{
                display: none; /* Hidden by default */
                flex-direction: column;
                justify-content: center;
                align-items: center;
                width: 100vw;
                height: 100vh;
                position: relative;
            }}
            #current-bell-display {{
                font-size: 20em; /* Large numeral */
                font-weight: bold;
                text-shadow: 0 0 20px rgba(0,0,0,0.8);
                display: none; /* Only show during flash */
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10;
            }}

            /* Info Overlays */
            /* Consolidated .info-overlay styles */
            .info-overlay {{
                position: absolute;
                left: 20px;
                right: 20px;
                display: flex;
                flex-direction: row; /* Default: horizontal arrangement */
                justify-content: space-between; /* Default: space out content */
                align-items: flex-start; /* Default: align items to top */
                z-index: 5;
            }}

            /* Top Info Area */
            #info-overlay-top {{
                top: 20px;
                flex-direction: column; /* Stack countdown and next bell vertically */
                align-items: center; /* Center horizontally */
                gap: 10px; /* Space between countdown and next bell */
            }}

            #countdown-info {{
                background-color: rgba(0, 0, 0, 0.6);
                padding: 15px 20px;
                border-radius: 10px;
                font-size: 1.8em; /* Kept this size for countdown */
                font-weight: bold;
                text-align: center;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                width: fit-content; /* Ensure it only takes needed width */
            }}

            #next-bell-info-center {{ /* New ID for centered next bell */
                display: flex;
                align-items: center;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 15px 20px;
                border-radius: 10px;
                font-size: 1.2em; /* Kept this size for label */
                line-height: 1.4;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                width: fit-content; /* Ensure it only takes needed width */
            }}
            #next-bell-info-center .next-bell-square-common {{
                margin-left: 15px; /* Margin to separate from label */
            }}


            #row-info {{
                position: absolute; /* Take out of flex flow of info-overlay-top */
                top: 20px; /* Position absolutely to top right */
                right: 20px;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 15px 20px;
                border-radius: 10px;
                max-width: 40%;
                font-size: 1.2em;
                line-height: 1.4;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            }}

            /* Total Time Elapsed Clock (bottom center) */
            #total-time-elapsed {{
                position: absolute;
                bottom: 20px;
                left: 50%; /* Center horizontally */
                transform: translateX(-50%); /* Center horizontally */
                background-color: rgba(0, 0, 0, 0.6);
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 1.5em;
                font-weight: bold;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                z-index: 5;
            }}

            .next-bell-square-common {{ /* Common styles for the square */
                width: 100px;
                height: 100px;
                border-radius: 10px;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 2em;
                font-weight: bold;
                color: white;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
            }}

            #current-row-display {{
                font-weight: bold;
                font-size: 2em; /* Bigger font */
            }}
            #method-row-display {{
                font-family: monospace;
                font-size: 1.8em; /* Bigger font */
                background-color: rgba(255,255,255,0.1);
                padding: 5px;
                border-radius: 5px;
                margin-top: 5px;
            }}

            /* Bell Colors */
            .color-1 {{ background-color: #008000; }} /* Green */
            .color-2 {{ background-color: #0000FF; }} /* Blue */
            .color-3 {{ background-color: #FFFF00; color: black; }} /* Yellow */
            .color-4 {{ background-color: #FFC0CB; color: black; }} /* Pink */
            .color-5 {{ background-color: #4B0082; }} /* Dark Purple */
            .color-6 {{ background-color: #FF0000; }} /* Red */
        </style>
    </head>
    <body>
        <div id="startup-screen">
            <h1>Bell Conducting Software - Singing Hollow</h1>
            <p>
                This bell conducting software is specifically designed for performing the scored sections of "Singing Hollow".
                In this piece, the goal is to ring your bell and then attempt to stand it whenever your colour and bell number appear on the screen.
                If you aren't able to stand the bell, don't worry, this striving/failure is part of the intended effect:
                simply keep attempting to stand the bell. During the performance, you will play slow_to_fast once and fast_to_slow once.
                Outside these performances, please perform methods and ring changes and rounds as normal in one of your bell-ringing sessions
                (and feel free to take regular breaks outside the scored sections)
            </p>

            <button id="start-button">START</button>

            <div class="control-group json-selection">
                <label for="json-preset-select">Select a Built-in Score:</label>
                <select id="json-preset-select">
                    <option value="none">-- Select Score --</option>
                    <option value="slow_to_fast.json">Slow to Fast</option>
                    <option value="fast_to_slow.json">Fast to Slow</option>
                </select>

                <label for="json-upload-input" style="margin-top: 15px;">Or Upload Your Own JSON Score:</label>
                <input type="file" id="json-upload-input" accept=".json">
            </div>

            <div class="control-group">
                <label>Bell Offsets (to deal with heavy bells - in seconds):</label>
                <div class="offset-inputs">
                    {''.join([f'''
                    <div class="offset-input-item">
                        <label for="offset-bell-{i+1}">Bell {i+1}</label>
                        <input type="number" id="offset-bell-{i+1}" class="bell-offset-input" value="{default_offsets[i]:.1f}" step="0.1" min="0">
                    </div>
                    ''' for i in range(len(default_offsets))])}
                </div>
            </div>
        </div>

        <div id="playback-screen">
            <div id="current-bell-display"></div>

            <div id="info-overlay-top" class="info-overlay">
                <div id="countdown-info">
                    Countdown: <span id="countdown-timer">--.--</span>s
                </div>
                <div id="next-bell-info-center">
                    Next Bell: <div id="next-bell-square-center" class="next-bell-square-common"></div>
                </div>
            </div>

            <div id="row-info">
                Current Row: <span id="current-row-display">--</span><br>
                Row: <span id="method-row-display"></span>
            </div>

            <div id="total-time-elapsed">
                Elapsed: <span id="elapsed-timer">00:00.00</span>
            </div>
        </div>

        <script>
            // --- Bell Color Mapping ---
            const BELL_COLORS = {{
                1: '#008000', // Green
                2: '#0000FF', // Blue
                3: '#FFFF00', // Yellow
                4: '#FFC0CB', // Pink
                5: '#4B0082', // Dark Purple
                6: '#FF0000'  // Red
            }};

            // --- DOM Elements ---
            const body = document.body;
            const startupScreen = document.getElementById('startup-screen');
            const playbackScreen = document.getElementById('playback-screen');
            const startButton = document.getElementById('start-button');
            const jsonPresetSelect = document.getElementById('json-preset-select');
            const jsonUploadInput = document.getElementById('json-upload-input');
            const bellOffsetInputs = document.querySelectorAll('.bell-offset-input');

            const currentBellDisplay = document.getElementById('current-bell-display');
            const nextBellSquareCenter = document.getElementById('next-bell-square-center'); // Renamed ID

            const countdownTimer = document.getElementById('countdown-timer');
            const currentRowDisplay = document.getElementById('current-row-display');
            const methodRowDisplay = document.getElementById('method-row-display');
            const elapsedTimeDisplay = document.getElementById('elapsed-timer');

            // --- Global State ---
            let currentScoreData = null;
            let timelineEvents = [];
            let methodDataParsed = [];
            let currentEventIndex = 0;
            let startTime = 0;
            let flashTimeoutId = null;
            let countdownIntervalId = null;
            let elapsedTimerIntervalId = null;
            let longestOffset = 0;
            let bellOffsets = {{}};

            // --- Core Functions ---

            function resetPlaybackState() {{
                currentEventIndex = 0;
                startTime = 0;
                if (flashTimeoutId) {{
                    clearTimeout(flashTimeoutId);
                    flashTimeoutId = null;
                }}
                if (countdownIntervalId) {{
                    clearInterval(countdownIntervalId);
                    countdownIntervalId = null;
                }}
                if (elapsedTimerIntervalId) {{
                    clearInterval(elapsedTimerIntervalId);
                    elapsedTimerIntervalId = null;
                }}

                body.style.backgroundColor = '#333';
                currentBellDisplay.style.display = 'none';
                currentBellDisplay.textContent = '';
                // Reset the single next bell square
                nextBellSquareCenter.style.backgroundColor = 'transparent';
                nextBellSquareCenter.textContent = '';
                nextBellSquareCenter.style.color = 'white';

                countdownTimer.textContent = '--.--';
                currentRowDisplay.textContent = '--';
                methodRowDisplay.textContent = '';
                elapsedTimeDisplay.textContent = '00:00.00';
            }}

            async function loadScoreFromUrl(url) {{
                try {{
                    const response = await fetch(url);
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    const data = await response.json();
                    if (data.timeline && data.methodDataParsed) {{
                        loadScore(data);
                    }} else {{
                        alert("Invalid JSON data from URL: Missing 'timeline' or 'methodDataParsed'.");
                        resetPlaybackState();
                    }}
                }} catch (error) {{
                    alert("Error loading JSON from URL: " + error.message + "\\nMake sure the file is in the same directory as this HTML file.");
                    resetPlaybackState();
                }}
            }}

            function loadScore(data) {{
                resetPlaybackState();
                currentScoreData = data;
                // Create a *copy* of the timeline events to modify with offsets
                timelineEvents = JSON.parse(JSON.stringify(data.timeline));
                methodDataParsed = data.methodDataParsed;
                console.log("Score loaded:", currentScoreData);
                startButton.disabled = false;
                startButton.textContent = "START";
            }}

            function handlePresetSelection() {{
                const selectedPresetFile = jsonPresetSelect.value;
                if (selectedPresetFile !== 'none') {{
                    loadScoreFromUrl(selectedPresetFile);
                    jsonUploadInput.value = '';
                }} else {{
                    currentScoreData = null;
                    timelineEvents = [];
                    methodDataParsed = [];
                    startButton.disabled = true;
                    resetPlaybackState();
                }}
            }}

            function handleFileUpload(event) {{
                const file = event.target.files[0];
                if (file) {{
                    const reader = new FileReader();
                    reader.onload = (e) => {{
                        try {{
                            const data = JSON.parse(e.target.result);
                            if (data.timeline && data.methodDataParsed) {{
                                loadScore(data);
                                jsonPresetSelect.value = 'none';
                            }} else {{
                                alert("Invalid JSON file: Missing 'timeline' or 'methodDataParsed'.");
                                resetPlaybackState();
                            }}
                        }} catch (error) {{
                            alert("Error parsing JSON file: " + error.message);
                            resetPlaybackState();
                        }}
                    }};
                    reader.readAsText(file);
                }}
            }}

            function getBellOffsets() {{
                let offsets = {{}};
                let maxOffset = 0;
                bellOffsetInputs.forEach(input => {{
                    const bellNum = parseInt(input.id.replace('offset-bell-', ''));
                    const offset = parseFloat(input.value) || 0;
                    offsets[bellNum] = offset;
                    if (offset > maxOffset) {{
                        maxOffset = offset;
                    }}
                }});
                longestOffset = maxOffset;
                bellOffsets = offsets;
            }}

            function applyOffsetsToTimeline() {{
                getBellOffsets();

                if (!currentScoreData || currentScoreData.timeline.length === 0) return;

                timelineEvents = JSON.parse(JSON.stringify(currentScoreData.timeline));

                timelineEvents.forEach(event => {{
                    const bellOffset = bellOffsets[event.ringer] || 0;
                    const offsetDifference = longestOffset - bellOffset;

                    event.adjusted_absolute_time_start = event.absolute_time_start + offsetDifference;
                }});

                timelineEvents.sort((a, b) => a.adjusted_absolute_time_start - b.adjusted_absolute_time_start);
                console.log("Offsets applied. Adjusted timeline:", timelineEvents);
            }}

            function startTimeline() {{
                if (!currentScoreData || timelineEvents.length === 0) {{
                    alert("Please load a bell-ringing score first.");
                    return;
                }}

                applyOffsetsToTimeline();

                startupScreen.style.display = 'none';
                playbackScreen.style.display = 'flex';
                body.style.backgroundColor = '#333';

                startTime = performance.now();

                elapsedTimerIntervalId = setInterval(updateElapsedTime, 100);

                currentEventIndex = 0;
                scheduleNextEvent();
            }}

            function updateElapsedTime() {{
                const elapsedTimeMs = performance.now() - startTime;
                const totalSeconds = elapsedTimeMs / 1000;
                const minutes = Math.floor(totalSeconds / 60);
                const seconds = totalSeconds % 60;
                const formattedTime = `${{String(minutes).padStart(2, '0')}}:${{seconds.toFixed(2).padStart(5, '0')}}`;
                elapsedTimeDisplay.textContent = formattedTime;
            }}

            function scheduleNextEvent() {{
                if (currentEventIndex >= timelineEvents.length) {{
                    endTimeline();
                    return;
                }}

                const eventToSchedule = timelineEvents[currentEventIndex];
                const nextBellInTimeline = timelineEvents[currentEventIndex + 1];

                const targetFlashTime = startTime + eventToSchedule.adjusted_absolute_time_start * 1000;
                const delayUntilFlash = targetFlashTime - performance.now();

                if (countdownIntervalId) {{
                    clearInterval(countdownIntervalId);
                }}

                updateNextBellInfo(eventToSchedule); // Updates the single next bell display

                countdownIntervalId = setInterval(() => {{
                    const remainingTime = (targetFlashTime - performance.now()) / 1000;
                    if (remainingTime <= 0) {{
                        countdownTimer.textContent = '0.00';
                        clearInterval(countdownIntervalId);
                    }} else {{
                        countdownTimer.textContent = remainingTime.toFixed(2);
                    }}
                }}, 100);

                flashTimeoutId = setTimeout(() => {{
                    flashBell(eventToSchedule);
                    currentEventIndex++;
                    scheduleNextEvent();
                }}, Math.max(0, delayUntilFlash));
            }}

            function flashBell(event) {{
                const bellColor = BELL_COLORS[event.ringer] || '#888';
                body.style.backgroundColor = bellColor;
                currentBellDisplay.textContent = event.ringer;
                currentBellDisplay.style.display = 'block';

                currentRowDisplay.textContent = event.row;
                if (methodDataParsed[event.row - 1]) {{
                    methodRowDisplay.textContent = methodDataParsed[event.row - 1].join(' ');
                }} else {{
                    methodRowDisplay.textContent = '';
                }}

                setTimeout(() => {{
                    body.style.backgroundColor = '#333';
                    currentBellDisplay.style.display = 'none';
                }}, 1000); // Flash duration
            }}

            function updateNextBellInfo(event) {{
                const bellColor = BELL_COLORS[event.ringer] || '#888';
                const bellNumber = event.ringer;

                // Update the single next bell square (now centered)
                nextBellSquareCenter.style.backgroundColor = bellColor;
                nextBellSquareCenter.textContent = bellNumber;
                nextBellSquareCenter.style.color = (bellColor === '#FFFF00' || bellColor === '#FFC0CB') ? 'black' : 'white';

                // Handle 'END' state
                if (!event) {{
                    nextBellSquareCenter.style.backgroundColor = 'transparent';
                    nextBellSquareCenter.textContent = 'END';
                    nextBellSquareCenter.style.color = 'white';
                }}
            }}

            function endTimeline() {{
                resetPlaybackState();
                playbackScreen.style.display = 'none';
                startupScreen.style.display = 'flex';
            }}

            // --- Event Listeners ---
            startButton.addEventListener('click', startTimeline);
            jsonPresetSelect.addEventListener('change', handlePresetSelection);
            jsonUploadInput.addEventListener('change', handleFileUpload);

            bellOffsetInputs.forEach(input => {{
                input.addEventListener('change', applyOffsetsToTimeline);
                input.addEventListener('input', applyOffsetsToTimeline);
            }});

            document.addEventListener('keydown', (event) => {{
                if (event.code === 'Space' && startupScreen.style.display !== 'none' && !startButton.disabled) {{
                    event.preventDefault();
                    startTimeline();
                }}
            }});

            // Initial setup on page load
            document.addEventListener('DOMContentLoaded', () => {{
                resetPlaybackState();
                playbackScreen.style.display = 'none';
                startupScreen.style.display = 'flex';
                startButton.disabled = true;

                getBellOffsets();
            }});
        </script>
    </body>
    </html>
    """
    with open(filename, "w") as f:
        f.write(html_content)
    print(f"Bell conducting software saved to {filename}")

# --- Main execution to generate the HTML file ---
if __name__ == "__main__":
    # Default offsets for Python-side generation of HTML
    # These will be the initial values in the input boxes
    default_html_offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    generate_conducting_software_html(filename="bell_conducting_software.html")