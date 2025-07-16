import json
import math

def calculate_bell_ringing_timeline(
    num_ringers=6,
    initial_time_per_ring=0.5,
    total_rows=40,
    final_time_per_ring=10.0,
    curve_type="linear",
    ignore_first_n_rows=0,
    ignore_last_n_rows=0,
    method_data=None # New parameter for method input
):
    """
    Calculates the timing for a bell-ringing process with non-linear slowing,
    ignoring specified first and last rows for gradual change, and using a
    specified bell-ringing method.

    Args:
        num_ringers (int): The number of people ringing bells. (Will be derived from method_data if provided)
        initial_time_per_ring (float): Time in seconds between rings in the first row.
        total_rows (int): The total number of rows in the bell-ringing method. (Will be derived from method_data if provided)
        final_time_per_ring (float): Time in seconds between rings in the last row.
        curve_type (str): The type of non-linear curve to use ('linear', 'ease_out_expo', 'ease_in_quad', etc.).
        ignore_first_n_rows (int): Number of initial rows to maintain at initial_time_per_ring.
        ignore_last_n_rows (int): Number of final rows to maintain at final_time_per_ring.
        method_data (list of list of int): A 2D list representing the bell-ringing method,
                                          where each inner list is a row of ringer numbers.

    Returns:
        dict: A dictionary containing:
            - 'timeline': A list of dictionaries, each representing a ring event.
            - 'total_duration': The total duration of the process in seconds.
            - 'method_data': The parsed method data used.
    """

    timeline = []
    current_time_absolute = 0.0

    # Override total_rows and num_ringers if method_data is provided
    if method_data:
        total_rows = len(method_data)
        if total_rows > 0:
            num_ringers = len(method_data[0])
        else:
            num_ringers = 0 # No rows, no ringers
    elif total_rows == 0: # If no method_data and total_rows is 0
        num_ringers = 0

    if total_rows == 0 or num_ringers == 0:
        return {
            "timeline": [],
            "total_duration": 0.0,
            "method_data": method_data if method_data else []
        }

    # Ensure valid 'n' values
    if ignore_first_n_rows < 0: ignore_first_n_rows = 0
    if ignore_last_n_rows < 0: ignore_last_n_rows = 0
    if ignore_first_n_rows + ignore_last_n_rows >= total_rows and total_rows > 0:
        print("Warning: Sum of ignored rows is greater than or equal to total rows. Adjusting behavior.")
        ignore_first_n_rows = total_rows # All rows will be initial_time_per_ring
        ignore_last_n_rows = 0
        active_rows = 0
    else:
        active_rows = total_rows - ignore_first_n_rows - ignore_last_n_rows

    # Calculate the total range for the time between rings for the active phase
    time_range = final_time_per_ring - initial_time_per_ring


    for row_idx in range(total_rows):
        row_number = row_idx + 1 # 1-indexed row number
        current_row_time_per_ring = 0.0

        if row_number <= ignore_first_n_rows:
            # First N rows: constant initial time
            current_row_time_per_ring = initial_time_per_ring
        elif row_number > (total_rows - ignore_last_n_rows):
            # Last N rows: constant final time
            current_row_time_per_ring = final_time_per_ring
        else:
            # Rows in the active (ramping) phase
            progress_in_active_rows = (row_idx) - ignore_first_n_rows # Use 0-indexed row for calculation in active phase

            normalized_progress = progress_in_active_rows / (active_rows - 1) if active_rows > 1 else 0

            progress_on_curve = 0.0
            if curve_type == "ease_out_expo":
                progress_on_curve = 1 - math.pow(2, -10 * normalized_progress)
            elif curve_type == "ease_in_quad":
                progress_on_curve = normalized_progress * normalized_progress
            elif curve_type == "ease_in_out_sine":
                progress_on_curve = -0.5 * (math.cos(math.pi * normalized_progress) - 1)
            else: # Default to linear
                progress_on_curve = normalized_progress

            current_row_time_per_ring = initial_time_per_ring + (time_range * progress_on_curve)

        # Iterate through ringers based on method_data for the current row
        current_row_ringers = method_data[row_idx] if method_data and row_idx < len(method_data) else list(range(1, num_ringers + 1))

        # NEW: Add position_in_row
        for position_in_row, ringer_num_in_method in enumerate(current_row_ringers, 1): # Start enumerate from 1
            ring_event = {
                "row": row_number,
                "ringer": ringer_num_in_method, # Use actual ringer number from method
                "position_in_row": position_in_row, # New field
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
        "method_data": method_data if method_data else [] # Include method data in output
    }

def generate_html_visualization(data, initial_params, filename="bell_ringing_timeline.html"):
    """
    Generates an HTML file to visualize the bell-ringing timeline.
    """
    timeline_data_json = json.dumps(data["timeline"])
    total_duration = data["total_duration"]
    initial_method_data_json = json.dumps(data.get("method_data", []))

    initial_time_per_ring = initial_params['initial_time_per_ring']
    initial_final_time_per_ring = initial_params['final_time_per_ring']
    initial_curve_type = initial_params['curve_type']
    initial_ignore_first_n_rows = initial_params['ignore_first_n_rows']
    initial_ignore_last_n_rows = initial_params['ignore_last_n_rows']
    initial_method_text = initial_params['method_text']

    initial_detected_num_ringers = len(data["method_data"][0]) if data.get("method_data") and data["method_data"] else initial_params['num_ringers']
    initial_detected_total_rows = len(data["method_data"]) if data.get("method_data") else initial_params['total_rows']

    initial_input_num_ringers = initial_params['num_ringers']
    initial_input_total_rows = initial_params['total_rows']


    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bell Ringing Timeline</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            #parameters {{ background-color: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            #parameters > div {{ display: flex; flex-direction: column; }}
            #parameters .full-width {{ grid-column: span 2; }}
            textarea {{ width: 100%; min-height: 150px; font-family: monospace; border: 1px solid #ccc; border-radius: 4px; padding: 8px; }}
            #timeline-container {{ position: relative; width: 100%; height: 600px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }}
            .ring-event {{
                position: absolute;
                background-color: #4CAF50; /* Green */
                color: white;
                padding: 3px 6px;
                border-radius: 3px;
                font-size: 0.8em;
                white-space: nowrap;
                left: 0; /* Align all events to the left for a linear timeline */
                width: fit-content;
                box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
            }}
            .ring-event:nth-child(even) {{ background-color: #2196F3; /* Blue for even */ }}
            .tooltip {{
                position: absolute;
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px;
                border-radius: 5px;
                font-size: 0.7em;
                display: none;
                z-index: 100;
            }}
            .ring-event:hover .tooltip {{ display: block; }}
            #summary {{ margin-top: 20px; padding: 10px; background-color: #e6f7ff; border-left: 5px solid #2196F3; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="number"], select {{ padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; width: 150px; }}
            .button-group {{ grid-column: span 2; text-align: right; }}
            button {{ padding: 10px 15px; background-color: #007BFF; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;}}
            button:hover {{ background-color: #0056b3; }}

            /* Legend for colors */
            .legend-item {{ display: inline-block; margin-right: 20px; }}
            .legend-color {{ display: inline-block; width: 15px; height: 15px; margin-right: 5px; border-radius: 3px; }}
            .legend-green {{ background-color: #4CAF50; }}
            .legend-blue {{ background-color: #2196F3; }}
        </style>
    </head>
    <body>
        <h1>Bell Ringing Timeline Visualizer</h1>

        <div id="parameters">
            <div>
                <label for="numRingers">Number of Ringers:</label>
                <input type="number" id="numRingers" value="{initial_input_num_ringers}" min="1" {'disabled' if initial_method_data_json != '[]' else ''}>
            </div>
            <div>
                <label for="initialTimePerRing">Initial Time Per Ring (seconds):</label>
                <input type="number" id="initialTimePerRing" value="{initial_time_per_ring}" step="0.1" min="0.1">
            </div>
            <div>
                <label for="totalRows">Total Rows:</label>
                <input type="number" id="totalRows" value="{initial_input_total_rows}" min="1" {'disabled' if initial_method_data_json != '[]' else ''}>
            </div>
            <div>
                <label for="finalTimePerRing">Final Time Per Ring (seconds):</label>
                <input type="number" id="finalTimePerRing" value="{initial_final_time_per_ring}" step="0.1" min="0.1">
            </div>
            <div>
                <label for="ignoreFirstNRows">Ignore First N Rows (constant initial time):</label>
                <input type="number" id="ignoreFirstNRows" value="{initial_ignore_first_n_rows}" min="0">
            </div>
            <div>
                <label for="ignoreLastNRows">Ignore Last N Rows (constant final time):</label>
                <input type="number" id="ignoreLastNRows" value="{initial_ignore_last_n_rows}" min="0">
            </div>
            <div class="full-width">
                <label for="curveType">Slowing Curve Type:</label>
                <select id="curveType">
                    <option value="linear" {'selected' if initial_curve_type == 'linear' else ''}>Linear</option>
                    <option value="ease_out_expo" {'selected' if initial_curve_type == 'ease_out_expo' else ''}>Ease Out Exponential</option>
                    <option value="ease_in_quad" {'selected' if initial_curve_type == 'ease_in_quad' else ''}>Ease In Quadratic</option>
                    <option value="ease_in_out_sine" {'selected' if initial_curve_type == 'ease_in_out_sine' else ''}>Ease In/Out Sine</option>
                </select>
            </div>
            <div class="full-width">
                <label for="methodInput">Bell-Ringing Method (each line is a row, space-separated ringers):</label>
                <textarea id="methodInput" placeholder="e.g.,
1 2 3 4 5 6
2 1 4 3 5 6
...">{initial_method_text}</textarea>
                <small>Number of Ringers and Total Rows will be determined by this input if provided.</small>
            </div>
            <div class="button-group">
                <button onclick="updateTimeline()">Update Timeline</button>
                <button onclick="exportToJson()">Export to JSON</button>
            </div>
        </div>

        <div id="summary">
            <h2>Process Summary</h2>
            <p>Total Duration: <strong id="totalDurationDisplay">{total_duration:.2f} seconds</strong></p>
            <p>Detected Number of Ringers: <strong id="detectedNumRingers">{initial_detected_num_ringers}</strong></p>
            <p>Detected Total Rows: <strong id="detectedTotalRows">{initial_detected_total_rows}</strong></p>
        </div>

        <h2>Visual Timeline Overview</h2>
        <div class="legend">
            <div class="legend-item"><span class="legend-color legend-green"></span> Odd Ringer Index</div>
            <div class="legend-item"><span class="legend-color legend-blue"></span> Even Ringer Index</div>
        </div>
        <div id="timeline-container">
            </div>

        <script>
            // Helper function for non-linear easing functions
            function easeOutExpo(t) {{
                return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
            }}

            function easeInQuad(t) {{
                return t * t;
            }}

            function easeInOutSine(t) {{
                return -0.5 * (Math.cos(Math.PI * t) - 1);
            }}

            function formatTime(seconds) {{
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                return `${{minutes}}m ${{remainingSeconds.toFixed(2)}}s`;
            }}

            let currentTimelineData = {timeline_data_json}; // Global variable to hold current data
            let currentTotalDuration = {total_duration}; // Global variable to hold current duration
            let currentMethodData = {initial_method_data_json}; // Global variable to hold current method data (parsed from Python)

            function parseMethodInput(methodText) {{
                const rows = methodText.trim().split('\\n');
                if (rows.length === 0 || (rows.length === 1 && rows[0].trim() === '')) {{
                    return []; // Return empty if no valid input
                }}
                const parsedMethod = rows.map(row => {{
                    return row.trim().split(/\\s+/).filter(Boolean).map(Number); // Split by space, filter empty strings, convert to numbers
                }}).filter(row => row.length > 0); // Remove any completely empty rows

                // Basic validation: ensure all rows have the same number of ringers
                if (parsedMethod.length > 1) {{
                    const firstRowRingerCount = parsedMethod[0].length;
                    for (let i = 1; i < parsedMethod.length; i++) {{
                        if (parsedMethod[i].length !== firstRowRingerCount) {{
                            console.warn("Method input error: Rows have inconsistent number of ringers. Proceeding with first row count.");
                            // For simplicity, we'll proceed but this might cause unexpected behavior
                            // A more robust solution might truncate or pad rows, or block calculation.
                        }}
                    }}
                }}
                return parsedMethod;
            }}

            function renderTimeline(timelineData, totalDuration, detectedNumRingers, detectedTotalRows) {{
                const container = document.getElementById('timeline-container');
                container.innerHTML = ''; // Clear previous timeline
                const totalHeight = totalDuration * 10; // Scale: 10 pixels per second (adjust as needed)
                container.style.height = Math.max(600, totalHeight + 50) + 'px'; // Ensure minimum height and expand with duration

                // Display summary info
                document.getElementById('totalDurationDisplay').textContent = formatTime(totalDuration);
                document.getElementById('detectedNumRingers').textContent = detectedNumRingers;
                document.getElementById('detectedTotalRows').textContent = detectedTotalRows;

                timelineData.forEach(event => {{
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'ring-event';
                    // Position based on absolute_time_start
                    eventDiv.style.top = (event.absolute_time_start * 10) + 'px'; // 10px per second scaling

                    // Content of the event: Now uses actual ringer number and position in row
                    eventDiv.innerHTML = `
                        Row: ${{event.row}}, Ringer: ${{event.ringer}} (#${{event.position_in_row}})
                        <div class="tooltip">
                            Time in Row: ${{event.time_between_rings_in_row.toFixed(2)}}s<br>
                            Abs. Start: ${{formatTime(event.absolute_time_start)}}<br>
                            Position in Row: ${{event.position_in_row}}
                        </div>
                    `;
                    container.appendChild(eventDiv);
                }});
            }}

            function updateTimeline() {{
                const initialTimePerRing = parseFloat(document.getElementById('initialTimePerRing').value);
                const finalTimePerRing = parseFloat(document.getElementById('finalTimePerRing').value);
                const ignoreFirstNRows = parseInt(document.getElementById('ignoreFirstNRows').value);
                const ignoreLastNRows = parseInt(document.getElementById('ignoreLastNRows').value);
                const curveType = document.getElementById('curveType').value;
                const methodTextInput = document.getElementById('methodInput').value;

                let numRingers;
                let totalRows;
                let methodData = parseMethodInput(methodTextInput);

                const numRingersInput = document.getElementById('numRingers');
                const totalRowsInput = document.getElementById('totalRows');

                if (methodData.length > 0 && methodData[0].length > 0) {{
                    totalRows = methodData.length;
                    numRingers = methodData[0].length;
                    numRingersInput.disabled = true;
                    totalRowsInput.disabled = true;
                }} else {{
                    numRingers = parseInt(numRingersInput.value) || 6;
                    totalRows = parseInt(totalRowsInput.value) || 40;
                    numRingersInput.disabled = false;
                    totalRowsInput.disabled = false;
                    methodData = []; // Ensure empty if not parsed
                }}

                let newTimeline = [];
                let currentAbsoluteTime = 0.0;

                let actualIgnoreFirstNRows = Math.max(0, ignoreFirstNRows);
                let actualIgnoreLastNRows = Math.max(0, ignoreLastNRows);

                let activeRows = totalRows - actualIgnoreFirstNRows - actualIgnoreLastNRows;
                if (activeRows < 0) {{
                    console.warn("Sum of ignored rows exceeds total rows. Adjusting to all initial time.");
                    actualIgnoreFirstNRows = totalRows;
                    actualIgnoreLastNRows = 0;
                    activeRows = 0;
                }}

                const timeRange = finalTimePerRing - initialTimePerRing;

                for (let rowIdx = 0; rowIdx < totalRows; rowIdx++) {{
                    let rowNumber = rowIdx + 1; // 1-indexed row number
                    let currentRowTimePerRing;

                    if (rowNumber <= actualIgnoreFirstNRows) {{
                        currentRowTimePerRing = initialTimePerRing;
                    }} else if (rowNumber > (totalRows - actualIgnoreLastNRows)) {{
                        currentRowTimePerRing = finalTimePerRing;
                    }} else {{
                        const progressInActiveRows = rowIdx - actualIgnoreFirstNRows;

                        let normalizedProgress;
                        if (activeRows > 1) {{
                            normalizedProgress = progressInActiveRows / (activeRows - 1);
                        }} else {{
                            normalizedProgress = 0;
                        }}

                        let progressOnCurve;
                        if (curveType === "ease_out_expo") {{
                            progressOnCurve = easeOutExpo(normalizedProgress);
                        }} else if (curveType === "ease_in_quad") {{
                            progressOnCurve = easeInQuad(normalizedProgress);
                        }} else if (curveType === "ease_in_out_sine") {{
                            progressOnCurve = easeInOutSine(normalizedProgress);
                        }} else {{ // linear
                            progressOnCurve = normalizedProgress;
                        }}

                        currentRowTimePerRing = initialTimePerRing + (timeRange * progressOnCurve);
                    }}

                    let currentRingersInOrder = methodData[rowIdx] || Array.from({{length: numRingers}}, (_, i) => i + 1);

                    // NEW: Add position_in_row
                    currentRingersInOrder.forEach((ringer, index) => {{
                        const position_in_row = index + 1; // 1-indexed position
                        newTimeline.push({{
                            row: rowNumber,
                            ringer: ringer,
                            position_in_row: position_in_row, // New field
                            time_between_rings_in_row: currentRowTimePerRing,
                            absolute_time_start: currentAbsoluteTime
                        }});
                        currentAbsoluteTime += currentRowTimePerRing;
                    }});
                }}

                let newTotalDuration = currentAbsoluteTime;
                if (newTimeline.length > 0) {{
                    newTotalDuration = currentAbsoluteTime - newTimeline[newTimeline.length - 1].time_between_rings_in_row;
                }} else {{
                    newTotalDuration = 0;
                }}

                currentTimelineData = newTimeline;
                currentTotalDuration = newTotalDuration;
                currentMethodData = methodData;

                renderTimeline(currentTimelineData, currentTotalDuration, numRingers, totalRows);
            }}

            function exportToJson() {{
                const exportData = {{
                    parameters: {{
                        numRingers: parseInt(document.getElementById('numRingers').value),
                        initialTimePerRing: parseFloat(document.getElementById('initialTimePerRing').value),
                        totalRows: parseInt(document.getElementById('totalRows').value),
                        finalTimePerRing: parseFloat(document.getElementById('finalTimePerRing').value),
                        ignoreFirstNRows: parseInt(document.getElementById('ignoreFirstNRows').value),
                        ignoreLastNRows: parseInt(document.getElementById('ignoreLastNRows').value),
                        curveType: document.getElementById('curveType').value,
                        methodText: document.getElementById('methodInput').value
                    }},
                    summary: {{
                        totalDuration: currentTotalDuration,
                        detectedNumRingers: parseInt(document.getElementById('detectedNumRingers').textContent),
                        detectedTotalRows: parseInt(document.getElementById('detectedTotalRows').textContent)
                    }},
                    methodDataParsed: currentMethodData,
                    timeline: currentTimelineData
                }};

                const dataStr = JSON.stringify(exportData, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

                const exportFileDefaultName = 'bell_ringing_timeline.json';

                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportFileDefaultName);
                linkElement.click();
                linkElement.remove();
            }}

            // Initial render
            document.addEventListener('DOMContentLoaded', () => {{
                updateTimeline();
            }});
        </script>
    </body>
    </html>
    """
    with open(filename, "w") as f:
        f.write(html_content)
    print(f"Visualization saved to {filename}")

# --- Main execution ---
if __name__ == "__main__":
    # Default parameters
    num_ringers = 6
    initial_time_per_ring = 0.5
    total_rows = 40
    final_time_per_ring = 10.0
    curve_type = "linear" # Or "ease_out_expo", "ease_in_quad", "ease_in_out_sine"
    ignore_first_n_rows = 0
    ignore_last_n_rows = 0

    # Example method input - Your provided example
    example_method = """1 2 3 4 5 6
2 1 4 3 5 6
2 4 1 5 3 6
4 2 5 1 3 6
4 5 2 3 1 6
5 4 3 2 1 6
5 3 4 1 2 6
3 5 1 4 2 6
3 1 5 2 4 6
1 3 2 5 4 6
1 2 3 4 5 6"""

    # Parse the example method for initial data calculation (Python side)
    initial_method_data = []
    if example_method:
        rows = example_method.strip().split('\n')
        for row_str in rows:
            ringers = [int(x) for x in row_str.strip().split(' ') if x.strip()]
            if ringers:
                initial_method_data.append(ringers)
    
    # If no method is provided, or method is empty, ensure default num_ringers and total_rows are used for parameters
    # This ensures the `value` attribute of the input fields is correct initially.
    if not initial_method_data:
        initial_input_num_ringers = num_ringers
        initial_input_total_rows = total_rows
    else:
        initial_input_num_ringers = len(initial_method_data[0]) if initial_method_data else num_ringers
        initial_input_total_rows = len(initial_method_data)

    params_for_calculation = {
        'num_ringers': initial_input_num_ringers,
        'initial_time_per_ring': initial_time_per_ring,
        'total_rows': initial_input_total_rows,
        'final_time_per_ring': final_time_per_ring,
        'curve_type': curve_type,
        'ignore_first_n_rows': ignore_first_n_rows,
        'ignore_last_n_rows': ignore_last_n_rows,
    }

    initial_params_for_html = {
        'num_ringers': initial_input_num_ringers,
        'initial_time_per_ring': initial_time_per_ring,
        'total_rows': initial_input_total_rows,
        'final_time_per_ring': final_time_per_ring,
        'curve_type': curve_type,
        'ignore_first_n_rows': ignore_first_n_rows,
        'ignore_last_n_rows': ignore_last_n_rows,
        'method_text': example_method
    }

    # Calculate initial data using the parsed method_data (if available)
    initial_data = calculate_bell_ringing_timeline(
        **params_for_calculation,
        method_data=initial_method_data
    )

    # Generate the HTML file
    generate_html_visualization(
        initial_data,
        initial_params_for_html,
        filename="bell_ringing_timeline.html"
    )