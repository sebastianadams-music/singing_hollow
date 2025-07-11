1. analyse file using python 
    (.venv) sebastianadams@Mac-mini get_loudest_frequencies % python analyze_audio.py /Volumes/seb/Downloads/390120__xploman__distant-church-bells.wav -o notes.json
2. this is exported to JSON (using -o notes.json flag)
3. Node file random-lilypond.js reads file and creates SVG (node random-lilypond.js)
3. Node server reads SVG: npm start
4. SVG displayed in browser.




STEPS:
1. webpage has an SVG reloading often, and a timer running material instructions
2. at intervals, webpage requests the organist to stop playing
3. server then activates the microphone
4. microphone content is analysed and a new SVG is created from the resulting analysis.