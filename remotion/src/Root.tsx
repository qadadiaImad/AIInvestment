import "./index.css";
import { Composition, Still, staticFile } from "remotion";
import {
  CaptionedVideo,
  calculateCaptionedVideoMetadata,
  captionedVideoSchema,
} from "./CaptionedVideo";
import fixture from "./fixtures/ddog.json";
import wulfSlidesFixture from "./fixtures/wulf_slides.json";
import tutorialTerminalFixture from "./fixtures/tutorial_terminal.json";
import kurzSlide2Fixture from "./fixtures/carousel_top3/slide2.json";
import { HalalVerdictReel } from "./compositions/HalalVerdictReel";
import { SlideStoryReel } from "./compositions/SlideStoryReel";
import { TutorialReel } from "./compositions/TutorialReel";
import { KurzSlide } from "./compositions/KurzSlide";
import { CharacterCard, characterCardSchema } from "./compositions/CharacterCard";
import { ChipShowcase, chipShowcaseSchema } from "./compositions/ChipShowcase";
import { ExplainerScene, explainerSceneSchema } from "./compositions/ExplainerScene";
import { FamilyRigShowcase, familyRigShowcaseSchema } from "./compositions/FamilyRigShowcase";
import { ExplainerSceneV2 } from "./compositions/ExplainerSceneV2";
import { FaceoffOverlay, faceoffOverlaySchema } from "./compositions/FaceoffOverlay";
import { InfraCountdown, infraCountdownSchema } from "./compositions/InfraCountdown";
import infraCountdownFixture from "./fixtures/infra_countdown_2026-07-22.json";
import { TradingQuiz, tradingQuizSchema } from "./compositions/TradingQuiz";
import { TradingStyles, tradingStylesSchema } from "./compositions/TradingStyles";
import { GroundingCheck, groundingCheckSchema } from "./compositions/GroundingCheck";
import tradingStylesFixture from "./fixtures/trading_styles/trading_styles.json";
import tradingQuizFixture from "./fixtures/trading_quiz_engulfing_2026-07-25.json";
import { QuizWithHost, quizWithHostSchema } from "./compositions/QuizWithHost";
import quizWithHostFixture from "./fixtures/quiz_with_host_2026-07-25.json";
import { MemeReel, memeReelSchema } from "./compositions/MemeReel";
import { TradeFailReel, tradeFailReelSchema } from "./compositions/TradeFailReel";
import { TradeFailCam, tradeFailCamSchema } from "./compositions/TradeFailCam";
import { PatternGallery, patternGallerySchema, PATTERN_GALLERY_FRAMES } from "./compositions/PatternGallery";
import { PatternSheet, patternSheetSchema, PATTERN_SHEET_FRAMES } from "./compositions/PatternSheet";
import { PatternEndCard, patternEndCardSchema } from "./compositions/PatternEndCard";
import patternGalleryFixture from "./fixtures/patterns_post/gallery.json";
import { RigCheck, rigCheckSchema } from "./compositions/RigCheck";
import memeReelFixture from "./fixtures/meme_reel/intc_failed_breakout.json";
import tradeFailFixture from "./fixtures/btc_reel/trade_fail_reel.json";
import { reelPropsSchema } from "./props";
import { slideStoryPropsSchema } from "./slides/slideProps";
import { tutorialPropsSchema } from "./slides/tutorialProps";
import { kurzSlidePropsSchema } from "./slides/kurzProps";

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

const kurzSlideDefaultProps = kurzSlidePropsSchema.parse(kurzSlide2Fixture);
// Fonts (Fraunces/Inter/JetBrains Mono) are imported locally in slides/theme.ts
// via @fontsource — no runtime Google Fonts fetch.

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
      <Composition
        id="KurzSlide"
        component={KurzSlide}
        durationInFrames={kurzSlideDefaultProps.durationInFrames}
        fps={30}
        width={1080}
        height={1350}
        schema={kurzSlidePropsSchema}
        defaultProps={kurzSlideDefaultProps}
        calculateMetadata={({ props }) => ({
          // duration follows whatever slide props file is rendered
          // (--props=fixtures/carousel_top3/slideN.json), not the default
          // fixture — durationInFrames is the single source of truth.
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="CharacterCard"
        component={CharacterCard}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1350}
        schema={characterCardSchema}
        defaultProps={{
          variant: "lineup" as const,
          footer: "Original AI STACK characters — educational content · not financial advice",
          durationInFrames: 300,
        }}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="ExplainerScene"
        component={ExplainerScene}
        durationInFrames={430}
        fps={30}
        width={1080}
        height={1920}
        schema={explainerSceneSchema}
        defaultProps={{
          kick: "CHIP EXPLAINS",
          title: "AMD: the model vs the market.",
          bars: [
            {label: "MODEL VALUE", value: 241, color: "#34D399"},
            {label: "PRICE", value: 558, color: "#E0A23B"},
          ],
          beats: [
            {text: "A fundamental-value model puts AMD near $241.", at: 100},
            {text: "The market pays $558 — more than double the model.", at: 190},
            {text: "That gap IS the story. Growth is real — so is the price of it.", at: 280},
          ],
          footer: "Figures as of July 11, 2026 — educational · not financial advice",
          durationInFrames: 430,
        }}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="FaceoffOverlay"
        component={FaceoffOverlay}
        durationInFrames={1}
        fps={30}
        width={1080}
        height={1350}
        schema={faceoffOverlaySchema}
        defaultProps={{ img: "uploads/faceoff_hearts.png" }}
      />
      <Composition
        id="InfraCountdown"
        component={InfraCountdown}
        durationInFrames={infraCountdownFixture.durationInFrames}
        fps={30}
        width={1080}
        height={1920}
        schema={infraCountdownSchema}
        defaultProps={infraCountdownSchema.parse(infraCountdownFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="TradingQuiz"
        component={TradingQuiz}
        durationInFrames={tradingQuizFixture.durationInFrames}
        fps={30}
        width={1080}
        height={1920}
        schema={tradingQuizSchema}
        defaultProps={tradingQuizSchema.parse(tradingQuizFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="GroundingCheck"
        component={GroundingCheck}
        durationInFrames={60}
        fps={30}
        width={1080}
        height={1920}
        schema={groundingCheckSchema}
        defaultProps={{ scale: 1, x: 760, guides: true, label: "measured", poseFrame: 0 }}
      />
      <Composition
        id="TradingStyles"
        component={TradingStyles}
        durationInFrames={tradingStylesFixture.durationInFrames}
        fps={30}
        width={1080}
        height={1920}
        schema={tradingStylesSchema}
        defaultProps={tradingStylesSchema.parse(tradingStylesFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="QuizWithHost"
        component={QuizWithHost}
        durationInFrames={quizWithHostFixture.durationInFrames}
        fps={30}
        width={1080}
        height={1920}
        schema={quizWithHostSchema}
        defaultProps={quizWithHostSchema.parse(quizWithHostFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="ExplainerSceneV2"
        component={ExplainerSceneV2}
        durationInFrames={430}
        fps={30}
        width={1080}
        height={1920}
        schema={explainerSceneSchema}
        defaultProps={{
          character: "chip" as const,
          kick: "CHIP EXPLAINS",
          title: "AMD: the model vs the market.",
          bars: [
            {label: "MODEL VALUE", value: 241, color: "#34D399"},
            {label: "PRICE", value: 558, color: "#E0A23B"},
          ],
          beats: [
            {text: "A fundamental-value model puts AMD near $241.", at: 100},
            {text: "The market pays $558 — more than double the model.", at: 190},
            {text: "That gap IS the story. Growth is real — so is the price of it.", at: 280},
          ],
          footer: "Figures as of July 11, 2026 — educational · not financial advice",
          durationInFrames: 430,
        }}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="FamilyRigShowcase"
        component={FamilyRigShowcase}
        durationInFrames={930}
        fps={30}
        width={1080}
        height={1350}
        schema={familyRigShowcaseSchema}
        defaultProps={{
          character: "watt" as const,
          variant: "sheet" as const,
          footer: "Original AI STACK character — educational content · not financial advice",
          durationInFrames: 930,
        }}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="MemeReel"
        component={MemeReel}
        durationInFrames={510}
        fps={30}
        width={1080}
        height={1920}
        schema={memeReelSchema}
        defaultProps={memeReelSchema.parse(memeReelFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      {/* CTA end card — a Still: the owner merges this single frame into the
          reel in Instagram, so it must sit against PatternSheet seamlessly.
          Every colour/type token is imported from the same modules the sheet
          uses rather than re-typed. */}
      <Still
        id="PatternEndCard"
        component={PatternEndCard}
        width={1080}
        height={1920}
        schema={patternEndCardSchema}
        defaultProps={patternEndCardSchema.parse({
          headline: "WHICH CHART",
          headlineAccent: "SHOULD I HUNT?",
          sub: "Comment your asset — the top pick gets\nits own pattern breakdown next.",
          prompt: "// DROP IT BELOW",
          placeholder: "your ticker...",
          footer:
            "Real market data · Interactive Brokers · educational only, not financial advice · DYOR",
        })}
      />
      <Composition
        id="PatternSheet"
        component={PatternSheet}
        durationInFrames={PATTERN_SHEET_FRAMES}
        fps={30}
        width={1080}
        height={1920}
        schema={patternSheetSchema}
        defaultProps={patternSheetSchema.parse({
          chapters: patternGalleryFixture.chapters,
          footer:
            "Real SPY daily bars · Interactive Brokers · retrieved 2026-07-30 · hindsight examples · educational only, not financial advice · DYOR",
          durationInFrames: PATTERN_SHEET_FRAMES,
        })}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="PatternGallery"
        component={PatternGallery}
        durationInFrames={PATTERN_GALLERY_FRAMES}
        fps={30}
        width={1080}
        height={1920}
        schema={patternGallerySchema}
        defaultProps={patternGallerySchema.parse({
          chapters: patternGalleryFixture.chapters,
          footer:
            "Real SPY daily bars · Interactive Brokers · retrieved 2026-07-30 · hindsight examples · educational only, not financial advice · DYOR",
          durationInFrames: PATTERN_GALLERY_FRAMES,
        })}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="TradeFailCam"
        component={TradeFailCam}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
        schema={tradeFailCamSchema}
        defaultProps={tradeFailCamSchema.parse(tradeFailFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      <Composition
        id="TradeFailReel"
        component={TradeFailReel}
        durationInFrames={1200}
        fps={30}
        width={1080}
        height={1920}
        schema={tradeFailReelSchema}
        defaultProps={tradeFailReelSchema.parse(tradeFailFixture)}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
      {/* Rig contact sheet — not a deliverable, a check. It exists so the two
          failure modes that typecheck cleanly (limbs detaching at the joints,
          a pose that reads wrong) are inspectable as stills instead of being
          hunted for inside a 510-frame render. */}
      <Composition
        id="RigCheck"
        component={RigCheck}
        durationInFrames={510}
        fps={30}
        width={1080}
        height={1350}
        schema={rigCheckSchema}
        defaultProps={{ mode: "sheet" as const, rig: "toon" as const }}
      />
      <Composition
        id="ChipShowcase"
        component={ChipShowcase}
        durationInFrames={730}
        fps={30}
        width={1080}
        height={1350}
        schema={chipShowcaseSchema}
        defaultProps={{
          variant: "demo" as const,
          footer: "Original AI STACK character — educational content · not financial advice",
          durationInFrames: 730,
        }}
        calculateMetadata={({ props }) => ({
          durationInFrames: props.durationInFrames,
        })}
      />
    </>
  );
};
