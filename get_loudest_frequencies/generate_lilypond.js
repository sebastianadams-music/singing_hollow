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

// --- Note Constraining Logic (REMOVED) ---
// The `constrainToOctave` function is no longer used, but kept for reference if needed later.
// You can delete it entirely if you're sure you won't use it.
function constrainToOctave(noteString, targetOctaveStartNote = "C4") {
    const originalMidi = noteToMidi(noteString);
    if (originalMidi === null) {
        return noteString;
    }

    const targetOctaveStartMidi = noteToMidi(targetOctaveStartNote);
    if (targetOctaveStartMidi === null) {
        console.error(`Invalid targetOctaveStartNote: ${targetOctaveStartNote}. Using default C4.`);
        targetOctaveStartMidi = noteToMidi("C4");
    }

    const offsetFromTargetC = originalMidi - targetOctaveStartMidi;
    const constrainedMidi = ((offsetFromTargetC % 12) + 0) % 12 + targetOctaveStartMidi;

    return midiToNote(constrainedMidi);
}


// --- LilyPond Conversion (Receives already processed notes) ---

// This function now generates ABSOLUTE LilyPond notes (e.g., c'' for C5, c for C3, c, for C2)
function convertToLilypond(noteString, durationType = '1') { // Removed relativeRefNote parameter
    const noteMap = { C: 'c', D: 'd', E: 'e', F: 'f', G: 'g', A: 'a', B: 'b' };
    const accidentalMap = {
        '♯': 'is', '#': 'is',
        '♭': 'es', 'b': 'es',
        '': ''
    };

    const match = noteString.match(/^([A-Ga-g])([#♯b♭]?)(-?\d+)$/);
    if (!match) {
        console.warn(`Skipping invalid note format in convertToLilypond: ${noteString}`);
        return null;
    }

    const [, letter, accidental, octaveStr] = match;
    const pitch = noteMap[letter.toUpperCase()] + (accidentalMap[accidental] || '');
    const octave = parseInt(octaveStr, 10);

    // LilyPond's absolute 'c' (no apostrophes/commas) represents C3 (MIDI 48).
    // We calculate octave modifiers relative to this C3.
    const lilypondAbsoluteReferenceOctave = 3;

    let lilypondAbsoluteModifier = '';
    if (octave > lilypondAbsoluteReferenceOctave) {
        lilypondAbsoluteModifier = "'".repeat(octave - lilypondAbsoluteReferenceOctave);
    } else if (octave < lilypondAbsoluteReferenceOctave) {
        lilypondAbsoluteModifier = ','.repeat(lilypondAbsoluteReferenceOctave - octave);
    }

    return `${pitch}${lilypondAbsoluteModifier}${durationType}`;
}

// --- LilyPond Content Generation ---

function generateLilypondContent(trebleContent, bassContent) {
  const finalTreble = trebleContent.length > 0 ? trebleContent.join(' ') : "s1";
  const finalBass = bassContent.length > 0 ? bassContent.join(' ') : "s1";

  return `
\\version "2.24.2"
\\paper {
  #(define output-format 'svg)
  indent = 0
  left-margin = 1.5 \\cm
  right-margin = 1.5 \\cm
  % Adjusted for grand staff layout
  system-system-spacing = #'((basic-distance . 20) (minimum-distance . 18) (padding . 1) (stretchability . 50))
  bottom-margin = 1.5 \\cm
}

\\layout {
  % Proportional Notation settings
  \\context {
    \\Score
    \\override BarLine.transparent = ##t
    \\override Score.SpacingSpanner.uniform-horizontal-spacing = ##f
  }
  \\context {
    \\Staff
    \\remove "Time_signature_engraver"
    \\remove "Key_engraver"
    % You might want to remove this too if rests appear with stems/flags
    % \\override Staff.Rest.transparent = ##t

    \\override Staff.Stem.transparent = ##t
    \\override Staff.Beam.transparent = ##t
    \\override Staff.Flag.transparent = ##t
    \\override Staff.KeySignature.transparent = ##t
    \\override Staff.TimeSignature.transparent = ##t
    \\override Staff.BarLine.transparent = ##t
  }
  \\context {
    \\GrandStaff
    \\override BarLine.allow-span-bar = ##f
    \\override SpanBar.transparent = ##t
  }
}

\\score {
    \\new Staff = "trebleStaff" {
      \\clef treble
      \\key c \\major
      \\time 4/4
      % REMOVE \\relative c' {
        ${finalTreble}
      % REMOVE }
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
  // Adjusted Y-translation for grand staff. You might need to fine-tune this.
  const translateY = 40;

  const updated = template.replace(
    /<g id="music"[^>]*>[\s\S]*?<\/g>/,
    `<g id="music" transform="translate(${translateX.toFixed(2)}, ${translateY}) scale(${scale.toFixed(3)})">\n${musicSVG}\n</g>`
  );
  fs.writeFileSync(FINAL_SVG, updated);
}

// --- Main Execution Function ---

function generateAndInjectAllNotes() {
  const rawNotes = JSON.parse(fs.readFileSync('notes.json', 'utf8'));

  // Filter out invalid notes first
  const validRawNotes = rawNotes.filter(noteString => noteToMidi(noteString) !== null);

  const alignedTrebleContent = [];
  const alignedBassContent = [];
  const C4_MIDI = noteToMidi("C4"); // Middle C is still the split point
  const defaultDuration = '1'; // All notes are treated as semibreves ('1')

  validRawNotes.forEach(noteString => {
  const midi = noteToMidi(noteString);

  if (midi === null) {
      console.warn(`Skipping note ${noteString} as its MIDI conversion failed within forEach.`);
      return;
  }

  // Call the updated convertToLilypond, no relativeRefNote needed
  const lilypondNote = convertToLilypond(noteString, defaultDuration);

  if (midi >= C4_MIDI) { // C4 and higher go to treble
    alignedTrebleContent.push(lilypondNote);
    alignedBassContent.push(`s${defaultDuration}`);
  } else { // Below C4 go to bass
    alignedBassContent.push(lilypondNote);
    alignedTrebleContent.push(`s${defaultDuration}`);
  }
});

  
  if (alignedTrebleContent.length === 0 && alignedBassContent.length === 0) {
    console.warn("No valid notes found after processing and splitting. Nothing to display.");
    return;
  }

  // Rest of your LilyPond generation and SVG injection logic
  const content = generateLilypondContent(alignedTrebleContent, alignedBassContent);
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
      console.log(`✅ Successfully generated and updated combined.svg with aligned notes/rests.`);
      console.log(`Check ${FINAL_SVG}`);
    }
  });
}

// Start the process
generateAndInjectAllNotes();