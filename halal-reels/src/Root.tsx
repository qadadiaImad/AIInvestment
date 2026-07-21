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
      <Composition id="WulfReel" component={WulfReel} durationInFrames={1020} fps={FPS} width={W} height={H} />
      <Composition id="EtnReel" component={EtnReel} durationInFrames={1140} fps={FPS} width={W} height={H} />
      <Composition id="GevReel" component={GevReel} durationInFrames={900} fps={FPS} width={W} height={H} />
    </>
  );
};
