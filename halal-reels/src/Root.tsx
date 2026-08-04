import "./index.css";
import { Composition } from "remotion";
import { WulfReel } from "./WulfReel";
import { EtnReel } from "./EtnReel";
import { GevReel } from "./GevReel";
import { IntroVideo } from "./IntroScenes";
import { ToolboxVideo } from "./ToolboxScenes";
import { TOOLBOX_BEATS } from "./ToolboxScenes";
import { INTRO_BEATS } from "./IntroScenes";
import { ValueQuizReel, QUIZ_BEATS } from "./ValueQuizReel";
import { CorrelationReel, CORRELATION_BEATS, CORRELATION_MINI_TOTAL } from "./CorrelationReel";
import { SemisReel, SEMIS_BEATS, SEMIS_MINI_TOTAL } from "./SemisReel";
import { QuarterlyReport, QR_BEATS } from "./QuarterlyReport";
import { PoseSheet } from "./toon/PoseSheet";
import { CastSheet } from "./toon/CastSheet";

const FPS = 30;
const W = 1080;
const H = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="QuarterlyReport" component={QuarterlyReport} durationInFrames={QR_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="WulfReel" component={WulfReel} durationInFrames={1020} fps={FPS} width={W} height={H} />
      <Composition id="EtnReel" component={EtnReel} durationInFrames={1140} fps={FPS} width={W} height={H} />
      <Composition id="IntroReel" component={IntroVideo} durationInFrames={INTRO_BEATS.total} fps={FPS} width={W} height={H} defaultProps={{ wide: false }} />
      <Composition id="IntroWide" component={IntroVideo} durationInFrames={INTRO_BEATS.total} fps={FPS} width={1920} height={1080} defaultProps={{ wide: true }} />
      <Composition id="ToolboxReel" component={ToolboxVideo} durationInFrames={TOOLBOX_BEATS.total} fps={FPS} width={W} height={H} defaultProps={{ wide: false }} />
      <Composition id="ToolboxWide" component={ToolboxVideo} durationInFrames={TOOLBOX_BEATS.total} fps={FPS} width={1920} height={1080} defaultProps={{ wide: true }} />
      <Composition id="GevReel" component={GevReel} durationInFrames={900} fps={FPS} width={W} height={H} />
      <Composition
        id="ValueQuizReel"
        component={ValueQuizReel}
        durationInFrames={QUIZ_BEATS.total}
        fps={FPS}
        width={W}
        height={H}
      />
      <Composition
        id="CorrelationReel"
        component={CorrelationReel}
        durationInFrames={CORRELATION_BEATS.total}
        fps={FPS}
        width={W}
        height={H}
      />
      <Composition
        id="CorrelationReelMini"
        component={CorrelationReel}
        durationInFrames={CORRELATION_MINI_TOTAL}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{ mini: true }}
      />
      <Composition
        id="SemisReel"
        component={SemisReel}
        durationInFrames={SEMIS_BEATS.total}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{ mini: false }}
      />
      <Composition
        id="SemisReelMini"
        component={SemisReel}
        durationInFrames={SEMIS_MINI_TOTAL}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{ mini: true }}
      />
      <Composition id="ToonPoseSheet" component={PoseSheet} durationInFrames={1} fps={FPS} width={1800} height={900} />
      <Composition id="ToonCatalogSheet" component={PoseSheet} durationInFrames={1} fps={FPS} width={1800} height={1800} defaultProps={{ fromCatalog: true }} />
      <Composition id="ToonCastSheet" component={CastSheet} durationInFrames={1} fps={FPS} width={1200} height={800} />
    </>
  );
};
