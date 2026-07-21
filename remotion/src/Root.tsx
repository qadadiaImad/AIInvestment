import "./index.css";
import { Composition, staticFile } from "remotion";
import {
  CaptionedVideo,
  calculateCaptionedVideoMetadata,
  captionedVideoSchema,
} from "./CaptionedVideo";
import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadJBM } from "@remotion/google-fonts/JetBrainsMono";
import fixture from "./fixtures/ddog.json";
import { HalalVerdictReel } from "./compositions/HalalVerdictReel";
import { reelPropsSchema } from "./props";

loadFraunces();
loadInter();
loadJBM();

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CaptionedVideo"
        component={CaptionedVideo}
        calculateMetadata={calculateCaptionedVideoMetadata}
        schema={captionedVideoSchema}
        width={1080}
        height={1920}
        defaultProps={{
          src: staticFile("sample-video.mp4"),
        }}
      />
      <Composition
        id="HalalVerdictReel"
        component={HalalVerdictReel}
        durationInFrames={720}
        fps={30}
        width={1080}
        height={1920}
        schema={reelPropsSchema}
        defaultProps={reelPropsSchema.parse(fixture)}
      />
    </>
  );
};
