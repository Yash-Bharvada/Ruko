import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { createRouter, rootRouteId } from "@tanstack/react-router";
import { routeTree } from "@/routeTree.gen";
import { getExplainStrings, EXPLAIN_STRINGS } from "@/lib/explainStrings";
import {
  SAMPLE_EXPLANATION_EN,
  SAMPLE_EXPLANATION_HI,
  SAMPLE_EXPLANATION_GU,
} from "@/lib/__fixtures__/explain.sample";

describe("DocExplain Routing", () => {
  it("matches /explain route successfully", () => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });
    const matches = router.matchRoutes("/explain");
    expect(matches.at(-1)?.routeId).not.toBe(rootRouteId);
    expect(matches.at(-1)?.pathname).toBe("/explain");
  });
});

describe("ExplainStrings i18n", () => {
  it("returns English strings for 'en' and unknown codes", () => {
    const en = getExplainStrings("en");
    expect(en.pageTitle).toBe("Explain a Document");
    expect(en.tabSummary).toBe("Summary");

    const unknown = getExplainStrings("fr");
    expect(unknown.pageTitle).toBe("Explain a Document");
  });

  it("returns Hindi strings for 'hi'", () => {
    const hi = getExplainStrings("hi");
    expect(hi.pageTitle).toBe("दस्तावेज़ को आसान भाषा में समझें");
    expect(hi.tabSummary).toBe("सारांश");
    expect(hi.tabDiagrams).toBe("डायग्राम");
  });

  it("returns Gujarati strings for 'gu'", () => {
    const gu = getExplainStrings("gu");
    expect(gu.pageTitle).toBe("દસ્તાવેજને સરળ ભાષામાં સમજો");
    expect(gu.tabSummary).toBe("સારાંશ");
  });

  it("falls back to English for hinglish and gujlish", () => {
    const hinglish = getExplainStrings("hinglish");
    expect(hinglish.pageTitle).toBe(EXPLAIN_STRINGS.en.pageTitle);

    const gujlish = getExplainStrings("gujlish");
    expect(gujlish.pageTitle).toBe(EXPLAIN_STRINGS.en.pageTitle);
  });
});

describe("Sample Document Fixtures", () => {
  it("validates English sample structure", () => {
    const sample = SAMPLE_EXPLANATION_EN;
    expect(sample.doc_type_guess).toBe("loan_agreement");
    expect(sample.summary).toBeTruthy();
    expect(sample.glossary.length).toBeGreaterThanOrEqual(1);
    expect(sample.key_points.length).toBeGreaterThanOrEqual(1);
    expect(sample.steps.length).toBeGreaterThanOrEqual(1);
    expect(sample.diagrams.flowchart?.nodes.length).toBeGreaterThanOrEqual(2);
    expect(sample.diagrams.money_flow?.nodes.length).toBeGreaterThanOrEqual(2);
    expect(sample.diagrams.timeline?.length).toBeGreaterThanOrEqual(1);
    expect(sample.storyboard.length).toBeGreaterThanOrEqual(2);
  });

  it("validates Hindi sample structure", () => {
    const sample = SAMPLE_EXPLANATION_HI;
    expect(sample.language).toBe("hi");
    expect(sample.summary).toBeTruthy();
    expect(sample.storyboard.length).toBeGreaterThanOrEqual(2);
    expect(sample.diagrams.flowchart?.nodes.length).toBeGreaterThanOrEqual(2);
  });

  it("validates Gujarati sample structure", () => {
    const sample = SAMPLE_EXPLANATION_GU;
    expect(sample.language).toBe("gu");
    expect(sample.summary).toBeTruthy();
    expect(sample.storyboard.length).toBeGreaterThanOrEqual(2);
    expect(sample.diagrams.flowchart?.nodes.length).toBeGreaterThanOrEqual(2);
  });
});
