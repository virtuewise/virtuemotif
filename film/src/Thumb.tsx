import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { PALETTE as P } from "./theme";
import { Scenery, Look } from "./HorizonFilm";
import { FONT_DISPLAY, FONT_MONO, FONT_SERIF } from "./theme";
import { useFilmFonts } from "./Type";

const THUMB_LOOK: Look = {
  variant: "giant",
  sunX: 960,
  sunY: 560,
  sunR: 470,
  warmth: 1,
  night: 0,
  camStart: 1.04,
  camEnd: 1.04,
  treeDensity: 0,
  figures: [
    { x: 300, y: 700, pose: "raise", s: 0.72 },
    { x: 620, y: 704, pose: "stand", s: 0.7 },
    { x: 1560, y: 702, pose: "mbira", s: 0.74, flip: true },
  ],
};

export const Thumb: React.FC<{ title: string; subtitle: string; kicker?: string; artist?: string }> = ({
  title,
  subtitle,
  kicker = "A LYRICAL FILM",
  artist = "virtuemotif",
}) => {
  useFilmFonts();
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: P.night }}>
      <Scenery t={frame / 30} st={frame / 30} look={THUMB_LOOK} />
      <AbsoluteFill
        style={{
          background: "linear-gradient(180deg, rgba(6,10,18,0.55) 0%, rgba(6,10,18,0.05) 38%, rgba(6,10,18,0.72) 100%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-start", paddingLeft: 96 }}>
        <div style={{ maxWidth: 1500 }}>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 20,
              letterSpacing: "0.5em",
              color: P.amber,
              marginBottom: 26,
            }}
          >
            {kicker}
          </div>
          <div
            style={{
              fontFamily: FONT_DISPLAY,
              fontSize: 178,
              lineHeight: 0.9,
              color: P.bone,
              textTransform: "uppercase",
              textShadow: "0 6px 0 #2A140F, 0 30px 70px rgba(0,0,0,0.65)",
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontFamily: FONT_SERIF,
              fontStyle: "italic",
              fontSize: 96,
              color: P.ochre,
              marginTop: 10,
              textShadow: "0 8px 30px rgba(0,0,0,0.7)",
            }}
          >
            {subtitle}
          </div>
          <div
            style={{
              marginTop: 34,
              fontFamily: FONT_MONO,
              fontSize: 22,
              letterSpacing: "0.36em",
              color: P.cream,
              opacity: 0.8,
            }}
          >
            {artist?.toUpperCase()}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
