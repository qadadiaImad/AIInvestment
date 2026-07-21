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
import wulfSlidesFixture from "./fixtures/wulf_slides.json";
import tutorialTerminalFixture from "./fixtures/tutorial_terminal.json";
import { HalalVerdictReel } from "./compositions/HalalVerdictReel";
import { SlideStoryReel } from "./compositions/SlideStoryReel";
import { TutorialReel } from "./compositions/TutorialReel";
import { reelPropsSchema } from "./props";
import { slideStoryPropsSchema } from "./slides/slideProps";
import { tutorialPropsSchema } from "./slides/tutorialProps";

const wulfSlidesProps = slideStoryPropsSchema.parse(wulfSlidesFixture);
const wulfSlidesDuration = wulfSlidesProps.beats.reduce(
  (sum, beat) => sum + beat.durationInFrames,
  0
);

const tutorialTerminalProps = tutorialPropsSchema.parse(tutorialTerminalFixture);
const tutorialTerminalDuration = tutorialTerminalProps.scenes.reduce(
  (sum, scene) => sum + scene.durationInFrames,
  0
);

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
      <Composition
        id="SlideStoryReel"
        component={SlideStoryReel}
        durationInFrames={wulfSlidesDuration}
        fps={30}
        width={1080}
        height={1920}
        schema={slideStoryPropsSchema}
        defaultProps={wulfSlidesProps}
        calculateMetadata={({ props }) => ({
          // duration follows whatever props file is rendered (--props=...),
          // not the default fixture — beats are the single source of truth.
          durationInFrames: props.beats.reduce(
            (sum, beat) => sum + beat.durationInFrames,
            0
          ),
        })}
      />
      <Composition
        id="TutorialReel"
        component={TutorialReel}
        durationInFrames={tutorialTerminalDuration}
        fps={30}
        width={1080}
        height={1920}
        schema={tutorialPropsSchema}
        defaultProps={tutorialTerminalProps}
        calculateMetadata={({ props }) => ({
          // duration follows whatever props file is rendered (--props=...),
          // not the default fixture — scenes are the single source of truth.
          durationInFrames: props.scenes.reduce(
            (sum, scene) => sum + scene.durationInFrames,
            0
          ),
        })}
      />
    </>
  );
};
