const express = require('express');
const path = require('path');
const { exec, spawn } = require('child_process');
const fs = require('fs');

const args = process.argv.slice(2); // Get arguments after 'node server.js'
const isTestMode = args.includes('test'); // run "npm start test" to use test mode!

const app = express();
const PORT = 3000;
const AUDIO_FILE_PATH = path.join(__dirname, 'recorded_audio.wav');
const NOTES_JSON_PATH = path.join(__dirname, 'notes.json');


if (isTestMode) {
    console.log("test mode")
    ORGAN_DATA_PATH = path.join(__dirname, 'dummyorganstructure.json'); // Using your dummy data path for testing
}
else {
    const ORGAN_DATA_PATH = path.join(__dirname, 'singinghollow_organ.json');

}


// --- Absolute Paths for Executables (IMPROVED ROBUSTNESS) ---
const FFMPEG_PATH = "ffmpeg";
const PYTHON_PATH = "python"
const LILYPOND_PATH = "lilypond";

// --- FFmpeg Device Index (CRITICAL: ENSURE THIS IS CORRECT) ---
const FFMPEG_DEVICE_INDEX = ":1";

// Ensure 'public' directory exists
const publicDir = path.join(__dirname, 'public');
if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir);
}

// Serve static files from the 'public' directory
app.use(express.static(publicDir));

let currentStatusMessage = '';

let organData = [];
let currentSegmentIndex = 0;
let currentMaterialIndex = 0;
let currentRecordingDuration = 0;

// Materials that are 'meta' and should not have their duration used for the main cycle timer
const META_MATERIALS = ["RECORDING", "analysis"];

function loadOrganData() {
    try {
        const data = fs.readFileSync(ORGAN_DATA_PATH, 'utf8');
        organData = JSON.parse(data);
        console.log("Organ data loaded successfully.");
        const recordingMaterial = organData.find(m => m.name === "RECORDING");
        if (recordingMaterial && recordingMaterial.durations.length > 0) {
            currentRecordingDuration = recordingMaterial.durations[0];
        } else {
            console.warn("RECORDING material not found or empty, defaulting recording duration to 5s.");
            currentRecordingDuration = 5;
        }

    } catch (error) {
        console.error("Failed to load organ data:", error);
        organData = [];
    }
}

function getCurrentSegmentDurations() {
    if (organData.length === 0) {
        return [];
    }

    const segmentDurations = organData.map(material => {
        if (material.durations && material.durations.length > currentSegmentIndex) {
            return {
                name: material.name,
                duration: material.durations[currentSegmentIndex]
            };
        }
        return { name: material.name, duration: null };
    });

    const recordingEntry = segmentDurations.find(s => s.name === "RECORDING");
    if (recordingEntry && recordingEntry.duration !== null) {
        currentRecordingDuration = recordingEntry.duration;
        // Commenting this out to reduce console spam, as it updates every frontend poll
        // console.log(`Updated current recording duration to: ${currentRecordingDuration}s`);
    }

    return segmentDurations;
}

function advancePerformanceState() {
    if (organData.length === 0) {
        console.warn("Cannot advance performance state, organ data not loaded.");
        return;
    }

    currentMaterialIndex++;

    const maxSegmentLength = Math.max(...organData.map(material => material.durations.length));

    if (currentMaterialIndex >= organData.length) {
        currentMaterialIndex = 0;
        currentSegmentIndex++;

        if (currentSegmentIndex >= maxSegmentLength) {
            console.log("End of performance data reached. Looping back to the beginning.");
            currentSegmentIndex = 0;
        }
    }
    console.log(`Advanced to Segment: ${currentSegmentIndex}, Material: ${organData[currentMaterialIndex]?.name || 'N/A'}`);
}


async function processAudioAndGenerateSVG() {
    console.log('--- Starting Audio Processing Cycle (Recording & Analysis) ---');
    let cycleSuccess = true;

    try {
        const scriptDir = __dirname;

        currentStatusMessage = 'Stop Playing!';
        console.log(`Status: ${currentStatusMessage}`);

        currentStatusMessage = `Recording bells for ${currentRecordingDuration}s...`;
        console.log(`Status: ${currentStatusMessage}`);
        console.log(`Recording audio for ${currentRecordingDuration} seconds using FFmpeg...`);

        const recordArgs = [
            '-f', 'avfoundation',
            '-i', FFMPEG_DEVICE_INDEX,
            '-t', currentRecordingDuration.toString(),
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
                resolve();
            });
        });

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
                resolve();
            });
        });

        currentStatusMessage = '';
        console.log('--- Audio Processing Cycle Complete ---');

    } catch (err) {
        cycleSuccess = false;
        console.error('An error occurred during the processing cycle:', err);
        currentStatusMessage = `Cycle Error: ${err.message.substring(0, 70)}...`;
    } finally {
        // No call to startProcessingTimer() or advancePerformanceState() here.
        // These are now exclusively handled by the main startProcessingTimer()
        // to manage the sequence and ensure immediate progression after recording.
    }
}

let processingTimer;

function startProcessingTimer() {
    if (processingTimer) {
        clearTimeout(processingTimer);
    }

    let nextInterval = 5; // Default if no valid material found
    let currentMaterial = null;

    if (organData.length > 0 && currentMaterialIndex < organData.length) {
        currentMaterial = organData[currentMaterialIndex];
        if (currentMaterial && currentMaterial.durations && currentMaterial.durations.length > currentSegmentIndex) {
            nextInterval = currentMaterial.durations[currentSegmentIndex];
        } else {
            console.warn(`Could not find duration for material ${currentMaterialIndex} at segment ${currentSegmentIndex}. Defaulting to 5s.`);
        }
    } else {
        console.warn("Organ data not loaded or empty, defaulting next interval to 5s.");
    }

    processingTimer = setTimeout(async () => {
        // Only run processAudioAndGenerateSVG if it's the last *playable* material (Low Rumbles)
        if (currentMaterial && currentMaterial.name === "Low Rumbles") {
            console.log("Current material is 'Low Rumbles'. Initiating audio processing.");
            await processAudioAndGenerateSVG();
        } else if (currentMaterial && META_MATERIALS.includes(currentMaterial.name)) {
            // If it's 'RECORDING' or 'analysis', these phases are handled *within* processAudioAndGenerateSVG
            // when it runs after Low Rumbles. So, if we hit these in the *normal* material
            // sequence, it means processAudioAndGenerateSVG didn't run this cycle,
            // and we should just advance past them immediately.
            console.log(`Current material is '${currentMaterial.name}'. This is a meta-material, advancing immediately.`);
            nextInterval = 0.1; // Make it a very short interval to skip quickly
        } else {
            console.log(`Current material is '${currentMaterial?.name || 'N/A'}'. Skipping audio processing for this unit.`);
        }

        // Always advance the performance state after the timer completes, regardless of sampling.
        // This ensures progression through materials, including skipping meta ones.
        advancePerformanceState();

        // Schedule the next timer immediately after advancing state
        startProcessingTimer();

    }, nextInterval * 1000);
    console.log(`Next material unit scheduled in ${nextInterval} seconds (for material ${currentMaterial?.name || 'N/A'} in segment ${currentSegmentIndex}).`);
}

// --- API endpoints ---
app.get('/status', (req, res) => {
    res.json({ status: currentStatusMessage });
});

app.get('/performance_state', (req, res) => {
    const segmentDurations = getCurrentSegmentDurations();
    res.json({
        segmentIndex: currentSegmentIndex,
        materialIndex: currentMaterialIndex,
        materials: segmentDurations
    });
});

// --- Express Route for the main page ---
app.get('/', (req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    const initialCombinedSvgPath = path.join(publicDir, 'combined.svg');
    if (!fs.existsSync(initialCombinedSvgPath)) {
        console.warn("public/combined.svg not found on startup. Creating a blank initial SVG.");
        const blankSvg = `<svg width="800" height="300" viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="800" height="300" fill="#fff"/></svg>`;
        fs.writeFileSync(initialCombinedSvgPath, blankSvg);
    }
    loadOrganData();
    startProcessingTimer(); // Start the first timer
});