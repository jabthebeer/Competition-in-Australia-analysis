import { NextStep, PageHeading, type PageProps } from "../App";

export function CompetitionPage({ go }: PageProps) {
  return (
    <>
      <PageHeading>Step 6: Competition screen</PageHeading>
      <p>The competition screen follows the Office of Impact Analysis's three steps.</p>
      <NextStep go={go} to="results">
        Next: results
      </NextStep>
    </>
  );
}
