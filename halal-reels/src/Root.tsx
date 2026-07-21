import "./index.css";
import { Composition } from "remotion";
import { WulfReel } from "./WulfReel";
import { EtnReel } from "./EtnReel";
import { GevReel } from "./GevReel";
import { IntroVideo } from "./IntroScenes";
import { INTRO_BEATS } from "./IntroScenes";

const FPS = 30;
const W = 1080;
const H = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="WulfReel" component={WulfReel} durationInFrames={1020} fps={FPS} width={W} height={H} />
      <Composition id="EtnReel" component={EtnReel} durationInFrames={1140} fps={FPS} width={W} height={H} />
      <Composition id="IntroReel" component={IntroVideo} durationInFrames={INTRO_BEATS.total} fps={FPS} width={W} height={H} defaultProps={{ wide: false }} />
      <Composition id="IntroWide" component={IntroVideo} durationInFrames={INTRO_BEATS.total} fps={FPS} width={1920} height={1080} defaultProps={{ wide: true }} />
      <Composition id="GevReel" component={GevReel} durationInFrames={900} fps={FPS} width={W} height={H} />
    </>
  );
};
