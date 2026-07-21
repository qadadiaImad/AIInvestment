import "./index.css";
import { Composition } from "remotion";
import { WulfReel } from "./WulfReel";
import { EtnReel } from "./EtnReel";
import { GevReel } from "./GevReel";

const FPS = 30;
const W = 1080;
const H = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="WulfReel" component={WulfReel} durationInFrames={640} fps={FPS} width={W} height={H} />
      <Composition id="EtnReel" component={EtnReel} durationInFrames={580} fps={FPS} width={W} height={H} />
      <Composition id="GevReel" component={GevReel} durationInFrames={545} fps={FPS} width={W} height={H} />
    </>
  );
};
