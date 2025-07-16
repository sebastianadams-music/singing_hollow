\version "2.24.2"
\paper {
  #(define output-format 'svg)
  indent = 0
  left-margin = 1.5 \cm
  right-margin = 1.5 \cm
  % Adjusted for grand staff layout
  system-system-spacing = #'((basic-distance . 20) (minimum-distance . 18) (padding . 1) (stretchability . 50))
  bottom-margin = 1.5 \cm
}

\layout {
  % Proportional Notation settings
  \context {
    \Score
    \override BarLine.transparent = ##t
    \override Score.SpacingSpanner.uniform-horizontal-spacing = ##f
  }
  \context {
    \Staff
    \remove "Time_signature_engraver"
    \remove "Key_engraver"
    % You might want to remove this too if rests appear with stems/flags
    % \override Staff.Rest.transparent = ##t

    \override Staff.Stem.transparent = ##t
    \override Staff.Beam.transparent = ##t
    \override Staff.Flag.transparent = ##t
    \override Staff.KeySignature.transparent = ##t
    \override Staff.TimeSignature.transparent = ##t
    \override Staff.BarLine.transparent = ##t
  }
  \context {
    \GrandStaff
    \override BarLine.allow-span-bar = ##f
    \override SpanBar.transparent = ##t
  }
}

\score {
    \new Staff = "trebleStaff" {
      \clef treble
      \key c \major
      \time 4/4
      % REMOVE \relative c' {
        gis'1 cis'1 d'1
      % REMOVE }
    }

}