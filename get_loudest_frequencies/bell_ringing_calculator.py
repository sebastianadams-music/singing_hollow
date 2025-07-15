import json
import math

def calculate_bell_ringing_timeline(
    num_ringers=6,
    initial_time_per_ring=0.5,
    total_rows=40,
    final_time_per_ring=10.0,
    curve_type="linear",
    ignore_first_n_rows=0,
    ignore_last_n_rows=0
):
    """
    Calculates the timing for a bell-ringing process with non-linear slowing,
    ignoring specified first and last rows for gradual change.

    Args:
        num_ringers (int): The number of people ringing bells.
        initial_time_per_ring (float): Time in seconds between rings in the first row.
        total_rows (int): The total number of rows in the bell-ringing method.
        final_time_per_ring (float): Time in seconds between rings in the last row.
        curve_type (str): The type of non-linear curve to use ('linear', 'ease_out_expo', 'ease_in_quad', etc.).
        ignore_first_n_rows (int): Number of initial rows to maintain at initial_time_per_ring.
        ignore_last_n_rows (int): Number of final rows to maintain at final_time_per_ring.

    Returns:
        dict: A dictionary containing:
            - 'timeline': A list of dictionaries, each representing a ring event.
            - 'total_duration': The total duration of the process in seconds.
    """

    timeline = []
    current_time_absolute = 0.0

    # Ensure valid 'n' values
    if ignore_first_n_rows < 0: ignore_first_n_rows = 0
    if ignore_last_n_rows < 0: ignore_last_n_rows = 0
    if ignore_first_n_rows + ignore_last_n_rows >= total_rows and total_rows > 0:
        # If all rows are ignored or there are too few rows for the ramp
        print("Warning: Sum of ignored rows is greater than or equal to total rows. Adjusting behavior.")
        ignore_first_n_rows = total_rows # All rows will be initial_time_per_ring
        ignore_last_n_rows = 0
        active_rows = 0
    else:
        active_rows = total_rows - ignore_first_n_rows - ignore_last_n_rows

    # Calculate the total range for the time between rings for the active phase
    time_range = final_time_per_ring - initial_time_per_ring


    for row_number in range(1, total_rows + 1):
        current_row_time_per_ring = 0.0

        if row_number <= ignore_first_n_rows:
            # First N rows: constant initial time
            current_row_time_per_ring = initial_time_per_ring
        elif row_number > (total_rows - ignore_last_n_rows):
            # Last N rows: constant final time
            current_row_time_per_ring = final_time_per_ring
        else:
            # Rows in the active (ramping) phase
            # Calculate progress within the active rows (0 to active_rows - 1)
            progress_in_active_rows = (row_number - 1) - ignore_first_n_rows

            # Normalize this progress to a 0-1 range for the curve function
            normalized_progress = progress_in_active_rows / (active_rows - 1) if active_rows > 1 else 0

            # Apply the non-linear curve function
            progress_on_curve = 0.0
            if curve_type == "ease_out_expo":
                progress_on_curve = 1 - math.pow(2, -10 * normalized_progress)
            elif curve_type == "ease_in_quad":
                progress_on_curve = normalized_progress * normalized_progress
            elif curve_type == "ease_in_out_sine":
                progress_on_curve = -0.5 * (math.cos(math.pi * normalized_progress) - 1)
            else: # Default to linear
                progress_on_curve = normalized_progress

            # Scale the progress on the curve back to the desired time range
            current_row_time_per_ring = initial_time_per_ring + (time_range * progress_on_curve)


        for ringer_index in range(1, num_ringers + 1):
            ring_event = {
                "row": row_number,
                "ringer": ringer_index,
                "time_between_rings_in_row": current_row_time_per_ring,
                "absolute_time_start": current_time_absolute
            }
            timeline.append(ring_event)
            current_time_absolute += current_row_time_per_ring

    # Handle single row/empty timeline cases for total_duration
    if not timeline:
        total_duration = 0.0
    else:
        # The total_duration is the absolute_time_start of the last event + its own duration
        total_duration = current_time_absolute - timeline[-1]["time_between_rings_in_row"]


    return {
        "timeline": timeline,
        "total_duration": total_duration
    }

def generate_html_visualization(data, initial_params, filename="bell_ringing_timeline.html"):
    """
    Generates an HTML file to visualize the bell-ringing timeline.
    """
    timeline_data_json = json.dumps(data["timeline"])
    total_duration = data["total_duration"]

    # Pass initial parameters to JavaScript for replication
    initial_num_ringers = initial_params['num_ringers']
    initial_time_per_ring = initial_params['initial_time_per_ring']
    initial_total_rows = initial_params['total_rows']
    initial_final_time_per_ring = initial_params['final_time_per_ring']
    initial_curve_type = initial_params['curve_type']
    initial_ignore_first_n_rows = initial_params['ignore_first_n_rows']
    initial_ignore_last_n_rows = initial_params['ignore_last_n_rows']


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
            #parameters {{ background-color: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
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
            button {{ padding: 10px 15px; background-color: #007BFF; color: white; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;}} /* Added margin-right for buttons */
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
            <h2>Adjust Parameters</h2>
            <div>
                <label for="numRingers">Number of Ringers:</label>
                <input type="number" id="numRingers" value="{initial_num_ringers}" min="1">
            </div>
            <div>
                <label for="initialTimePerRing">Initial Time Per Ring (seconds):</label>
                <input type="number" id="initialTimePerRing" value="{initial_time_per_ring}" step="0.1" min="0.1">
            </div>
            <div>
                <label for="totalRows">Total Rows:</label>
                <input type="number" id="totalRows" value="{initial_total_rows}" min="1">
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
            <div>
                <label for="curveType">Slowing Curve Type:</label>
                <select id="curveType">
                    <option value="linear" {'selected' if initial_curve_type == 'linear' else ''}>Linear</option>
                    <option value="ease_out_expo" {'selected' if initial_curve_type == 'ease_out_expo' else ''}>Ease Out Exponential</option>
                    <option value="ease_in_quad" {'selected' if initial_curve_type == 'ease_in_quad' else ''}>Ease In Quadratic</option>
                    <option value="ease_in_out_sine" {'selected' if initial_curve_type == 'ease_in_out_sine' else ''}>Ease In/Out Sine</option>
                </select>
            </div>
            <button onclick="updateTimeline()">Update Timeline</button>
            <button onclick="exportToJson()">Export to JSON</button> </div>

        <div id="summary">
            <h2>Process Summary</h2>
            <p>Total Duration: <strong id="totalDurationDisplay">{total_duration:.2f} seconds</strong></p>
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

            function renderTimeline(timelineData, totalDuration) {{
                const container = document.getElementById('timeline-container');
                container.innerHTML = ''; // Clear previous timeline
                const totalHeight = totalDuration * 10; // Scale: 10 pixels per second (adjust as needed)
                container.style.height = Math.max(600, totalHeight + 50) + 'px'; // Ensure minimum height and expand with duration

                // Display total duration
                document.getElementById('totalDurationDisplay').textContent = formatTime(totalDuration);

                timelineData.forEach(event => {{
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'ring-event';
                    // Position based on absolute_time_start
                    eventDiv.style.top = (event.absolute_time_start * 10) + 'px'; // 10px per second scaling

                    // Content of the event
                    eventDiv.innerHTML = `
                        Row: ${{event.row}}, Ringer: ${{event.ringer}}
                        <div class="tooltip">
                            Time in Row: ${{event.time_between_rings_in_row.toFixed(2)}}s<br>
                            Abs. Start: ${{formatTime(event.absolute_time_start)}}
                        </div>
                    `;
                    container.appendChild(eventDiv);
                }});
            }}

            function updateTimeline() {{
                const numRingers = parseInt(document.getElementById('numRingers').value);
                const initialTimePerRing = parseFloat(document.getElementById('initialTimePerRing').value);
                const totalRows = parseInt(document.getElementById('totalRows').value);
                const finalTimePerRing = parseFloat(document.getElementById('finalTimePerRing').value);
                const ignoreFirstNRows = parseInt(document.getElementById('ignoreFirstNRows').value);
                const ignoreLastNRows = parseInt(document.getElementById('ignoreLastNRows').value);
                const curveType = document.getElementById('curveType').value;

                let newTimeline = [];
                let currentAbsoluteTime = 0.0;

                // Ensure valid 'n' values
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

                for (let rowNumber = 1; rowNumber <= totalRows; rowNumber++) {{
                    let currentRowTimePerRing;

                    if (rowNumber <= actualIgnoreFirstNRows) {{
                        currentRowTimePerRing = initialTimePerRing;
                    }} else if (rowNumber > (totalRows - actualIgnoreLastNRows)) {{
                        currentRowTimePerRing = finalTimePerRing;
                    }} else {{
                        // Calculate progress within the active rows
                        const progressInActiveRows = (rowNumber - 1) - actualIgnoreFirstNRows;

                        // Normalize this progress to a 0-1 range for the curve function
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

                    for (let ringerIndex = 1; ringerIndex <= numRingers; ringerIndex++) {{
                        newTimeline.push({{
                            row: rowNumber,
                            ringer: ringerIndex,
                            time_between_rings_in_row: currentRowTimePerRing,
                            absolute_time_start: currentAbsoluteTime
                        }});
                        currentAbsoluteTime += currentRowTimePerRing;
                    }}
                }}
                let newTotalDuration = currentAbsoluteTime;
                if (newTimeline.length > 0) {{
                    newTotalDuration = currentAbsoluteTime - newTimeline[newTimeline.length - 1].time_between_rings_in_row;
                }} else {{
                    newTotalDuration = 0;
                }}

                currentTimelineData = newTimeline; // Update global variable
                currentTotalDuration = newTotalDuration; // Update global variable
                renderTimeline(currentTimelineData, currentTotalDuration);
            }}

            // NEW FUNCTION: Export timeline data to JSON
            function exportToJson() {{
                const dataStr = JSON.stringify(currentTimelineData, null, 2); // Pretty print JSON
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

                const exportFileDefaultName = 'bell_ringing_timeline.json';

                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportFileDefaultName);
                linkElement.click(); // Programmatically click the link to trigger download
                linkElement.remove(); // Clean up the temporary link
            }}


            // Initial render
            document.addEventListener('DOMContentLoaded', () => {{
                renderTimeline(currentTimelineData, currentTotalDuration);
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
    ignore_first_n_rows = 5
    ignore_last_n_rows = 5

    initial_params = {
        'num_ringers': num_ringers,
        'initial_time_per_ring': initial_time_per_ring,
        'total_rows': total_rows,
        'final_time_per_ring': final_time_per_ring,
        'curve_type': curve_type,
        'ignore_first_n_rows': ignore_first_n_rows,
        'ignore_last_n_rows': ignore_last_n_rows
    }

    # Calculate initial data
    initial_data = calculate_bell_ringing_timeline(
        **initial_params
    )

    # Generate the HTML file
    generate_html_visualization(
        initial_data,
        initial_params,
        filename="bell_ringing_timeline.html"
    )