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
import { QuarterlyReportEp2, QR_EP2_BEATS } from "./QuarterlyReportEp2";
import { QuarterlyReportKorea, QR_KOREA_BEATS } from "./QuarterlyReportKorea";
import { QuarterlyReportCongress, QR_CONGRESS_BEATS } from "./QuarterlyReportCongress";
import { QuarterlyReportLoop, QR_LOOP_BEATS } from "./QuarterlyReportLoop";
import { QuarterlyReportTier, QR_TIER_BEATS } from "./QuarterlyReportTier";
import { QuarterlyReportCascade, QR_CASCADE_BEATS } from "./QuarterlyReportCascade";
import { QuarterlyReportDebt, QR_DEBT_BEATS } from "./QuarterlyReportDebt";
import { QuarterlyReportDebtCover, QR_DEBT_COVER_BEATS } from "./QuarterlyReportDebtCover";
import { HostPreview } from "./toon/host";
import { PoseSheet } from "./toon/PoseSheet";
import { CastSheet } from "./toon/CastSheet";

const FPS = 30;
const W = 1080;
const H = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="QuarterlyReport" component={QuarterlyReport} durationInFrames={QR_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportEp2" component={QuarterlyReportEp2} durationInFrames={QR_EP2_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportKorea" component={QuarterlyReportKorea} durationInFrames={QR_KOREA_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportCongress" component={QuarterlyReportCongress} durationInFrames={QR_CONGRESS_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportLoop" component={QuarterlyReportLoop} durationInFrames={QR_LOOP_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportTier" component={QuarterlyReportTier} durationInFrames={QR_TIER_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportCascade" component={QuarterlyReportCascade} durationInFrames={QR_CASCADE_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportDebt" component={QuarterlyReportDebt} durationInFrames={QR_DEBT_BEATS.total} fps={FPS} width={W} height={H} />
      <Composition id="QuarterlyReportDebtCover" component={QuarterlyReportDebtCover} durationInFrames={QR_DEBT_COVER_BEATS.total} fps={FPS} width={W} height={H} />
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
      <Composition id="HostPreview" component={HostPreview} durationInFrames={1} fps={FPS} width={W} height={H} />
      <Composition id="ToonCastSheet" component={CastSheet} durationInFrames={1} fps={FPS} width={1200} height={800} />
    </>
  );
};
