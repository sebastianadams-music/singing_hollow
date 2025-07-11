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
    \override BarLine.transparent = ##t % No barlines on score level
    \override Score.SpacingSpanner.uniform-horizontal-spacing = ##f % Disable uniform spacing
  }
  \context {
    \Staff
    \remove "Time_signature_engraver" % Remove time signature from staff
    \remove "Clef_engraver" % Remove clef from staff
    \remove "Key_engraver" % Remove key signature from staff

    \override Staff.Stem.transparent = ##t % No stems on notes
    \override Staff.Beam.transparent = ##t % No beams
    \override Staff.Flag.transparent = ##t % No flags
    \override Staff.Rest.transparent = ##t % Make rests transparent (s-rests are already invisible)
    \override Staff.Clef.transparent = ##t % Make clef transparent
    \override Staff.KeySignature.transparent = ##t % Make key signature transparent
    \override Staff.TimeSignature.transparent = ##t % Make time signature transparent
    \override Staff.BarLine.transparent = ##t % No barlines on staff level
  }
  \context {
    \GrandStaff % Target the GrandStaff context
    \override BarLine.allow-span-bar = ##f % This is the key: prevents span bars
    \override SpanBar.transparent = ##t % Also explicitly make it transparent, though allow-span-bar should take care of it
  }
}


\score {
  \new GrandStaff = "grand staff" <<
    \new Staff = "trebleStaff" {
      \clef treble % Treble clef (still needed for vertical positioning, but transparent)
      \key c \major % Key signature (still needed for accidental calculation, but transparent)
      \time 4/4 % Time signature (still needed for rhythmic parsing, but transparent)
      \relative c' { % C4 is 'c'
        cis1
      }
    }
    \new Staff = "bassStaff" {
      \clef bass % Bass clef (still needed for vertical positioning, but transparent)
      \key c \major % Key signature (still needed for accidental calculation, but transparent)
      \time 4/4 % Time signature (still needed for rhythmic parsing, but transparent)
      \relative c { % C3 is 'c'
        s1
      }
    }
  >>
}