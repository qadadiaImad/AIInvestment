import { Composition } from "remotion";
import { CharacterSmokeTest, characterSmokeTestSchema } from "./compositions/CharacterSmokeTest";

const SMOKE_TEST_CHARACTERS = ["chip", "watt", "qubit", "cap", "nova", "cloudy"] as const;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {SMOKE_TEST_CHARACTERS.map((key) => (
        <Composition
          key={key}
          id={`SmokeTest-${key[0].toUpperCase()}${key.slice(1)}`}
          component={CharacterSmokeTest}
          durationInFrames={240}
          fps={30}
          width={1080}
          height={1920}
          schema={characterSmokeTestSchema}
          defaultProps={{ character: key, debugSafeZone: false }}
        />
      ))}
    </>
  );
};
