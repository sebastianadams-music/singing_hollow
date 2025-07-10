const fs = require('fs');
const { exec } = require('child_process');
const path = require('path');

const OUTPUT_LY = 'notes.ly';
const OUTPUT_SVG = 'notes.svg';
const TEMPLATE_FILE = 'template.svg';
const FINAL_SVG = 'public/combined.svg';
const TARGET_WIDTH = 800; // Desired width in pixels for the music

// --- Helper Functions for Note/MIDI Conversion ---

// Converts a note name (e.g., "C4", "F#3") to a MIDI number.
// MIDI 0 = C-1, MIDI 60 = C4 (Middle C)
function noteToMidi(noteName) {
    const pitchClasses = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    };
    const accidentalOffsets = {
        '#': 1, '♯': 1, 'b': -1, '♭': -1, '': 0
    };

    const match = noteName.match(/^([A-Ga-g])([#♯b♭]?)(-?\d+)$/);
    if (!match) {
        console.warn(`Invalid note format for MIDI conversion: ${noteName}`);
        return null;
    }

    const [, letter, accidental, octaveStr] = match;
    const baseMidi = pitchClasses[letter.toUpperCase()];
    const accidentalMidi = accidentalOffsets[accidental || ''];
    const octave = parseInt(octaveStr, 10);

    return (octave + 1) * 12 + baseMidi + accidentalMidi;
}

// Converts a MIDI number back to a note name (e.g., 60 -> "C4").
// This function outputs sharps by default for accidentals.
function midiToNote(midiNumber) {
    if (midiNumber === null || midiNumber < 0 || midiNumber > 127) {
        console.warn(`Invalid MIDI number for conversion: ${midiNumber}`);
        return null;
    }

    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(midiNumber / 12) - 1; // MIDI 0 is C-1, so octave - 1
    const pitchClass = midiNumber % 12;

    return `${noteNames[pitchClass]}${octave}`;
}

// --- Note Constraining Logic ---

// Constrains a note to a specific octave range (e.g., C4 to B4).
// It 'wraps' notes into the target octave.
function constrainToOctave(noteString, targetOctaveStartNote = "C4") {
    const originalMidi = noteToMidi(noteString);
    if (originalMidi === null) {
        return noteString; // Cannot constrain if original is invalid
    }

    const targetOctaveStartMidi = noteToMidi(targetOctaveStartNote);
    if (targetOctaveStartMidi === null) {
        console.error(`Invalid targetOctaveStartNote: ${targetOctaveStartNote}. Using default C4.`);
        targetOctaveStartMidi = noteToMidi("C4");
    }

    // Calculate the difference in semitones from the target octave's C
    const offsetFromTargetC = originalMidi - targetOctaveStartMidi;

    // Use modulo 12 to wrap the pitch class, then add it back to the target C
    // The `+ 12) % 12` handles potential negative results from modulo for negative offsets
    const constrainedMidi = ((offsetFromTargetC % 12) + 12) % 12 + targetOctaveStartMidi;

    return midiToNote(constrainedMidi);
}

// --- LilyPond Conversion (Receives already constrained notes) ---

function convertToLilypond(noteString, duration = '4') {
    const noteMap = {
        C: 'c', D: 'd', E: 'e', F: 'f', G: 'g', A: 'a', B: 'b'
    };
    const accidentalMap = {
        '♯': 'is', '#': 'is',
        '♭': 'es', 'b': 'es',
        '': ''
    };

    const match = noteString.match(/^([A-Ga-g])([#♯b♭]?)(-?\d+)$/);
    if (!match) {
        // This should ideally not happen if notes are first passed through constrainToOctave
        // and midiToNote, but as a safeguard:
        console.warn(`Skipping invalid note format in convertToLilypond: ${noteString}`);
        return null;
    }

    const [, letter, accidental, octaveStr] = match;
    const pitch = noteMap[letter.toUpperCase()] + (accidentalMap[accidental] || '');
    const octave = parseInt(octaveStr, 10);

    // LilyPond \relative c' mode: 'c' corresponds to C4 (MIDI 60).
    // Calculate the correct number of ' or , modifiers relative to C4.
    let lilyOctaveModifier = '';
    const referenceOctaveForLilypondCPrime = 4; // C4 is the 'c' in \relative c'

    if (octave > referenceOctaveForLilypondCPrime) {
        lilyOctaveModifier = "'".repeat(octave - referenceOctaveForLilypondCPrime);
    } else if (octave < referenceOctaveForLilypondCPrime) {
        lilyOctaveModifier = ','.repeat(referenceOctaveForLilypondCPrime - octave);
    }

    return `${pitch}${lilyOctaveModifier}${duration}`;
}

// --- LilyPond Content Generation ---

function generateLilypondContent(notes) {
  const notesArray = Array.isArray(notes) ? notes : [notes];

  return `
\\version "2.24.2"
\\paper {
  #(define output-format 'svg)
  indent = 0
  left-margin = 1.5 \\cm
  right-margin = 1.5 \\cm
  system-system-spacing = #'((basic-distance . 10) (minimum-distance . 8) (padding . 1) (stretchability . 50))
  bottom-margin = 1.0 \\cm
}
\\score {
  \\new Staff {
    \\clef treble
    \\key c \\major
    \\time 4/4
    \\relative c' {
      ${notesArray.join(' ')}
    }
  }
}
`.trim();
}

// --- SVG Extraction and Injection (Unchanged) ---

function extractSVGContent(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const match = raw.match(/<svg[^>]*>([\s\S]*?)<\/svg>/);
  return match ? match[1].trim() : '';
}

function getViewBox(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const match = raw.match(/viewBox="([^"]+)"/);
  if (!match) return null;

  const [minX, minY, width, height] = match[1].split(/\s+/).map(Number);
  return { minX, minY, width, height };
}

function injectIntoTemplate(musicSVG, scale, translateX) {
  const template = fs.readFileSync(TEMPLATE_FILE, 'utf8');
  const translateY = 20;

  const updated = template.replace(
    /<g id="music"[^>]*>[\s\S]*?<\/g>/,
    `<g id="music" transform="translate(${translateX.toFixed(2)}, ${translateY}) scale(${scale.toFixed(3)})">\n${musicSVG}\n</g>`
  );
  fs.writeFileSync(FINAL_SVG, updated);
}

// --- Main Execution Function ---

function generateAndInjectAllNotes() {
  const rawNotes = JSON.parse(fs.readFileSync('notes.json', 'utf8'));

  // Define your target octave here. For C4-B4, use "C4". For C3-B3, use "C3", etc.
  const targetConstrainedOctaveStart = "C4"; // Example: Constrain all notes to the C4-B4 octave

  // First, constrain all notes to the desired octave
  const constrainedNotes = rawNotes.map(noteString =>
    constrainToOctave(noteString, targetConstrainedOctaveStart)
  ).filter(Boolean); // Filter out any notes that couldn't be constrained

  // Then, convert the constrained notes to LilyPond format
  const allLilypondNotes = constrainedNotes.map(n => convertToLilypond(n, '4')).filter(Boolean);

  if (allLilypondNotes.length === 0) {
    console.warn("No valid notes found in notes.json after constraining and conversion. Nothing to display.");
    return;
  }

  const content = generateLilypondContent(allLilypondNotes);
  fs.writeFileSync(OUTPUT_LY, content);

  exec(`lilypond -dbackend=svg -o ${OUTPUT_SVG.replace('.svg', '')} ${OUTPUT_LY}`, (err, stdout, stderr) => {
    if (err) {
      console.error('LilyPond error:', err);
      console.error("LilyPond stdout (if any):", stdout);
      console.error("LilyPond stderr (if any):", stderr);
    } else {
      const musicSVG = extractSVGContent(OUTPUT_SVG);
      const viewBox = getViewBox(OUTPUT_SVG);

      if (!viewBox) {
        console.error("Couldn't find viewBox in LilyPond SVG. LilyPond might have failed silently or generated no output.");
        console.error("LilyPond stdout (if any):", stdout);
        console.error("LilyPond stderr (if any):", stderr);
        return;
      }

      const scale = TARGET_WIDTH / viewBox.width;
      const svgOuterWidth = 800;
      const translateX = (svgOuterWidth - TARGET_WIDTH) / 2;

      injectIntoTemplate(musicSVG, scale, translateX);
      console.log(`✅ Successfully generated and updated combined.svg with ${allLilypondNotes.length} notes constrained to the ${targetConstrainedOctaveStart} octave.`);
      console.log(`Check ${FINAL_SVG}`);
    }
  });
}

// Start the process
generateAndInjectAllNotes();