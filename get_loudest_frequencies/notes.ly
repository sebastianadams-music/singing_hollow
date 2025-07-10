\version "2.24.2"
\paper {
  #(define output-format 'svg)
  indent = 0
  left-margin = 1.5 \cm
  right-margin = 1.5 \cm
  system-system-spacing = #'((basic-distance . 10) (minimum-distance . 8) (padding . 1) (stretchability . 50))
  bottom-margin = 1.0 \cm
}
\score {
  \new Staff {
    \clef treble
    \key c \major
    \time 4/4
    \relative c' {
      f4 ais4 d4 c4 d4 f4 g4 a4 b4 cis4 d4 fis4
    }
  }
}