const express = require('express');
const path = require('path');
const { exec, spawn } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = 3000;
const RECORD_DURATION_SECONDS = 5;
// Removed fixed TIMER_INTERVAL_SECONDS constant, as it's now dynamic
const DURATION_UPDATE_INTERVAL_SECONDS = 180; // How often material durations update (1 minute)
const AUDIO_FILE_PATH = path.join(__dirname, 'recorded_audio.wav');
const NOTES_JSON_PATH = path.join(__dirname, 'notes.json');

// --- Absolute Paths for Executables (IMPROVED ROBUSTNESS) ---
// CONFIRM THESE PATHS ARE CORRECT ON YOUR SYSTEM!
const FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"; // From 'which ffmpeg'
const PYTHON_PATH = "/Volumes/seb/Documents/Projects/1Active/singing_hollow/get_loudest_frequencies/.venv/bin/python"; // From 'which python' in activated venv
const LILYPOND_PATH = "/opt/homebrew/bin/lilypond"; // Assuming Homebrew install, verify with 'which lilypond'

// --- FFmpeg Device Index (CRITICAL: ENSURE THIS IS CORRECT) ---
const FFMPEG_DEVICE_INDEX = ":3"; // You confirmed this for your Focusrite. MAKE SURE IT'S ":3" in your actual file!

// --- New Testing Mode Switch ---
// Set to `true` to force 5-second interval for audio processing cycle.
// Set to `false` to use random 5-60 second interval.
const IS_TESTING_MODE = false; // <--- Set this to true or false as needed

if (!fs.existsSync(path.join(__dirname, 'public'))) {
    fs.mkdirSync(path.join(__dirname, 'public'));
}

app.use(express.static('public'));

let currentStatusMessage = '';
// New: Store the current material durations
const POSSIBLE_DURATIONS = [3, 5, 8, 13, 21, 34, 59];
let currentMaterialDurations = []; // Will store the generated durations

// Function to generate random durations for the 6 segments
function generateRandomMaterialDurations() {
    const newDurations = [];
    for (let i = 0; i < 6; i++) { // Assuming 6 segments
        const randomIndex = Math.floor(Math.random() * POSSIBLE_DURATIONS.length);
        newDurations.push(POSSIBLE_DURATIONS[randomIndex]);
    }
    currentMaterialDurations = newDurations;
    console.log("Generated new material durations:", currentMaterialDurations);
}


async function processAudioAndGenerateSVG() {
    console.log('--- Starting Audio Processing Cycle ---');
    let cycleSuccess = true;

    try {
        const scriptDir = __dirname;

        // 1. Set initial message: "Stop Playing!"
        currentStatusMessage = 'Stop Playing!';
        console.log(`Status: ${currentStatusMessage}`);

        // --- Recording bells ---
        currentStatusMessage = 'Recording bells...';
        console.log(`Status: ${currentStatusMessage}`);
        console.log(`Recording audio for ${RECORD_DURATION_SECONDS} seconds using FFmpeg...`);

        const recordArgs = [
            '-f', 'avfoundation',
            '-i', FFMPEG_DEVICE_INDEX, // Corrected variable name here
            '-t', RECORD_DURATION_SECONDS.toString(),
            '-ar', '48000',
            '-ac', '1',
            '-y',
            AUDIO_FILE_PATH,
            '-nostats',
            '-loglevel', 'debug'
        ];


        await new Promise((resolve, reject) => {
            console.log(`FFmpeg Command: ${FFMPEG_PATH} ${recordArgs.join(' ')}`);
            const ffmpegChild = spawn(FFMPEG_PATH, recordArgs, { cwd: scriptDir });

            let ffmpegErrorOutput = '';
            ffmpegChild.stderr.on('data', (data) => {
                const output = data.toString();
                console.warn(`FFmpeg stderr: ${output}`);
                ffmpegErrorOutput += output;
            });

            ffmpegChild.on('close', (code) => {
                if (code === 0) {
                    console.log('Audio recording complete (via FFmpeg spawn).');
                    resolve();
                } else {
                    const errorMsg = `FFmpeg process exited with code ${code}. Stderr: ${ffmpegErrorOutput.substring(0, 500)}...`;
                    console.error(`Recording failed: ${errorMsg}`);
                    reject(new Error(errorMsg));
                }
            });

            ffmpegChild.on('error', (err) => {
                console.error(`Failed to start FFmpeg process: ${err.message}`);
                reject(err);
            });
        });

        // --- Analysing bells ---
        currentStatusMessage = 'Analysing bells...';
        console.log(`Status: ${currentStatusMessage}`);
        console.log('Analyzing audio...');

        const analyzeCommand = `${PYTHON_PATH} ${path.join(__dirname, 'analyze_audio.py')} ${AUDIO_FILE_PATH} --output_json ${NOTES_JSON_PATH} --constrain_octave_start_note C4`;
        await new Promise((resolve, reject) => {
            exec(analyzeCommand, { cwd: scriptDir }, (error, stdout, stderr) => {
                if (error) {
                    const errorMsg = `Audio analysis command failed: ${error.message}. Stderr: ${stderr.substring(0, 500)}...`;
                    console.error(`Analysis failed: ${errorMsg}`);
                    return reject(new Error(errorMsg));
                }
                if (stderr) {
                    console.warn(`Analysis stderr: ${stderr}`);
                }
                console.log('Audio analysis complete.');
                console.log('Analysis stdout:', stdout);
                resolve();
            });
        });

        // --- Generate new LilyPond SVG ---
        console.log('Generating new LilyPond SVG...');
        const generateNodeCommand = `node generate_lilypond.js`;
        await new Promise((resolve, reject) => {
            exec(generateNodeCommand, { cwd: scriptDir }, (error, stdout, stderr) => {
                if (error) {
                    const errorMsg = `LilyPond generation command failed: ${error.message}. Stderr: ${stderr.substring(0, 500)}...`;
                    console.error(`LilyPond generation failed: ${errorMsg}`);
                    return reject(new Error(errorMsg));
                }
                if (stderr) {
                    console.warn(`LilyPond generation stderr: ${stderr}`);
                }
                console.log('LilyPond SVG generation complete.');
                console.log('LilyPond stdout:', stdout);
                resolve();
            });
        });

        // Full cycle successful
        currentStatusMessage = ''; // Clear message
        console.log('--- Audio Processing Cycle Complete ---');

    } catch (err) {
        cycleSuccess = false;
        console.error('An error occurred during the processing cycle:', err);
        currentStatusMessage = `Cycle Error: ${err.message.substring(0, 70)}...`;
    } finally {
        startProcessingTimer(); // Schedule next cycle with a random delay or fixed delay
    }
}

let processingTimer;
let durationUpdateTimer;

// Function to calculate a random interval between 5 and 60 seconds (in 5-second steps)
function getRandomAudioCycleInterval() {
    const minSeconds = 5;
    const maxSeconds = 60;
    const step = 5;

    const numberOfSteps = (maxSeconds - minSeconds) / step + 1;
    const randomStep = Math.floor(Math.random() * numberOfSteps); // 0 to 11
    const randomInterval = minSeconds + (randomStep * step); // 5, 10, ..., 60

    return randomInterval;
}


function startProcessingTimer() {
    if (processingTimer) {
        clearTimeout(processingTimer);
    }

    let nextInterval;
    if (IS_TESTING_MODE) {
        nextInterval = 5; // Force 5 seconds in testing mode
    } else {
        nextInterval = getRandomAudioCycleInterval(); // Use random interval in normal mode
    }

    processingTimer = setTimeout(async () => {
        await processAudioAndGenerateSVG();
    }, nextInterval * 1000); // Convert seconds to milliseconds
    console.log(`Next audio processing cycle scheduled in ${nextInterval} seconds.`);
}

function startDurationUpdateTimer() {
    if (durationUpdateTimer) {
        clearTimeout(durationUpdateTimer);
    }

    // Generate durations immediately on first call
    generateRandomMaterialDurations();

    durationUpdateTimer = setTimeout(() => {
        startDurationUpdateTimer(); // Call itself to loop
    }, DURATION_UPDATE_INTERVAL_SECONDS * 1000);
    console.log(`Next material durations update scheduled in ${DURATION_UPDATE_INTERVAL_SECONDS} seconds.`);
}


// --- API endpoints ---
app.get('/status', (req, res) => {
    res.json({ status: currentStatusMessage });
});

app.get('/durations', (req, res) => {
    res.json({ durations: currentMaterialDurations });
});


// --- Express Routes ---
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynamic LilyPond SVG</title>
            <style>
                body {
                    font-family: sans-serif;
                    background: #f0f0f0;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding-bottom: 50px;
                }
                h1 {
                    color: #333;
                }
                #score-container {
                    position: relative;
                    width: 800px;
                    height: 300px;
                    margin: 20px auto;
                    border: 1px solid #ccc;
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
                    background-color: #fff;
                }
                #score {
                    display: block;
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }
                #status-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: rgba(255, 255, 255, 0.8);
                    color: #FF0000;
                    font-size: 3em;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    z-index: 1000;
                    transition: opacity 0.3s ease-in-out;
                    opacity: 0;
                    pointer-events: none;
                }
                #status-overlay.visible {
                    opacity: 1;
                }

                /* Material segment duration section */
                .material-section {
                    margin-top: 40px;
                    width: 800px;
                    text-align: left;
                }
                .material-section h2 {
                    color: #333;
                    font-size: 1.5em;
                    margin-bottom: 15px;
                    text-align: center;
                }
                .columns-container {
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: wrap;
                    gap: 20px;
                    padding: 0 20px;
                }
                .column {
                    flex: 1;
                    min-width: 120px;
                    max-width: 150px;
                    text-align: center;
                    background-color: #fff;
                    padding: 15px 10px;
                    border-radius: 8px;
                    box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
                }
                .column h3 {
                    font-size: 1.1em;
                    color: #555;
                    margin-top: 0;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 8px;
                }
                /* Added IDs for each duration paragraph for dynamic updates */
                .column p {
                    font-size: 1.2em;
                    font-weight: bold;
                    color: #007bff;
                    margin: 0;
                }
            </style>
        </head>
        <body>
            <h1>Dynamic Music Display</h1>

            <div id="score-container">
                <img id="score" src="combined.svg" alt="Music Score"/>
                <div id="status-overlay"></div>
            </div>

            <div class="material-section">
                <h2>Material segment duration:</h2>
                <div class="columns-container">
                    <div class="column">
                        <h3>1. runs</h3>
                        <p id="duration-0">3s</p>
                    </div>
                    <div class="column">
                        <h3>2. Cluster chords</h3>
                        <p id="duration-1">5s</p>
                    </div>
                    <div class="column">
                        <h3>3. High very high squeaks</h3>
                        <p id="duration-2">8s</p>
                    </div>
                    <div class="column">
                        <h3>4. Random runs</h3>
                        <p id="duration-3">5s</p>
                    </div>
                    <div class="column">
                        <h3>5. Ostinato chords</h3>
                        <p id="duration-4">3s</p>
                    </div>
                    <div class="column">
                        <h3>6. Low rumbles</h3>
                        <p id="duration-5">2s</p>
                    </div>
                </div>
            </div>

            <script>
                const scoreImg = document.getElementById('score');
                const statusOverlay = document.getElementById('status-overlay');
                const durationParagraphs = [];
                for(let i = 0; i < 6; i++) {
                    durationParagraphs.push(document.getElementById('duration-' + i));
                }


                async function updateDisplay() {
                    try {
                        // Fetch status
                        const statusResponse = await fetch('/status');
                        const statusData = await statusResponse.json();
                        const serverStatus = statusData.status;

                        // Update status overlay
                        if (serverStatus) {
                            statusOverlay.textContent = serverStatus;
                            statusOverlay.classList.add('visible');
                            if (serverStatus === 'Recording bells...') {
                                statusOverlay.style.color = '#008000';
                            } else if (serverStatus === 'Analysing bells...') {
                                statusOverlay.style.color = '#0000FF';
                            } else {
                                statusOverlay.style.color = '#FF0000';
                            }
                        } else {
                            statusOverlay.classList.remove('visible');
                        }

                        // Fetch durations
                        const durationsResponse = await fetch('/durations');
                        const durationsData = await durationsResponse.json();
                        const newDurations = durationsData.durations;

                        // Update duration paragraphs
                        if (newDurations && newDurations.length === 6) {
                            newDurations.forEach((duration, index) => {
                                if (durationParagraphs[index]) {
                                    durationParagraphs[index].textContent = duration + 's';
                                }
                            });
                        }

                        // Refresh SVG
                        scoreImg.src = 'combined.svg?t=' + Date.now();

                    } catch (error) {
                        console.error('Error fetching status or durations:', error);
                        statusOverlay.textContent = 'Client: Connection Error';
                        statusOverlay.classList.add('visible');
                        statusOverlay.style.color = '#FFA500';
                    }
                }

                setInterval(updateDisplay, 500);
                updateDisplay(); // Initial call
            </script>
        </body>
        </html>
    `);
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    const initialCombinedSvgPath = path.join(__dirname, 'public', 'combined.svg');
    if (!fs.existsSync(initialCombinedSvgPath)) {
        console.warn("public/combined.svg not found on startup. Creating a blank initial SVG.");
        const blankSvg = `<svg width="800" height="300" viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="800" height="300" fill="#fff"/></svg>`;
        fs.writeFileSync(initialCombinedSvgPath, blankSvg);
    }
    // Start both timers when the server starts
    startDurationUpdateTimer(); // This will also generate initial durations
    startProcessingTimer();
});